# EMS Frontend (Part 4)

React 19 + TypeScript (strict) + Vite 8 + Tailwind v4 (CSS-first, no
`tailwind.config.js`). Server state via TanStack Query v5, client state via
Zustand 5, response validation via Zod 4, HTTP via ky.

## Scripts

```bash
npm install
npm run dev        # Vite dev server on :5173 (proxies /api to :8000)
npm run build      # tsc -b && vite build
npm run lint       # tsc --noEmit (strict)
npm run test       # vitest run
```

## What's here (master prompt §6 Part 4)

- **`lib/api.ts`** — ky client: bearer injection, single-flight 401 →
  refresh-rotation retry, generic error extraction. Every response is parsed
  through a Zod schema (`lib/schemas.ts`).
- **`store/auth.ts`** — Zustand token store (localStorage), decodes access-token
  claims for UI shaping only (never for authorization).
- **Auth** — passkey-first login (`@github/webauthn-json`), password + TOTP
  fallback, register.
- **Events** — cursor infinite scroll → detail → tier picker.
- **Purchase** — Idempotency-Key mutation; FREE issues instantly, PAID redirects
  to Stripe Checkout; success/cancel pages.
- **My Tickets** — QR PNG (authenticated blob, refreshed every ~55 s), 60 s
  auto-refetch, status chips.
- **Organizer wizard** — details → Leaflet map pin (+ optional geocoding) →
  tiers → publish.
- **Badge admin** — issue (type, zones, validity), toggle, list.
- **Scanner PWA** — `html5-qrcode` camera scan, online validate, offline
  IndexedDB queue with reconnect sync.

Accessibility: WCAG 2.2 AA — skip link, visible focus, labelled fields with
`aria-describedby` errors, `aria-live` scan feedback, reduced-motion support.

Role-gated routes (organizer/badge/scanner) are code-split so attendees never
download them.
