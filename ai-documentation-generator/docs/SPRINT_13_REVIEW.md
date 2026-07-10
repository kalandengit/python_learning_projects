# Sprint 13 Review — Browser Extension MVP

## Delivered
- Manifest V3 React/TypeScript extension.
- Visible-tab, selectable-region, and experimental segmented full-page capture.
- Scoped, revocable extension access tokens stored as SHA-256 hashes.
- Dedicated `/api/extension/*` routes for identity, projects, captures, and job polling.
- Upload persistence, quota checks, AI job creation, queue integration, and document deep-linking.
- Settings UI for generating and revoking extension tokens.
- Extension build documentation and a small unit test.

## Security review
- No Supabase service key or user password is shipped to the browser extension.
- Tokens are shown once, stored locally by Chrome, hashed server-side, scoped, and revocable.
- Project IDs are revalidated against the token's organization.
- Upload MIME type and size are validated server-side.
- Extension API queries are constrained to the authenticated organization.

## Trade-offs
A manually generated scoped token is used for the MVP instead of OAuth. This is simpler and reliable for self-hosted/local environments. V2 should replace it with a PKCE authorization flow and short-lived access/refresh tokens.

## Validation required locally
Run root and extension installs/builds. Test capture on regular HTTPS pages; Chrome internal pages cannot be captured or scripted.
