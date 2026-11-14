import { randomUUID } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";
import { hasValidSession } from "@/app/lib/session";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  if (!(await hasValidSession())) {
    return NextResponse.json({ detail: "Sign in to run a workflow demo" }, { status: 401 });
  }
  const origin = request.headers.get("origin");
  if (origin) {
    try {
      if (new URL(origin).host.toLowerCase() !== request.headers.get("host")?.toLowerCase()) {
        return NextResponse.json({ detail: "Cross-origin request rejected" }, { status: 403 });
      }
    } catch {
      return NextResponse.json({ detail: "Cross-origin request rejected" }, { status: 403 });
    }
  }

  const webhookUrl = process.env.N8N_INVOICE_WEBHOOK_URL;
  const webhookSecret = process.env.N8N_INBOUND_WEBHOOK_SECRET;
  if (!webhookUrl || !webhookSecret) {
    return NextResponse.json({ detail: "Configure N8N_INVOICE_WEBHOOK_URL and N8N_INBOUND_WEBHOOK_SECRET on the web service" }, { status: 503 });
  }
  const apiBase = process.env.MANDATE_API_URL ?? "http://api:8000";
  const adminKey = process.env.MANDATE_ADMIN_API_KEY;
  if (!adminKey) return NextResponse.json({ detail: "Dashboard API credential is not configured on the web service" }, { status: 503 });
  try {
    const dashboardResponse = await fetch(new URL("/api/v1/dashboard", apiBase), {
      headers: { "X-Admin-API-Key": adminKey }, cache: "no-store",
    });
    const dashboard = await dashboardResponse.json().catch(() => ({}));
    if (!dashboardResponse.ok) return NextResponse.json({ detail: "Could not verify payment execution status" }, { status: 503 });
    if (dashboard.execution_enabled === true) {
      return NextResponse.json({ detail: "Dashboard demo is paused because XRPL execution is enabled. Turn it off before sending a no-funds-moved workflow test." }, { status: 409 });
    }
  } catch {
    return NextResponse.json({ detail: "Could not reach the Mandate API to verify payment execution status" }, { status: 503 });
  }
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ detail: "Invalid invoice request" }, { status: 400 });
  }
  if (!payload || typeof payload !== "object") {
    return NextResponse.json({ detail: "Invoice payload must be a JSON object" }, { status: 400 });
  }
  const invoice = payload as Record<string, unknown>;
  const invoiceId = `DASH-${new Date().toISOString().slice(0, 10).replaceAll("-", "")}-${randomUUID().slice(0, 8)}`;
  const amount = String(invoice.amount ?? "");
  if (typeof invoice.payee !== "string" || !invoice.payee.trim() || !/^\d+(\.\d{1,6})?$/.test(amount) || Number(amount) <= 0) {
    return NextResponse.json({ detail: "Choose an approved supplier and enter a positive amount (up to 6 decimal places)" }, { status: 422 });
  }
  const event = {
    invoice_id: invoiceId,
    payee: invoice.payee.trim(),
    amount,
    currency: invoice.currency === "XRP" ? "XRP" : "RLUSD",
    issuer: typeof invoice.issuer === "string" && invoice.issuer ? invoice.issuer : null,
    network: invoice.network === "devnet" ? "devnet" : "testnet",
    reason: "Dashboard workflow demonstration invoice",
  };
  try {
    const upstream = await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Invoice-Webhook-Secret": webhookSecret },
      body: JSON.stringify(event),
      cache: "no-store",
      signal: AbortSignal.timeout(70_000),
    });
    const result = await upstream.json().catch(() => ({}));
    if (!upstream.ok) {
      const hint = upstream.status === 404
        ? "n8n did not find the active invoice-approved webhook. Import the workflow, select its Header Auth credential, activate it, and retry."
        : result.message ?? result.detail ?? "n8n could not process the invoice";
      return NextResponse.json({ detail: hint, upstream_status: upstream.status, invoice_id: invoiceId }, { status: upstream.status });
    }
    return NextResponse.json({ invoice_id: invoiceId, workflow_status: "accepted", result }, { status: 200 });
  } catch {
    return NextResponse.json({ detail: "Could not reach n8n. Check that Docker Compose is running and n8n is available." }, { status: 502 });
  }
}
