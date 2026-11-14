import base64
import hashlib
import hmac
import logging
import re
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.config import settings
from app.models.orm import PasswordResetRow, UserRow
from app.services.errors import ConflictError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
SCRYPT_N = 2**14


def _password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=8, p=1, dklen=64)
    return "scrypt${}${}${}${}${}".format(
        SCRYPT_N, 8, 1,
        base64.urlsafe_b64encode(salt).decode(),
        base64.urlsafe_b64encode(derived).decode(),
    )


def _password_matches(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt_text, digest_text = encoded.split("$")
        if scheme != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
        actual = hashlib.scrypt(password.encode(), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _normal_email(email: str) -> str:
    value = email.strip().lower()
    if not EMAIL_PATTERN.fullmatch(value):
        raise ValidationError("Enter a valid email address")
    return value


def _user_payload(user: UserRow) -> dict[str, int | str]:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "session_version": user.session_version,
    }


class AuthService:
    RESET_LIFETIME = timedelta(minutes=30)

    def __init__(self, session: Session):
        self.session = session

    def registration_status(self) -> dict[str, bool]:
        count = self.session.scalar(select(func.count()).select_from(UserRow)) or 0
        return {"registration_open": count == 0}

    def register(self, full_name: str, email: str, password: str) -> dict[str, int | str]:
        email = _normal_email(email)
        name = full_name.strip()
        if len(name) < 2:
            raise ValidationError("Enter your name (at least 2 characters)")
        if len(password) < 12:
            raise ValidationError("Use a password with at least 12 characters")
        if self.session.scalar(select(UserRow.id).limit(1)) is not None:
            raise ConflictError("The owner account is already set up. Sign in or reset its password.")
        user = UserRow(email=email, full_name=name, password_hash=_password_hash(password), role="owner")
        try:
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
            return _user_payload(user)
        except Exception:
            self.session.rollback()
            if self.session.scalar(select(UserRow.id).limit(1)) is not None:
                raise ConflictError("The owner account is already set up. Sign in or reset its password.")
            raise

    def login(self, email: str, password: str) -> dict[str, int | str]:
        email = _normal_email(email)
        user = self.session.scalar(select(UserRow).where(UserRow.email == email))
        # Use a fixed dummy hash for unknown accounts to reduce timing differences.
        dummy = "scrypt$16384$8$1$MDEyMzQ1Njc4OWFiY2RlZg==$" + base64.urlsafe_b64encode(b"x" * 64).decode()
        if user is None:
            _password_matches(password, dummy)
            raise NotFoundError("Email or password is incorrect")
        if not _password_matches(password, user.password_hash):
            raise NotFoundError("Email or password is incorrect")
        return _user_payload(user)

    def request_password_reset(self, email: str) -> str | None:
        email = _normal_email(email)
        user = self.session.scalar(select(UserRow).where(UserRow.email == email))
        if user is None:
            return None
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        try:
            self.session.query(PasswordResetRow).filter(PasswordResetRow.user_id == user.id).delete()
            self.session.add(PasswordResetRow(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=now + self.RESET_LIFETIME,
            ))
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        reset_url = f"{settings.app_public_url.rstrip('/')}/reset-password?token={token}"
        self._deliver_reset_email(user.email, user.full_name, reset_url)
        return reset_url if settings.app_env == "development" else None

    def reset_password(self, token: str, password: str) -> None:
        if len(password) < 12:
            raise ValidationError("Use a password with at least 12 characters")
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        reset = self.session.scalar(select(PasswordResetRow).where(PasswordResetRow.token_hash == token_hash))
        if reset is None:
            raise ValidationError("This reset link is invalid or has expired. Request a new one.")
        expires = reset.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires <= datetime.now(timezone.utc):
            self.session.delete(reset)
            self.session.commit()
            raise ValidationError("This reset link is invalid or has expired. Request a new one.")
        user = self.session.get(UserRow, reset.user_id)
        if user is None:
            self.session.delete(reset)
            self.session.commit()
            raise ValidationError("This reset link is invalid or has expired. Request a new one.")
        try:
            user.password_hash = _password_hash(password)
            user.session_version += 1
            self.session.query(PasswordResetRow).filter(PasswordResetRow.user_id == user.id).delete()
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def validate_session(self, user_id: int, session_version: int) -> bool:
        user = self.session.get(UserRow, user_id)
        return bool(user and user.session_version == session_version)

    @staticmethod
    def _deliver_reset_email(email: str, name: str, reset_url: str) -> None:
        if not settings.smtp_host or not settings.smtp_from_email:
            if settings.app_env == "development":
                logger.warning("Development password reset link for %s: %s", email, reset_url)
            else:
                logger.error("Password reset email is not configured; set SMTP_HOST and SMTP_FROM_EMAIL")
            return
        message = EmailMessage()
        message["Subject"] = "Reset your Mandate password"
        message["From"] = settings.smtp_from_email
        message["To"] = email
        message.set_content(
            f"Hi {name},\n\nUse this one-time link to reset your Mandate password. "
            f"It expires in 30 minutes.\n\n{reset_url}\n\nIf you did not request this, ignore this email."
        )
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
                smtp.starttls()
                if settings.smtp_username:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
        except Exception:
            logger.exception("Unable to deliver password reset message")
