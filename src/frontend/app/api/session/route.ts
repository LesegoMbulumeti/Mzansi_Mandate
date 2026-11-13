import { timingSafeEqual } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";
import {
  createSessionToken,
  sessionCookieName,
  sessionDurationSeconds,
} from "@/app/lib/session";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const configuredPassword = process.env.ADMIN_LOGIN_PASSWORD;
  if (!configuredPassword) {
    return NextResponse.json({ detail: "ADMIN_LOGIN_PASSWORD is not configured" }, { status: 503 });
  }

  let password = "";
  try {
    password = String((await request.json()).password ?? "");
  } catch {
    return NextResponse.json({ detail: "Invalid login request" }, { status: 400 });
  }
  const supplied = Buffer.from(password);
  const expected = Buffer.from(configuredPassword);
  if (supplied.length !== expected.length || !timingSafeEqual(supplied, expected)) {
    return NextResponse.json({ detail: "Email or password is incorrect" }, { status: 401 });
  }

  const response = NextResponse.json({ authenticated: true });
  response.cookies.set(sessionCookieName, createSessionToken(), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: sessionDurationSeconds,
  });
  return response;
}

export async function DELETE() {
  const response = NextResponse.json({ authenticated: false });
  response.cookies.set(sessionCookieName, "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: 0,
  });
  return response;
}
