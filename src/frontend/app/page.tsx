import Link from "next/link";
import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  BadgeCheck,
  Blocks,
  CircleDollarSign,
  FileCheck2,
  Fingerprint,
  LockKeyhole,
  MoveUpRight,
  Radio,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import { ParticleField } from "@/app/components/ParticleField";

const steps = [
  { number: "01", title: "Business event", text: "An approved supplier invoice arrives from your finance workflow." },
  { number: "02", title: "Policy check", text: "The service checks the payee, asset, payment cap and daily budget." },
  { number: "03", title: "Settlement proof", text: "A validated XRPL result and transaction hash link back to the invoice." },
];

export default function HomePage() {
  return (
    <main className="site-shell">
      <header className="site-nav wrap">
        <Link href="/" className="brand-lockup" aria-label="Mandate home">
          <span className="brand-mark"><span /></span>
          <span>mandate<span className="brand-period">.</span></span>
        </Link>
        <nav className="site-nav-links" aria-label="Main navigation">
          <a href="#workflow">Workflow</a>
          <a href="#controls">Controls</a>
          <a href="#rails">XRPL rails</a>
        </nav>
        <Link href="/login" className="nav-cta">Open dashboard <ArrowUpRight size={15} /></Link>
      </header>

      <section className="hero-section">
        <div className="hero-glow" />
        <ParticleField />
        <div className="hero-content wrap">
          <div className="eyebrow"><span className="eyebrow-dot" /> FINANCE OPERATIONS, IN MOTION</div>
          <h1>Move payables<br /><span>with purpose.</span></h1>
          <p className="hero-copy">From an approved supplier invoice to a verified ledger result, give every payment a clear route, a policy check and a traceable story.</p>
          <div className="hero-actions">
            <Link href="/login" className="button button-primary">Explore the dashboard <ArrowRight size={17} /></Link>
            <a href="#workflow" className="text-link">See how it works <ArrowDownRight size={16} /></a>
          </div>
          <div className="hero-note"><LockKeyhole size={14} /> Policy-controlled execution <span /> Built for African SME workflows</div>
        </div>

        <div className="hero-visual" aria-label="Illustration of an invoice moving through policy checks to settlement">
          <div className="visual-orbit orbit-one" />
          <div className="visual-orbit orbit-two" />
          <div className="visual-node node-left"><FileCheck2 size={20} /><span>Invoice approved</span></div>
          <div className="visual-node node-right"><BadgeCheck size={20} /><span>Validated on XRPL</span></div>
          <div className="visual-card">
            <div className="visual-card-top"><span className="mini-label">ILLUSTRATIVE INTENT</span><span className="status-chip"><i /> EXAMPLE STATE</span></div>
            <div className="visual-card-amount">RLUSD <b>2,450.00</b></div>
            <div className="visual-card-divider" />
            <div className="visual-card-meta"><span>Beneficiary</span><strong>Atlas Components</strong></div>
            <div className="visual-card-meta"><span>Source reference</span><strong>INV-2048 · Supplier payable</strong></div>
            <div className="visual-card-footer"><span><ShieldCheck size={14} /> Within mandate</span><MoveUpRight size={15} /></div>
          </div>
          <div className="floating-proof"><span className="proof-icon"><Fingerprint size={18} /></span><span><b>Every action</b><small>has an audit trail</small></span><span className="proof-check"><BadgeCheck size={16} /></span></div>
          <div className="floating-rail"><span className="rail-pulse" /><span>XRPL TESTNET</span><span className="rail-divider" /><span>3–5 sec finality*</span></div>
        </div>
        <div className="hero-bottom wrap"><span>ONE CONTROLLED FLOW</span><div /><span>INVOICE</span><ArrowRight size={14} /><span>POLICY</span><ArrowRight size={14} /><span>SETTLEMENT</span><ArrowRight size={14} /><span>RECONCILIATION</span></div>
      </section>

      <section className="section workflow-section wrap" id="workflow">
        <div className="section-heading">
          <div><div className="eyebrow dark-eyebrow">THE WORKFLOW LAYER</div><h2>Payments that keep<br />their context.</h2></div>
          <p>Mandate connects a business event to the payment decision and the evidence finance teams need to reconcile it.</p>
        </div>
        <div className="step-grid">
          {steps.map((step) => <article className="step-card" key={step.number}><span className="step-number">{step.number}</span><h3>{step.title}</h3><p>{step.text}</p><span className="step-line" /></article>)}
        </div>
      </section>

      <section className="controls-section" id="controls">
        <div className="controls-inner wrap">
          <div className="controls-copy"><div className="eyebrow">BUILT FOR FINANCE TEAMS</div><h2>Automation needs<br /><span>guardrails.</span></h2><p>Agents can handle eligible work automatically. The policy service checks each intent independently, while humans keep control of the mandate and its emergency stop.</p><Link href="/login" className="text-link light-link">See the control room <ArrowRight size={16} /></Link></div>
          <div className="control-list">
            <div className="control-row"><span className="control-icon"><ShieldCheck size={20} /></span><span><b>Counterparty controls</b><small>Only approved supplier destinations can pass.</small></span><span className="control-state">ACTIVE</span></div>
            <div className="control-row"><span className="control-icon"><CircleDollarSign size={20} /></span><span><b>Spend boundaries</b><small>Per-payment and daily budgets are checked before signing.</small></span><span className="control-state">ACTIVE</span></div>
            <div className="control-row"><span className="control-icon"><Fingerprint size={20} /></span><span><b>Human authority</b><small>High-value exceptions wait for a human decision.</small></span><span className="control-state muted-state">READY</span></div>
            <div className="control-row"><span className="control-icon"><Radio size={20} /></span><span><b>Emergency stop</b><small>Pause policy execution; revoke ledger key when configured.</small></span><span className="control-state muted-state">READY</span></div>
          </div>
        </div>
      </section>

      <section className="rails-section wrap" id="rails">
        <div className="rails-copy"><div className="eyebrow dark-eyebrow">SETTLEMENT, MADE VISIBLE</div><h2>Connected to the<br />ledger. Clear to finance.</h2><p>Test and inspect payment execution on XRPL before building provider-specific local payout connections. A transaction hash is paired with the validated ledger result, never shown as proof on its own.</p><div className="rail-pills"><span><Blocks size={15} /> XRPL Testnet</span><span><Workflow size={15} /> n8n workflows</span><span><ShieldCheck size={15} /> Independent policy</span></div></div>
        <div className="settlement-card"><div className="settlement-header"><span>PAYMENT JOURNEY</span><span className="live-label"><i /> TRACEABLE</span></div><div className="journey-row"><span className="journey-icon invoice-icon"><FileCheck2 size={18} /></span><span><b>Supplier invoice</b><small>Source event · n8n</small></span><span className="journey-time">01</span></div><div className="journey-connector" /><div className="journey-row"><span className="journey-icon policy-icon"><ShieldCheck size={18} /></span><span><b>Mandate policy</b><small>Payee · budget · expiry</small></span><span className="journey-time">02</span></div><div className="journey-connector" /><div className="journey-row"><span className="journey-icon xrpl-icon"><Blocks size={18} /></span><span><b>XRPL payment</b><small>Validated result · explorer hash</small></span><span className="journey-time">03</span></div><div className="settlement-bottom"><span>Source to settlement, in one audit trail</span><ArrowUpRight size={16} /></div></div>
      </section>

      <section className="cta-section wrap"><div className="cta-card"><div className="cta-orb" /><div><div className="eyebrow">READY TO SEE THE FLOW?</div><h2>Bring payables<br />into focus.</h2><p>Explore the Mandate finance dashboard and its policy-controlled workflow.</p></div><Link href="/login" className="button button-white">Open dashboard <ArrowUpRight size={16} /></Link></div></section>

      <footer className="site-footer wrap"><Link href="/" className="brand-lockup"><span className="brand-mark"><span /></span><span>mandate<span className="brand-period">.</span></span></Link><span>Policy-controlled payables on XRPL Testnet</span><span>© 2026 Mzansi Mandate</span></footer>
      <p className="footnote wrap">*Typical XRPL settlement time; actual results depend on network validation. This demo does not provide fiat accounts, local currency payout or financial advice.</p>
    </main>
  );
}
