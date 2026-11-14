"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight, LockKeyhole } from "lucide-react";

export default function ResetPasswordPage() {
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setToken(new URLSearchParams(window.location.search).get("token") ?? "");
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    if (password !== confirmPassword) { setError("Those passwords do not match."); return; }
    setBusy(true);
    try {
      const response = await fetch("/api/auth/reset-password", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "Unable to reset password");
      setDone(true);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to reset password");
    } finally { setBusy(false); }
  }

  return <main className="login-shell"><div className="login-backdrop" />
    <Link href="/login" className="login-back"><ArrowLeft size={16} /> Back to sign in</Link>
    <section className="login-card">
      <div className="login-mark"><span className="brand-mark"><span /></span></div>
      <div className="eyebrow dark-eyebrow">ACCOUNT RECOVERY</div>
      <h1>{done ? "Password updated." : "Choose a new password."}</h1>
      {done ? <><p>Your password has been changed. You can now sign in with it.</p><Link href="/login" className="button button-primary login-submit auth-login-link">Continue to sign in <ArrowRight size={16} /></Link></> : !token ? <p>This reset link is missing or invalid. Request a new one from the sign-in page.</p> : <>
        <p>Use at least 12 characters. This reset link can only be used once.</p>
        <form onSubmit={submit} className="login-form">
          <label htmlFor="password">New password</label>
          <div className="input-wrap"><LockKeyhole size={16} /><input id="password" type="password" autoComplete="new-password" required minLength={12} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 12 characters" /></div>
          <label htmlFor="confirm-password">Confirm new password</label>
          <div className="input-wrap"><LockKeyhole size={16} /><input id="confirm-password" type="password" autoComplete="new-password" required minLength={12} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} placeholder="Enter it again" /></div>
          {error && <div className="form-error" role="alert">{error}</div>}
          <button className="button button-primary login-submit" disabled={busy}>{busy ? "Updating…" : "Update password"}<ArrowRight size={17} /></button>
        </form>
      </>}
    </section>
    <div className="login-footer">Never share your reset link with anyone.</div>
  </main>;
}
