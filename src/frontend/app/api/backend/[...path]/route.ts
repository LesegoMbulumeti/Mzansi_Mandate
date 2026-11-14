import { NextRequest, NextResponse } from "next/server";
import { hasValidSession } from "@/app/lib/session";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RouteContext = { params: Promise<{ path: string[] }> };

async function proxy(request: NextRequest, context: RouteContext) {
  if (!(await hasValidSession())) {
    return NextResponse.json({ detail: "Sign in to continue" }, { status: 401 });
  }

  if (!["GET", "POST", "PUT", "PATCH", "DELETE"].includes(request.method)) {
    return NextResponse.json({ detail: "Method not allowed" }, { status: 405 });
  }
  if (request.method !== "GET" && request.method !== "HEAD") {
    const origin = request.headers.get("origin");
    if (origin) {
      const forwardedHost = request.headers.get("x-forwarded-host")?.split(",")[0].trim();
      const requestHost = forwardedHost || request.headers.get("host");
      const forwardedProto = request.headers.get("x-forwarded-proto")?.split(",")[0].trim();
      const requestProtocol = forwardedProto
        ? `${forwardedProto.replace(/:$/, "")}:`
        : request.nextUrl.protocol;

      let originUrl: URL | undefined;
      try {
        originUrl = new URL(origin);
      } catch {
        return NextResponse.json({ detail: "Cross-origin request rejected" }, { status: 403 });
      }

      if (
        !requestHost ||
        originUrl.host.toLowerCase() !== requestHost.toLowerCase() ||
        originUrl.protocol !== requestProtocol
      ) {
        return NextResponse.json({ detail: "Cross-origin request rejected" }, { status: 403 });
      }
    }
  }

  const { path } = await context.params;
  if (!path.length || path.some((part) => part === ".." || part.includes("/"))) {
    return NextResponse.json({ detail: "Invalid API path" }, { status: 400 });
  }

  const apiBase = process.env.MANDATE_API_URL ?? "http://localhost:8000";
  const adminKey = process.env.MANDATE_ADMIN_API_KEY;
  if (!adminKey) {
    return NextResponse.json({ detail: "MANDATE_ADMIN_API_KEY is not configured" }, { status: 503 });
  }

  const target = new URL(`/api/v1/${path.map(encodeURIComponent).join("/")}`, apiBase);
  target.search = request.nextUrl.search;
  const headers = new Headers({
    "X-Admin-API-Key": adminKey,
    Accept: request.headers.get("accept") ?? "application/json",
  });
  const contentType = request.headers.get("content-type");
  const idempotencyKey = request.headers.get("idempotency-key");
  if (contentType) headers.set("Content-Type", contentType);
  if (idempotencyKey) headers.set("Idempotency-Key", idempotencyKey);

  let body: ArrayBuffer | undefined;
  if (request.method !== "GET" && request.method !== "HEAD") body = await request.arrayBuffer();
  try {
    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
    });
    return new NextResponse(await upstream.arrayBuffer(), {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
    });
  } catch {
    return NextResponse.json({ detail: "Mandate API is unavailable" }, { status: 502 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
