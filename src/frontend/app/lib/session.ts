import { createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";

const COOKIE_NAME = "mandate_session";
const SESSION_DURATION_SECONDS = 60 * 60 * 8;

function sessionSecret() {
  const secret = process.env.SESSION_SECRET;
  if (!secret || secret.length < 32) throw new Error("SESSION_SECRET must contain at least 32 characters");
  return secret;
}

function signature(expires: string) {
  return createHmac("sha256", sessionSecret()).update(expires).digest("hex");
}

export function createSessionToken() {
  const expires = String(Math.floor(Date.now() / 1000) + SESSION_DURATION_SECONDS);
  return `${expires}.${signature(expires)}`;
}

export function isValidSessionToken(token: string | undefined) {
  if (!token) return false;
  const [expires, suppliedSignature] = token.split(".");
  if (!expires || !suppliedSignature || Number(expires) <= Math.floor(Date.now() / 1000)) return false;
  try {
    const expected = Buffer.from(signature(expires), "hex");
    const supplied = Buffer.from(suppliedSignature, "hex");
    return expected.length === supplied.length && timingSafeEqual(expected, supplied);
  } catch {
    return false;
  }
}

export async function hasValidSession() {
  const store = await cookies();
  return isValidSessionToken(store.get(COOKIE_NAME)?.value);
}

export const sessionCookieName = COOKIE_NAME;
export const sessionDurationSeconds = SESSION_DURATION_SECONDS;
