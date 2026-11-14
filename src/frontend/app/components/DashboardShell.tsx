"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity, ArrowDownLeft, ArrowRight, ArrowUpRight, BadgeCheck, Bell,
  Blocks, Check, ChevronDown, CircleAlert, Clock3, FileCheck2, Gauge,
  LayoutDashboard, LogOut, MoreHorizontal, Plus, RefreshCw,
  Pencil, Search, ShieldAlert, ShieldCheck, SlidersHorizontal, Users, WalletCards, X,
} from "lucide-react";
import { apiRequest, formatAmount, formatDate, shortAddress } from "@/app/lib/api";
import type { AuditEvent, DashboardSummary, Mandate, Page, Payee, PaymentIntent } from "@/app/lib/types";
import { DashboardCharts } from "@/app/components/DashboardCharts";

type MandateForm = {
  per_payment_cap: string;
  daily_cap: string;
  max_slippage_pct: string;
  large_payment_threshold: string;
  currency: string;
  issuer: string;
  expires_at: string;
};

function localDateValue(value?: string) {
  const date = value ? new Date(value) : new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
  return new Date(date.getTime() - date.getTimezoneOffset() * 60_000).toISOString().slice(0, 16);
}

function defaultMandateForm(mandate?: Mandate | null): MandateForm {
  return {
    per_payment_cap: mandate?.per_payment_cap ?? "5000",
    daily_cap: mandate?.daily_cap ?? "12000",
    max_slippage_pct: mandate?.max_slippage_pct ?? "1.0",
    large_payment_threshold: mandate?.large_payment_threshold ?? "",
    currency: mandate?.currency ?? "RLUSD",
    issuer: mandate?.issuer ?? "",
    expires_at: localDateValue(mandate?.expires_at),
  };
}

function StateBadge({ intent }: { intent: PaymentIntent }) {
  let type = "neutral";
  let label = intent.status.replaceAll("_", " ");
  if (intent.status === "settled") { type = "success"; label = "Settled"; }
  else if (intent.status === "blocked") { type = "danger"; label = "Blocked"; }
  else if (intent.status === "needs_approval") { type = "warning"; label = "Needs approval"; }
  else if (intent.status === "submission_unknown") { type = "danger"; label = "Reconcile"; }
  else if (intent.status === "failed" || intent.status === "cancelled") type = "danger";
  else if (intent.status === "authorized") { type = "info"; label = "Authorized · not sent"; }
  else if (intent.status === "processing" || intent.status === "submitted") type = "info";
  return <span className={`state-badge ${type}`}><i />{label}</span>;
}

function initials(name: string) {
  return name.split(/\s+/).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("");
}

export function DashboardShell() {
  const pathname = usePathname();
  const section = pathname === "/dashboard" ? "overview" : pathname.split("/").filter(Boolean).at(-1) ?? "overview";
  const sectionTitles: Record<string, { title: string; description: string }> = {
    overview: { title: "Payment overview", description: "Here’s your payment workflow at a glance." },
    payments: { title: "Payment intents", description: "Review autonomous payment decisions and settlement results." },
    suppliers: { title: "Approved suppliers", description: "Manage the XRPL destinations your mandate permits." },
    policy: { title: "Policy & limits", description: "Set and review the finance rules enforced before signing." },
    audit: { title: "Audit activity", description: "Review the append-only history of policy and payment events." },
  };
  const page = sectionTitles[section] ?? sectionTitles.overview;
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [payees, setPayees] = useState<Payee[]>([]);
  const [intentPage, setIntentPage] = useState<Page<PaymentIntent> | null>(null);
  const [auditPage, setAuditPage] = useState<Page<AuditEvent> | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [mandateOpen, setMandateOpen] = useState(false);
  const [payeeOpen, setPayeeOpen] = useState(false);
  const [editingPayee, setEditingPayee] = useState<Payee | null>(null);
  const [selectedIntent, setSelectedIntent] = useState<PaymentIntent | null>(null);
  const [mandateForm, setMandateForm] = useState<MandateForm>(defaultMandateForm());
  const [payeeName, setPayeeName] = useState("");
  const [payeeAddress, setPayeeAddress] = useState("");
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState("");
  const [workflowBusy, setWorkflowBusy] = useState(false);
  const [workflowAmount, setWorkflowAmount] = useState("0.01");
  const [workflowPayeeId, setWorkflowPayeeId] = useState("");
  const [workflowMessage, setWorkflowMessage] = useState("");
  const [workflowError, setWorkflowError] = useState("");

  const load = useCallback(async (quiet = false) => {
    if (quiet) setRefreshing(true); else setLoading(true);
    setError("");
    try {
      const [nextSummary, nextPayees, nextIntents, nextAudit] = await Promise.all([
        apiRequest<DashboardSummary>("dashboard"),
        apiRequest<Payee[]>("payees"),
        apiRequest<Page<PaymentIntent>>("intents?limit=100&offset=0"),
        apiRequest<Page<AuditEvent>>("audit-events?limit=25&offset=0"),
      ]);
      setSummary(nextSummary);
      setPayees(nextPayees);
      setIntentPage(nextIntents);
      setAuditPage(nextAudit);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load dashboard data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const filteredIntents = useMemo(() => {
    const items = intentPage?.items ?? [];
    if (!filter.trim()) return items;
    const needle = filter.toLowerCase();
    return items.filter((item) => [item.payee, item.source, item.source_reference ?? "", item.status, item.currency]
      .some((value) => value.toLowerCase().includes(needle)));
  }, [filter, intentPage]);

  const pendingApprovals = useMemo(
    () => (intentPage?.items ?? []).filter((intent) => intent.status === "needs_approval"),
    [intentPage],
  );

  async function saveMandate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      const body = {
        per_payment_cap: mandateForm.per_payment_cap,
        daily_cap: mandateForm.daily_cap,
        max_slippage_pct: mandateForm.max_slippage_pct,
        large_payment_threshold: mandateForm.large_payment_threshold || null,
        currency: mandateForm.currency,
        issuer: mandateForm.issuer || null,
        expires_at: new Date(mandateForm.expires_at).toISOString(),
      };
      await apiRequest<Mandate>("mandate", { method: "PUT", body: JSON.stringify(body) });
      setMandateOpen(false);
      setNotice("Mandate saved and suspended. Review it, then activate when ready.");
      await load(true);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to save mandate");
    } finally { setBusy(false); }
  }

  async function toggleMandate(active: boolean) {
    if (!active && !window.confirm("Pause new payment authorizations? This app-level action does not revoke the XRPL signing key.")) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await apiRequest<Mandate>(`mandate/${active ? "activate" : "suspend"}`, { method: "POST" });
      setNotice(active ? "Mandate activated." : "New authorizations are paused at the API policy layer.");
      await load(true);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to update mandate"); }
    finally { setBusy(false); }
  }

  async function addPayee(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const isEditing = Boolean(editingPayee);
      await apiRequest<Payee>(isEditing ? `payees/${editingPayee?.id}` : "payees", {
        method: isEditing ? "PUT" : "POST",
        body: JSON.stringify({ name: payeeName.trim(), xrpl_address: payeeAddress.trim() }),
      });
      setPayeeOpen(false); setEditingPayee(null); setPayeeName(""); setPayeeAddress("");
      setNotice(isEditing ? "Supplier details updated." : "Supplier added to the approved payee list.");
      await load(true);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to add supplier"); }
    finally { setBusy(false); }
  }

  function openPayeeEditor(payee?: Payee) {
    setError("");
    setEditingPayee(payee ?? null);
    setPayeeName(payee?.name ?? "");
    setPayeeAddress(payee?.xrpl_address ?? "");
    setPayeeOpen(true);
  }

  async function deactivatePayee(payee: Payee) {
    if (!window.confirm(`Remove ${payee.name} from future payment approvals?`)) return;
    setBusy(true); setError("");
    try { await apiRequest<Payee>(`payees/${payee.id}`, { method: "DELETE" }); setNotice(`${payee.name} is no longer approved.`); await load(true); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to update supplier"); }
    finally { setBusy(false); }
  }

  async function decide(intent: PaymentIntent, action: "approve" | "reject") {
    setBusy(true); setError(""); setNotice("");
    try {
      const updated = await apiRequest<PaymentIntent>(`intents/${intent.id}/${action}`, {
        method: "POST", body: JSON.stringify({ comment: action === "approve" ? "Approved from finance dashboard" : "Rejected from finance dashboard" }),
      });
      setNotice(action === "approve" ? `Intent #${updated.id} approved${updated.status === "authorized" ? "; XRPL execution is disabled" : ""}.` : `Intent #${updated.id} rejected.`);
      await load(true);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to update approval"); }
    finally { setBusy(false); }
  }

  async function logout() {
    await fetch("/api/session", { method: "DELETE" });
    window.location.assign("/login");
  }

  async function sendDemoInvoice() {
    const payee = selectedWorkflowPayee;
    if (!payee) { setWorkflowError("Add an approved supplier before sending a workflow demo."); return; }
    setWorkflowBusy(true); setWorkflowError(""); setWorkflowMessage("");
    try {
      const response = await fetch("/api/workflow/invoice-test", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          payee: payee.xrpl_address,
          amount: workflowAmount,
          currency: mandate?.currency ?? "RLUSD",
          issuer: mandate?.issuer ?? null,
          network: summary?.network ?? "testnet",
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "The invoice workflow could not be reached");
      const outcome = result.result ?? {};
      setWorkflowMessage(`${result.invoice_id}: ${outcome.status ?? outcome.verdict ?? "workflow accepted"}${outcome.detail ? ` — ${outcome.detail}` : ""}`);
      await load(true);
    } catch (cause) {
      setWorkflowError(cause instanceof Error ? cause.message : "The invoice workflow could not be reached");
    } finally { setWorkflowBusy(false); }
  }

  const mandate = summary?.mandate;
  const spendPercent = mandate ? Math.min(100, (Number(summary?.daily_spend ?? 0) / Number(mandate.daily_cap || 1)) * 100) : 0;
  const activePayees = payees.filter((payee) => payee.active);
  const selectedWorkflowPayee = activePayees.find((payee) => String(payee.id) === workflowPayeeId) ?? activePayees[0];

  return <div className="dashboard-layout">
    <aside className="dashboard-sidebar">
      <Link href="/" className="brand-lockup dashboard-brand"><span className="brand-mark"><span /></span><span>mandate<span className="brand-period">.</span></span></Link>
      <div className="sidebar-workspace"><span className="workspace-avatar">MM</span><span><b>Mzansi Mandate</b><small>Finance workspace</small></span><ChevronDown size={14} /></div>
      <div className="sidebar-label">WORKSPACE</div>
      <nav className="dashboard-nav" aria-label="Dashboard navigation">
        <Link className={section === "overview" ? "active" : ""} href="/dashboard"><LayoutDashboard size={17} /> Overview</Link>
        <Link className={section === "payments" ? "active" : ""} href="/dashboard/payments"><ArrowUpRight size={17} /> Payment intents{(summary?.pending_approval ?? 0) > 0 && <span className="nav-count">{summary?.pending_approval}</span>}</Link>
        <Link className={section === "suppliers" ? "active" : ""} href="/dashboard/suppliers"><Users size={17} /> Approved suppliers</Link>
        <Link className={section === "policy" ? "active" : ""} href="/dashboard/policy"><SlidersHorizontal size={17} /> Policy &amp; limits</Link>
        <Link className={section === "audit" ? "active" : ""} href="/dashboard/audit"><Activity size={17} /> Audit activity</Link>
      </nav>
      <div className="sidebar-bottom">
        <div className="network-card"><span className="network-icon"><Blocks size={17} /></span><span><b>XRPL {summary?.network ?? "Testnet"}</b><small>{summary?.execution_enabled ? "Execution enabled" : "Signing disabled"}</small></span><i className={summary?.execution_enabled ? "" : "network-off"} /></div>
        <button className="sidebar-logout" onClick={logout}><LogOut size={16} /> Sign out</button>
        <div className="sidebar-user"><span className="user-avatar">FO</span><span><b>Finance operator</b><small>Workspace admin</small></span><MoreHorizontal size={17} /></div>
      </div>
    </aside>

    <main className="dashboard-main" id="overview">
      <header className="dashboard-topbar">
        <div className="mobile-brand"><span className="brand-mark"><span /></span> mandate<span className="brand-period">.</span></div>
        <div className="breadcrumb"><span>Workspace</span><span>/</span><b>{page.title}</b></div>
        <div className="topbar-actions"><label className="top-search"><Search size={15} /><input aria-label="Search" placeholder="Search activity" value={filter} onChange={(event) => setFilter(event.target.value)} /></label><span className="topbar-divider" /><button className="icon-button notification-button" aria-label="Notifications"><Bell size={17} />{(summary?.pending_approval ?? 0) > 0 && <i />}</button><span className="topbar-avatar">FO</span></div>
      </header>

      <div className="dashboard-content">
        <section className="page-heading"><div><div className="eyebrow dark-eyebrow">FINANCE OPERATIONS · XRPL {summary?.network ?? "TESTNET"}</div><h1>{page.title}<span className="heading-period">.</span></h1><p>{page.description}</p></div><div className="heading-actions"><button className="button button-outline" onClick={() => void load(true)} disabled={refreshing}><RefreshCw size={15} className={refreshing ? "spin" : ""} /> Refresh</button>{(section === "overview" || section === "policy") && <button className="button button-primary" onClick={() => { setMandateForm(defaultMandateForm(mandate)); setMandateOpen(true); }}><Plus size={16} /> {mandate ? "Edit mandate" : "Set up mandate"}</button>}{section === "suppliers" && <button className="button button-primary" onClick={() => openPayeeEditor()}><Plus size={16} /> Add supplier</button>}</div></section>

        {error && <div className="alert alert-error" role="alert"><CircleAlert size={17} /><span>{error}</span><button onClick={() => setError("")} aria-label="Dismiss"><X size={15} /></button></div>}
        {notice && <div className="alert alert-success" role="status"><BadgeCheck size={17} /><span>{notice}</span><button onClick={() => setNotice("")} aria-label="Dismiss"><X size={15} /></button></div>}

        {section === "overview" && <section className="panel workflow-test-panel" aria-labelledby="workflow-test-title">
          <div className="workflow-test-copy"><span className="eyebrow dark-eyebrow">WORKFLOW DEMO</span><h2 id="workflow-test-title">Try the invoice workflow</h2><p>Send a small demo invoice through the active n8n workflow. Choose an approved supplier and see the policy result here.</p></div>
          <div className="workflow-test-action"><label htmlFor="workflow-payee">Approved supplier</label><div className="workflow-test-controls"><select id="workflow-payee" value={selectedWorkflowPayee ? String(selectedWorkflowPayee.id) : ""} onChange={(event) => setWorkflowPayeeId(event.target.value)} disabled={!activePayees.length}>{activePayees.map((payee) => <option value={payee.id} key={payee.id}>{payee.name} · {shortAddress(payee.xrpl_address)}</option>)}</select><input aria-label={`Demo amount in ${mandate?.currency ?? "RLUSD"}`} type="number" min="0.000001" step="0.01" value={workflowAmount} onChange={(event) => setWorkflowAmount(event.target.value)} /><button className="button button-primary" disabled={workflowBusy || !activePayees.length || summary?.execution_enabled} onClick={() => void sendDemoInvoice()}>{workflowBusy ? "Sending…" : "Send demo invoice"}<ArrowRight size={15} /></button></div><small>{summary?.execution_enabled ? "Turn off XRPL execution before testing; this demo sends no funds." : activePayees.length ? `Uses ${selectedWorkflowPayee?.name}; XRPL execution remains disabled.` : "Add an approved supplier to enable the demo."}</small></div>
          {(workflowError || workflowMessage) && <div className={`workflow-feedback ${workflowError ? "is-error" : "is-success"}`} role={workflowError ? "alert" : "status"}>{workflowError || workflowMessage}</div>}
        </section>}

        {loading ? <div className="loading-grid"><div className="panel skeleton" /><div className="panel skeleton" /><div className="panel skeleton" /><div className="panel skeleton" /></div> : summary && <>
          {!mandate && <div className="setup-banner"><span className="setup-banner-icon"><SlidersHorizontal size={19} /></span><div><b>Set up your first payment mandate</b><p>Define the spending boundary and issuer before you activate payments.</p></div><button className="button button-primary" onClick={() => { setMandateForm(defaultMandateForm()); setMandateOpen(true); }}>Configure mandate <ArrowRight size={15} /></button></div>}
          {!summary.execution_enabled && <div className="execution-banner"><CircleAlert size={16} /><span><b>XRPL signing is disabled.</b> Policy decisions are recorded, but no funds move until testnet execution is explicitly enabled in the backend environment.</span></div>}
          {mandate && !mandate.active && <div className="setup-banner paused-banner"><span className="setup-banner-icon"><ShieldAlert size={19} /></span><div><b>Policy execution is paused</b><p>Changes to a mandate suspend it until an operator activates it again.</p></div><button className="button button-primary" disabled={busy} onClick={() => void toggleMandate(true)}>Activate mandate <Check size={15} /></button></div>}

          {section === "overview" && <>
          <section className="metric-grid" aria-label="Payment summary">
            <article className="metric-card"><div className="metric-top"><span className="metric-label">DAILY BUDGET USED</span><span className="metric-icon blue-icon"><Gauge size={17} /></span></div><div className="metric-value">{formatAmount(summary.daily_spend, summary.currency)}</div><div className="metric-foot"><span>{mandate ? `${formatAmount(mandate.daily_cap, summary.currency)} daily cap` : "No active budget set"}</span><span className="metric-trend">{mandate ? `${spendPercent.toFixed(0)}%` : "—"}</span></div><div className="budget-track"><i style={{ width: `${spendPercent}%` }} /></div></article>
            <article className="metric-card"><div className="metric-top"><span className="metric-label">PAYMENT INTENTS</span><span className="metric-icon violet-icon"><WalletCards size={17} /></span></div><div className="metric-value">{summary.intents_today}</div><div className="metric-foot"><span>Received today</span><span className="metric-soft">{summary.allowed_today} policy passed</span></div></article>
            <article className="metric-card"><div className="metric-top"><span className="metric-label">BLOCKED BY POLICY</span><span className="metric-icon orange-icon"><ShieldAlert size={17} /></span></div><div className="metric-value">{summary.blocked_today}</div><div className="metric-foot"><span>Attempts stopped safely</span><span className="metric-soft">Today</span></div></article>
            <article className="metric-card"><div className="metric-top"><span className="metric-label">APPROVED SUPPLIERS</span><span className="metric-icon green-icon"><Users size={17} /></span></div><div className="metric-value">{summary.approved_payees}</div><div className="metric-foot"><span>{summary.pending_approval} need a decision</span><a href="#suppliers">Manage <ArrowUpRight size={12} /></a></div></article>
          </section>

          <DashboardCharts data={summary.trend} currency={summary.currency} />
          </>}

          {section === "payments" && pendingApprovals.length > 0 && <section className="panel approvals-panel"><div className="panel-heading"><div><h3>Needs your decision</h3><p>Large payments are held until an operator approves them.</p></div><span className="approval-count">{pendingApprovals.length} pending</span></div><div className="approval-list">{pendingApprovals.map((intent) => <div className="approval-row" key={intent.id}><span className="intent-avatar approval-avatar"><Clock3 size={16} /></span><span className="approval-info"><b>{intent.source_reference || `Intent #${intent.id}`}</b><small>{shortAddress(intent.payee)} · {formatDate(intent.created_at)}</small></span><span className="approval-amount">{formatAmount(intent.amount, intent.currency)}</span><button className="button button-small button-outline" disabled={busy} onClick={() => void decide(intent, "reject")}>Reject</button><button className="button button-small button-primary" disabled={busy} onClick={() => void decide(intent, "approve")}>Approve</button></div>)}</div></section>}

          {(section === "payments" || section === "overview") && <section className="panel table-panel" id="payment-activity"><div className="panel-heading table-heading"><div><h3>{section === "overview" ? "Recent payment activity" : "Payment activity"}</h3><p>Intent decisions and settlement results</p></div><div className="table-actions"><button className="filter-button"><SlidersHorizontal size={14} /> Filter</button><button className="more-button" aria-label="More options"><MoreHorizontal size={18} /></button></div></div>
            <div className="table-scroll"><table><thead><tr><th>PAYMENT</th><th>SUPPLIER</th><th>SOURCE</th><th>AMOUNT</th><th>STATUS</th><th>DATE</th><th /></tr></thead><tbody>
              {filteredIntents.length === 0 ? <tr><td colSpan={7}><div className="table-empty"><span className="empty-icon"><ArrowDownLeft size={18} /></span><b>{filter ? "No matching intents" : "No payment intents yet"}</b><small>Invoice-approved events sent through n8n or the agent will appear here.</small></div></td></tr> : filteredIntents.slice(0, 12).map((intent) => <tr key={intent.id}><td><span className={`intent-avatar ${intent.verdict === "blocked" ? "blocked-avatar" : ""}`}>{intent.source === "invoice" ? <FileCheck2 size={16} /> : <ArrowUpRight size={16} />}</span><span className="payment-cell"><b>{intent.source_reference || `Intent #${intent.id}`}</b><small>{intent.network} · #{intent.id}</small></span></td><td><span className="supplier-cell">{shortAddress(intent.payee)}</span></td><td><span className="source-pill">{intent.source}</span></td><td><b className="amount-cell">{formatAmount(intent.amount, intent.currency)}</b></td><td><StateBadge intent={intent} /></td><td><span className="date-cell">{formatDate(intent.created_at)}</span></td><td><button className="more-button" aria-label={`View intent ${intent.id}`} onClick={() => setSelectedIntent(intent)}><MoreHorizontal size={17} /></button></td></tr>)}
            </tbody></table></div>
            <div className="table-footer"><span>Showing {Math.min(filteredIntents.length, 12)} of {intentPage?.total ?? 0} intents</span><div><button disabled>Previous</button><button disabled>Next</button></div></div>
          </section>}

          {section === "audit" && <section className="panel table-panel audit-panel" id="audit-trail"><div className="panel-heading table-heading"><div><h3>Audit trail</h3><p>Append-only policy and payment events</p></div><span className="audit-lock"><ShieldCheck size={14} /> Immutable history</span></div><div className="table-scroll"><table><thead><tr><th>EVENT</th><th>REFERENCE</th><th>POLICY</th><th>AMOUNT</th><th>DETAIL</th><th>TIME</th></tr></thead><tbody>{!auditPage?.items.length ? <tr><td colSpan={6}><div className="table-empty"><b>No audit events yet</b><small>Every policy decision and payment transition will appear here.</small></div></td></tr> : auditPage.items.slice(0, 25).map((event) => <tr key={event.id}><td><span className="source-pill">{event.source}</span></td><td><span className="payment-cell"><b>{event.source_reference || (event.intent_id ? `Intent #${event.intent_id}` : "System event")}</b><small>{event.mandate_version ? `Policy v${event.mandate_version}` : "No mandate"}</small></span></td><td><span className={`state-badge ${event.verdict === "blocked" ? "danger" : event.verdict === "allowed" ? "success" : "warning"}`}><i />{event.verdict}</span></td><td><b className="amount-cell">{formatAmount(event.amount, event.currency)}</b></td><td><span className="audit-detail">{event.detail}</span></td><td><span className="date-cell">{formatDate(event.created_at)}</span></td></tr>)}</tbody></table></div><div className="table-footer"><span>Showing {Math.min(auditPage?.items.length ?? 0, 25)} of {auditPage?.total ?? 0} events</span><span>Audit entries are never edited or deleted.</span></div></section>}

          {(section === "suppliers" || section === "policy" || section === "overview") && <section className={`lower-grid ${section !== "overview" ? "single-panel-grid" : ""}`}>
            {(section === "suppliers" || section === "overview") && <>
            <article className="panel suppliers-panel" id="suppliers"><div className="panel-heading"><div><h3>Approved suppliers</h3><p>Destinations permitted by policy</p></div><button className="icon-button small-add" onClick={() => openPayeeEditor()} aria-label="Add supplier"><Plus size={17} /></button></div>
              {activePayees.length === 0 ? <div className="supplier-empty"><Users size={21} /><span>No suppliers approved yet.</span><button onClick={() => openPayeeEditor()}>Add your first supplier</button></div> : <div className="supplier-list">{activePayees.map((payee, index) => <div className="supplier-row" key={payee.id}><span className={`supplier-avatar supplier-color-${index % 4}`}>{initials(payee.name)}</span><span className="supplier-name"><b>{payee.name}</b><small title={payee.xrpl_address}>{payee.xrpl_address}</small></span><button className="supplier-edit" onClick={() => openPayeeEditor(payee)} title={`Edit ${payee.name}`} aria-label={`Edit ${payee.name}`} disabled={busy}><Pencil size={14} /></button><button className="supplier-remove" onClick={() => void deactivatePayee(payee)} title="Remove supplier" aria-label={`Remove ${payee.name}`} disabled={busy}><X size={15} /></button></div>)}</div>}
            </article>
            </>}
            {(section === "policy" || section === "overview") && <article className="panel mandate-panel" id="policy"><div className="panel-heading"><div><h3>Policy status</h3><p>Current finance guardrails</p></div><span className={`mandate-state ${mandate?.active ? "is-active" : "is-paused"}`}><i />{mandate?.active ? "Active" : mandate ? "Paused" : "Not set"}</span></div>
              {mandate ? <><div className="policy-rule"><span>Per-payment limit</span><b>{formatAmount(mandate.per_payment_cap, mandate.currency)}</b></div><div className="policy-rule"><span>Daily budget</span><b>{formatAmount(mandate.daily_cap, mandate.currency)}</b></div><div className="policy-rule"><span>Asset / issuer</span><b>{mandate.currency}{mandate.issuer ? ` · ${shortAddress(mandate.issuer)}` : " · issuer unset"}</b></div><div className="policy-rule"><span>Expires</span><b>{new Intl.DateTimeFormat("en-ZA", { dateStyle: "medium" }).format(new Date(mandate.expires_at))}</b></div><div className="policy-rule"><span>Policy version</span><b>v{mandate.version}</b></div><div className="policy-actions"><button className="button button-outline button-small" onClick={() => { setMandateForm(defaultMandateForm(mandate)); setMandateOpen(true); }}><SlidersHorizontal size={14} /> Edit policy</button>{mandate.active && <button className="pause-link" disabled={busy} onClick={() => void toggleMandate(false)}>Pause new payments</button>}</div><div className="policy-note"><ShieldCheck size={15} /><span>Limits are checked by the API before any configured XRPL signing attempt.</span></div></> : <div className="supplier-empty"><SlidersHorizontal size={21} /><span>Set a mandate to control payment permissions.</span></div>}
            </article>}
          </section>}
          <footer className="dashboard-footer"><span>Mandate · Finance operations</span><span>XRPL {summary.network} · No fiat payout configured</span></footer>
        </>}
      </div>
    </main>

    {mandateOpen && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setMandateOpen(false); }}><section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="mandate-title"><div className="modal-heading"><div><span className="eyebrow dark-eyebrow">PAYMENT POLICY</span><h2 id="mandate-title">{mandate ? "Update mandate" : "Set up mandate"}</h2><p>Saving changes pauses the mandate until you activate it.</p></div><button className="icon-button" onClick={() => setMandateOpen(false)} aria-label="Close"><X size={18} /></button></div><form onSubmit={saveMandate} className="modal-form"><div className="form-grid"><label>Per-payment cap<input type="number" min="0.000001" step="0.000001" required value={mandateForm.per_payment_cap} onChange={(event) => setMandateForm({ ...mandateForm, per_payment_cap: event.target.value })} /></label><label>Daily budget<input type="number" min="0.000001" step="0.000001" required value={mandateForm.daily_cap} onChange={(event) => setMandateForm({ ...mandateForm, daily_cap: event.target.value })} /></label><label>Asset<select value={mandateForm.currency} onChange={(event) => setMandateForm({ ...mandateForm, currency: event.target.value })}><option value="RLUSD">RLUSD (issued asset)</option><option value="XRP">XRP</option></select></label><label>Allowed issuer<input type="text" placeholder="Required for issued RLUSD" value={mandateForm.issuer} onChange={(event) => setMandateForm({ ...mandateForm, issuer: event.target.value })} /></label><label>Large payment approval threshold<input type="number" min="0.000001" step="0.000001" placeholder="Optional" value={mandateForm.large_payment_threshold} onChange={(event) => setMandateForm({ ...mandateForm, large_payment_threshold: event.target.value })} /></label><label>Maximum slippage (%)<input type="number" min="0" max="100" step="0.1" value={mandateForm.max_slippage_pct} onChange={(event) => setMandateForm({ ...mandateForm, max_slippage_pct: event.target.value })} /></label><label className="full-width">Mandate expiry<input type="datetime-local" required value={mandateForm.expires_at} onChange={(event) => setMandateForm({ ...mandateForm, expires_at: event.target.value })} /></label></div><div className="form-hint"><CircleAlert size={15} /> Payment execution only works on the configured XRPL test network. No fiat rail is connected.</div>{error && <div className="form-error" role="alert">{error}</div>}<div className="modal-actions"><button type="button" className="button button-outline" onClick={() => setMandateOpen(false)}>Cancel</button><button type="submit" className="button button-primary" disabled={busy}>{busy ? "Saving…" : "Save mandate"}<ArrowRight size={15} /></button></div></form></section></div>}

    {payeeOpen && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) { setPayeeOpen(false); setEditingPayee(null); } }}><section className="modal-card modal-compact" role="dialog" aria-modal="true" aria-labelledby="payee-title"><div className="modal-heading"><div><span className="eyebrow dark-eyebrow">COUNTERPARTY CONTROLS</span><h2 id="payee-title">{editingPayee ? "Edit approved supplier" : "Add approved supplier"}</h2><p>Only this XRPL destination will be eligible for policy approval.</p></div><button className="icon-button" onClick={() => { setPayeeOpen(false); setEditingPayee(null); }} aria-label="Close"><X size={18} /></button></div><form onSubmit={addPayee} className="modal-form"><label>Supplier name<input required minLength={2} maxLength={120} value={payeeName} onChange={(event) => setPayeeName(event.target.value)} placeholder="e.g. Atlas Components" /></label><label>XRPL classic address<input required minLength={25} maxLength={64} value={payeeAddress} onChange={(event) => setPayeeAddress(event.target.value)} placeholder="r…" /></label>{error && <div className="form-error" role="alert">{error}</div>}<div className="modal-actions"><button type="button" className="button button-outline" onClick={() => { setPayeeOpen(false); setEditingPayee(null); }}>Cancel</button><button type="submit" className="button button-primary" disabled={busy}>{busy ? "Saving…" : editingPayee ? "Save changes" : "Approve supplier"}<Check size={15} /></button></div></form></section></div>}

    {selectedIntent && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelectedIntent(null); }}><section className="modal-card modal-compact" role="dialog" aria-modal="true" aria-labelledby="intent-title"><div className="modal-heading"><div><span className="eyebrow dark-eyebrow">PAYMENT INTENT · #{selectedIntent.id}</span><h2 id="intent-title">{selectedIntent.source_reference || `Intent #${selectedIntent.id}`}</h2><p>Source event, policy decision and settlement evidence.</p></div><button className="icon-button" onClick={() => setSelectedIntent(null)} aria-label="Close"><X size={18} /></button></div><div className="intent-detail"><div className="intent-detail-amount">{formatAmount(selectedIntent.amount, selectedIntent.currency)}</div><StateBadge intent={selectedIntent} /><div className="intent-detail-row"><span>Beneficiary</span><b>{shortAddress(selectedIntent.payee)}</b></div><div className="intent-detail-row"><span>Source</span><b>{selectedIntent.source}</b></div><div className="intent-detail-row"><span>Network</span><b>XRPL {selectedIntent.network}</b></div><div className="intent-detail-row"><span>Policy version</span><b>{selectedIntent.mandate_version ? `v${selectedIntent.mandate_version}` : "No mandate"}</b></div><div className="intent-detail-row"><span>Received</span><b>{formatDate(selectedIntent.created_at)}</b></div><div className="intent-detail-explanation"><b>Policy explanation</b><p>{selectedIntent.detail}</p></div>{selectedIntent.ledger_result && <div className="intent-detail-row"><span>Ledger result</span><b>{selectedIntent.ledger_result}</b></div>}{selectedIntent.tx_hash && <a className="explorer-link" href={`https://${selectedIntent.network}.xrpl.org/transactions/${selectedIntent.tx_hash}`} target="_blank" rel="noreferrer">View transaction on explorer <ArrowUpRight size={15} /></a>}</div></section></div>}
  </div>;
}
