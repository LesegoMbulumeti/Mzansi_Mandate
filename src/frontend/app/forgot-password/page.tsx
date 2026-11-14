"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight, Mail } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [developmentResetUrl, setDevelopmentResetUrl] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const response = await fetch("/api/auth/forgot-password", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "Unable to request a reset link");
      setDevelopmentResetUrl(result.development_reset_url ?? "");
      setSent(true);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to request a reset link");
    } finally { setBusy(false); }
  }

  return <main className="login-shell"><div className="login-backdrop" />
    <Link href="/login" className="login-back"><ArrowLeft size={16} /> Back to sign in</Link>
    <section className="login-card">
      <div className="login-mark"><span className="brand-mark"><span /></span></div>
      <div className="eyebrow dark-eyebrow">ACCOUNT RECOVERY</div>
      <h1>{sent ? "Check your inbox." : "Reset your password."}</h1>
      {sent ? <><p>If an account exists for <b>{email}</b>, reset instructions are on their way. The link expires after 30 minutes.</p>{developmentResetUrl && <div className="dev-reset-link"><span>Local development reset link</span><Link href={developmentResetUrl}>Reset your password <ArrowRight size={14} /></Link></div>}</> : <>
        <p>Enter the email you used to create your Mandate account. We’ll send a one-time reset link.</p>
        <form onSubmit={submit} className="login-form">
          <label htmlFor="email">Work email</label>
          <div className="input-wrap"><Mail size={16} /><input id="email" type="email" autoComplete="email" required maxLength={320} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" /></div>
          {error && <div className="form-error" role="alert">{error}</div>}
          <button className="button button-primary login-submit" disabled={busy}>{busy ? "Sending…" : "Send reset link"}<ArrowRight size={17} /></button>
        </form>
      </>}
      <div className="auth-switch"><Link href="/login">Return to sign in</Link></div>
    </section>
    <div className="login-footer">Password reset links are single-use and expire in 30 minutes.</div>
  </main>;
}
