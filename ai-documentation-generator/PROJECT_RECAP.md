# AI Documentation Generator — Project Recap

## Current sprint
Sprint 13 — Browser Extension MVP

## Status
Implemented in the integrated Sprint 12 repository. Local dependency installation and browser testing are still required.

## Completed
- Previous Sprint 01–12 application foundation.
- Manifest V3 React/TypeScript browser extension.
- Visible, region, and experimental full-page captures.
- Scoped extension token lifecycle and settings UI.
- Extension identity, projects, capture/upload, generation, and job-status APIs.
- AI queue integration and document deep links.

## Database
Apply `supabase/migrations/013_sprint13_browser_extension.sql`.

## Run next
1. Install and run the root application.
2. Apply Supabase migrations through 013.
3. Build `browser-extension/`.
4. Generate a token in Settings and perform a real capture.
5. Run the AI worker or database job drainer.

## Known risks
- ~~Root dependencies use `latest`~~ — **resolved**: dependencies are pinned to
  exact versions with a committed `package-lock.json`; lint, typecheck, unit
  tests, security-header check, and a production build were all validated
  against the pins (Next 15.x, Tailwind 3.x, ESLint 9, TypeScript 5 — do not
  bump these majors without migrating code).
- Full-page stitching can duplicate sticky elements.
- Manual tokens should become PKCE OAuth in a later sprint.
- The existing repository must still be validated against a real Supabase and Stripe environment.

## Recommended Sprint 14
Integration test and stabilization: pin dependencies, generate DB types, run migrations in staging, fix build/type errors, test extension-to-worker flow, and add OAuth/PKCE design.
