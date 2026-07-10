# Sprint 06 Review — Export and Share Polish

## Completed

- Added HTML export route.
- Added PDF export route using Playwright/Chromium when available.
- Added export audit table with RLS policies.
- Added reusable HTML document renderer.
- Added export action component to the document editor sidebar.
- Added polished shared document toolbar.
- Added shared Markdown and HTML download endpoints.

## Key Decisions

- PDF rendering uses Playwright because browser-based rendering preserves CSS and produces better SaaS documentation exports than hand-built PDF primitives.
- PDF generation remains inside a Node.js route for the MVP, but should move to a dedicated worker/container as export volume grows.
- Export events are persisted immediately because they support future billing limits, analytics, and enterprise audit requirements.

## Tradeoffs

- Playwright adds deployment complexity because Chromium must be installed in the runtime environment.
- The MVP HTML renderer uses `marked`; before accepting arbitrary public HTML, add sanitization with a strict allowlist.
- Shared public downloads do not write export records yet because anonymous exports require a different analytics model.

## Self-Review

- Access to private exports is protected by existing document RLS.
- Shared documents only render when visibility is `shared` or `public`.
- Export files use slugified filenames.
- PDF route returns a clear 503 when Chromium is unavailable.

## Next Sprint

Sprint 07 should add Stripe billing, plan limits, and usage quotas for uploads, AI generations, exports, and storage.
