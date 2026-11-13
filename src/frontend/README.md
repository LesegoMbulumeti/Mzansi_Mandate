# Mandate web app

Next.js 16 App Router application with a public landing page and a password-protected finance dashboard. Lucide React provides icons, ApexCharts renders admin charts from persisted API summaries, and tsParticles adds a decorative landing-page field with a reduced-motion fallback.

## Local setup

From `src/`:

```bash
cp .env.example .env
```

Set `ADMIN_LOGIN_PASSWORD` and `SESSION_SECRET` in `.env`. From `src/frontend/`:

```bash
npm install
npm run dev
```

The web app runs at `http://localhost:3000`. It proxies authenticated dashboard requests to `MANDATE_API_URL` and sends `MANDATE_ADMIN_API_KEY` from the server only. The API key is not exposed to client JavaScript.

## Pages

- `/`: product landing page and invoice-to-settlement workflow overview.
- `/login`: dashboard password login; the server creates an HTTP-only signed session cookie.
- `/dashboard`: live API dashboard with mandate/payee controls, approvals, payment status and ApexCharts summaries.

The local password login is a single-operator development gate, not multi-user identity, SSO, MFA or production authorization. Deploy behind proper identity and role management before real funds or customer data are used.
