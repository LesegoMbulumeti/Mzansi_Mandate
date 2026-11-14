import { NextRequest, NextResponse } from "next/server";
import { createSessionToken, sessionCookieName, sessionDurationSeconds, type SessionUser } from "@/app/lib/session";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const actions = new Set(["register", "login", "forgot-password", "reset-password", "registration-status"]);

export async function GET(_request: NextRequest, { params }: { params: Promise<{ action: string }> }) {
  const { action } = await params;
  if (action !== "registration-status") return NextResponse.json({ detail: "Unknown authentication action" }, { status: 404 });
  const apiBase = process.env.MANDATE_API_URL ?? "http://localhost:8000";
  try {
    const upstream = await fetch(new URL("/api/v1/auth/registration-status", apiBase), { cache: "no-store" });
    return NextResponse.json(await upstream.json().catch(() => ({})), { status: upstream.status });
  } catch {
    return NextResponse.json({ detail: "Authentication service is unavailable" }, { status: 502 });
  }
}

export async function POST(request: NextRequest, { params }: { params: Promise<{ action: string }> }) {
  const { action } = await params;
  if (!actions.has(action)) return NextResponse.json({ detail: "Unknown authentication action" }, { status: 404 });
  let body: string;
  try {
    body = await request.text();
    JSON.parse(body);
  } catch {
    return NextResponse.json({ detail: "Invalid request" }, { status: 400 });
  }

  const apiBase = process.env.MANDATE_API_URL ?? "http://localhost:8000";
  try {
    const upstream = await fetch(new URL(`/api/v1/auth/${action}`, apiBase), {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body,
      cache: "no-store",
    });
    const payload = await upstream.json().catch(() => ({}));
    const responsePayload = { ...payload };
    delete responsePayload.session_version;
    delete responsePayload.password_hash;
    const response = NextResponse.json(responsePayload, { status: upstream.status });
    if (upstream.ok && (action === "login" || action === "register")) {
      response.cookies.set(sessionCookieName, createSessionToken(payload as SessionUser), {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "strict",
        path: "/",
        maxAge: sessionDurationSeconds,
      });
    }
    return response;
  } catch {
    return NextResponse.json({ detail: "Authentication service is unavailable" }, { status: 502 });
  }
}
