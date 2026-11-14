"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight, LockKeyhole, Mail, UserRound } from "lucide-react";
import { useRouter } from "next/navigation";

export default function RegisterPage() {
  const router = useRouter();
  const [registrationOpen, setRegistrationOpen] = useState<boolean | null>(null);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    void fetch("/api/auth/registration-status", { cache: "no-store" })
      .then((response) => response.json())
      .then((data) => { if (alive) setRegistrationOpen(Boolean(data.registration_open)); })
      .catch(() => { if (alive) setRegistrationOpen(false); });
    return () => { alive = false; };
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    if (password !== confirmPassword) { setError("Those passwords do not match."); return; }
    setBusy(true);
    try {
      const response = await fetch("/api/auth/register", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name: fullName, email, password }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "Unable to create your account");
      router.push("/dashboard"); router.refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to create your account");
    } finally { setBusy(false); }
  }

  return <main className="login-shell">
    <div className="login-backdrop" />
    <Link href="/" className="login-back"><ArrowLeft size={16} /> Back to Mandate</Link>
    <section className="login-card auth-card-wide">
      <div className="login-mark"><span className="brand-mark"><span /></span></div>
      <div className="eyebrow dark-eyebrow">WORKSPACE SETUP</div>
      <h1>{registrationOpen === false ? "Account already set up." : "Create your account."}</h1>
      {registrationOpen === false ? <>
        <p>Mandate has one owner account for this local finance workspace. Sign in, or reset its password if you can’t access it.</p>
        <div className="auth-actions"><Link href="/login" className="button button-primary login-submit">Go to sign in <ArrowRight size={16} /></Link><Link href="/forgot-password" className="text-link auth-centered-link">Forgot password?</Link></div>
      </> : <>
        <p>Create the owner account for your Mandate finance workspace.</p>
        <form onSubmit={submit} className="login-form">
          <label htmlFor="full-name">Your name</label>
          <div className="input-wrap"><UserRound size={16} /><input id="full-name" autoComplete="name" required minLength={2} maxLength={120} value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="John Doe" /></div>
          <label htmlFor="email">Work email</label>
          <div className="input-wrap"><Mail size={16} /><input id="email" type="email" autoComplete="email" required maxLength={320} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" /></div>
          <label htmlFor="password">Password</label>
          <div className="input-wrap"><LockKeyhole size={16} /><input id="password" type="password" autoComplete="new-password" required minLength={12} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 12 characters" /></div>
          <label htmlFor="confirm-password">Confirm password</label>
          <div className="input-wrap"><LockKeyhole size={16} /><input id="confirm-password" type="password" autoComplete="new-password" required minLength={12} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} placeholder="Enter it again" /></div>
          {error && <div className="form-error" role="alert">{error}</div>}
          <button className="button button-primary login-submit" disabled={busy}>{busy ? "Creating account…" : "Create account"}<ArrowRight size={17} /></button>
        </form>
        <div className="auth-switch">Already registered? <Link href="/login">Sign in</Link></div>
      </>}
    </section>
    <div className="login-footer">Your API credentials stay private to the server.</div>
  </main>;
}
