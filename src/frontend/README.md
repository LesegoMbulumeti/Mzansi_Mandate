# Mandate web app

Next.js 16 App Router application with a public landing page and a protected finance dashboard. Lucide React provides icons, ApexCharts renders admin charts from persisted API summaries, and tsParticles adds a decorative landing-page field with a reduced-motion fallback.

## Local setup

From `src/`:

```bash
cp .env.example .env
```

Set `SESSION_SECRET` in `.env`; the API/admin credentials stay server-side and are not used as user passwords. From `src/frontend/`:

```bash
npm install
npm run dev
```

The web app runs at `http://localhost:3000`. It proxies authenticated dashboard requests to `MANDATE_API_URL` and sends `MANDATE_ADMIN_API_KEY` from the server only. The API key is not exposed to client JavaScript.

## Pages

- `/`: product landing page and invoice-to-settlement workflow overview.
- `/register`: one-time owner-account setup for the shared local finance workspace.
- `/login`: email and password sign-in; the server creates an HTTP-only signed session cookie.
- `/forgot-password` and `/reset-password`: single-use, 30-minute recovery links. In development, the reset link is shown in the app and written to API logs. Configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, and `APP_PUBLIC_URL` to deliver recovery emails.
- `/dashboard`: live API dashboard with mandate/payee controls, approvals, payment status, ApexCharts summaries, and a demo invoice action that calls the active n8n webhook server-side.

This initial account flow is single-owner: public registration closes after the first account because the current finance data model is one shared workspace. Team invitations and per-workspace roles are a separate follow-up before multi-tenant deployment. Configure a real SMTP provider before production so account recovery links are delivered by email.

## Routine demo workflow

After importing and activating the n8n workflow and selecting its two Header Auth credentials, sign in to the dashboard and use **Try the invoice workflow**. The Next.js server sends the request to n8n; webhook secrets are not sent to browser JavaScript. This demo is blocked while `XRPL_PAYMENTS_ENABLED=true`, so the dashboard button cannot accidentally submit a ledger payment. The first import/credential setup remains in n8n's UI.
