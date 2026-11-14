import { NextResponse } from "next/server";
import { sessionCookieName } from "@/app/lib/session";

export const runtime = "nodejs";

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
