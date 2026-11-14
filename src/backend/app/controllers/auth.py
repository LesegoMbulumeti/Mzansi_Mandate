from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers.security import require_operator
from app.db.session import get_session
from app.schemas.auth import AuthUserOut, ForgotPasswordIn, LoginIn, RegisterIn, ResetPasswordIn, SessionValidationIn
from app.services.auth_service import AuthService
from app.services.errors import NotFoundError

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.get("/registration-status")
def registration_status(session: Session = Depends(get_session)) -> dict[str, bool]:
    return AuthService(session).registration_status()


@router.post("/register", response_model=AuthUserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, session: Session = Depends(get_session)) -> dict:
    return AuthService(session).register(body.full_name, body.email, body.password)


@router.post("/login", response_model=AuthUserOut)
def login(body: LoginIn, session: Session = Depends(get_session)) -> dict:
    try:
        return AuthService(session).login(body.email, body.password)
    except NotFoundError as exc:
        raise HTTPException(status_code=401, detail="Email or password is incorrect") from exc


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(body: ForgotPasswordIn, session: Session = Depends(get_session)) -> dict[str, str]:
    development_reset_url = AuthService(session).request_password_reset(body.email)
    response = {"message": "If an account exists for that email, password reset instructions will be sent."}
    if development_reset_url:
        response["development_reset_url"] = development_reset_url
    return response


@router.post("/reset-password")
def reset_password(body: ResetPasswordIn, session: Session = Depends(get_session)) -> dict[str, bool]:
    AuthService(session).reset_password(body.token, body.password)
    return {"password_reset": True}


@router.post("/validate-session", dependencies=[Depends(require_operator)])
def validate_session(body: SessionValidationIn, session: Session = Depends(get_session)) -> dict[str, bool]:
    return {"valid": AuthService(session).validate_session(body.user_id, body.session_version)}
