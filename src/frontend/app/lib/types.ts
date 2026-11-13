export type Mandate = {
  id: number;
  per_payment_cap: string;
  daily_cap: string;
  max_slippage_pct: string;
  large_payment_threshold: string | null;
  currency: string;
  issuer: string | null;
  version: number;
  expires_at: string;
  active: boolean;
  created_at: string;
  updated_at: string | null;
};

export type PaymentIntent = {
  id: number;
  idempotency_key: string;
  mandate_version: number | null;
  payee: string;
  amount: string;
  currency: string;
  issuer: string | null;
  network: string;
  source: string;
  source_reference: string | null;
  reason: string;
  verdict: "allowed" | "blocked" | "needs_approval";
  detail: string;
  status: string;
  tx_hash: string | null;
  ledger_result: string | null;
  created_at: string;
};

export type Payee = {
  id: number;
  mandate_id: number;
  name: string;
  xrpl_address: string;
  active: boolean;
};

export type DashboardSummary = {
  mandate: Mandate | null;
  approved_payees: number;
  intents_today: number;
  allowed_today: number;
  blocked_today: number;
  pending_approval: number;
  daily_spend: string;
  currency: string;
  network: string;
  execution_enabled: boolean;
  trend: { label: string; allowed: number; blocked: number; volume: string }[];
  recent_intents: PaymentIntent[];
};

export type AuditEvent = {
  id: number;
  intent_id: number | null;
  payee: string;
  amount: string;
  currency: string;
  source: string;
  source_reference: string | null;
  mandate_version: number | null;
  reason: string;
  verdict: string;
  detail: string;
  tx_hash: string | null;
  created_at: string;
};

export type Page<T> = { items: T[]; total: number; limit: number; offset: number };
