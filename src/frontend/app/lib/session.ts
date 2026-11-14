import { createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";

const COOKIE_NAME = "mandate_session";
const SESSION_DURATION_SECONDS = 60 * 60 * 8;

export type SessionUser = { id: number; email: string; full_name: string; role: string; session_version: number };
type SessionClaims = SessionUser & { exp: number };

function sessionSecret() {
  const secret = process.env.SESSION_SECRET;
  if (!secret || secret.length < 32) throw new Error("SESSION_SECRET must contain at least 32 characters");
  return secret;
}

function signature(payload: string) {
  return createHmac("sha256", sessionSecret()).update(payload).digest("base64url");
}

export function createSessionToken(user: SessionUser) {
  const claims: SessionClaims = { ...user, exp: Math.floor(Date.now() / 1000) + SESSION_DURATION_SECONDS };
  const payload = Buffer.from(JSON.stringify(claims)).toString("base64url");
  return `${payload}.${signature(payload)}`;
}

export function isValidSessionToken(token: string | undefined) {
  if (!token) return false;
  const [payload, suppliedSignature] = token.split(".");
  if (!payload || !suppliedSignature) return false;
  try {
    const expected = Buffer.from(signature(payload));
    const supplied = Buffer.from(suppliedSignature);
    if (expected.length !== supplied.length || !timingSafeEqual(expected, supplied)) return false;
    const claims = JSON.parse(Buffer.from(payload, "base64url").toString("utf8")) as SessionClaims;
    return Number.isInteger(claims.id) && claims.exp > Math.floor(Date.now() / 1000);
  } catch {
    return false;
  }
}

export async function hasValidSession() {
  const store = await cookies();
  const token = store.get(COOKIE_NAME)?.value;
  if (!isValidSessionToken(token)) return false;
  try {
    const [payload] = token!.split(".");
    const claims = JSON.parse(Buffer.from(payload, "base64url").toString("utf8")) as SessionClaims;
    const apiBase = process.env.MANDATE_API_URL ?? "http://localhost:8000";
    const adminKey = process.env.MANDATE_ADMIN_API_KEY;
    if (!adminKey) return false;
    const response = await fetch(new URL("/api/v1/auth/validate-session", apiBase), {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Admin-API-Key": adminKey },
      body: JSON.stringify({ user_id: claims.id, session_version: claims.session_version }),
      cache: "no-store",
    });
    if (!response.ok) return false;
    const result = await response.json() as { valid?: boolean };
    return result.valid === true;
  } catch {
    return false;
  }
}

export const sessionCookieName = COOKIE_NAME;
export const sessionDurationSeconds = SESSION_DURATION_SECONDS;
