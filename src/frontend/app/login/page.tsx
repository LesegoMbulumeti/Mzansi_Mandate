"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight, LockKeyhole, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const response = await fetch("/api/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "Unable to sign in");
      router.push("/dashboard");
      router.refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to sign in");
    } finally {
      setBusy(false);
    }
  }

  return <main className="login-shell">
    <div className="login-backdrop" />
    <Link href="/" className="login-back"><ArrowLeft size={16} /> Back to Mandate</Link>
    <section className="login-card">
      <div className="login-mark"><span className="brand-mark"><span /></span></div>
      <div className="eyebrow dark-eyebrow">FINANCE OPERATIONS</div>
      <h1>Welcome back.</h1>
      <p>Sign in to review your payment workflow and policy controls.</p>
      <form onSubmit={submit} className="login-form">
        <label htmlFor="password">Dashboard password</label>
        <div className="input-wrap"><LockKeyhole size={17} /><input id="password" type="password" autoComplete="current-password" required minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter your password" /></div>
        {error && <div className="form-error" role="alert">{error}</div>}
        <button className="button button-primary login-submit" disabled={busy}>{busy ? "Signing in…" : "Continue"}<ArrowRight size={17} /></button>
      </form>
      <div className="login-security"><ShieldCheck size={15} /> Protected operator access <span>·</span> XRPL Testnet</div>
    </section>
    <div className="login-footer">Mzansi Mandate <span>·</span> Payment controls with context</div>
  </main>;
}
