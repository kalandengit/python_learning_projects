# Sprint 10 Review — Profiles, Invitation Emails, Audit Logs, Notifications

## Goal
Add operational collaboration capabilities needed before the product becomes team-ready: profile settings, outbound invitation email support, audit history, and user notifications.

## What changed
- Added `profiles` table with auth trigger for automatic profile creation.
- Added `audit_logs` table and `insert_audit_log` RPC for compliance-friendly event history.
- Added `notifications` table with user-scoped RLS.
- Added Resend-backed invitation emails with safe console fallback when `RESEND_API_KEY` is missing.
- Added Settings page for user profile updates.
- Added Notifications page with read/unread actions.
- Added Admin Audit Logs page.
- Added audit events for team invitation/member actions.

## Security review
- Server actions still verify authentication and organization role before mutation.
- RLS protects profiles, notifications, audit logs, and collaboration tables.
- Invitation acceptance checks signed-in email against invited email.
- Audit metadata intentionally avoids sensitive content.

## Tradeoffs
- Email templates use simple HTML rather than React Email to keep Sprint 10 lightweight.
- Audit logs are application-level plus RPC-based, not full PGAudit. This is sufficient for MVP visibility; PGAudit/SIEM forwarding belongs in Enterprise hardening.
- Notifications are database-backed only. Real-time subscriptions and email digests are deferred.

## Manual QA checklist
1. Apply migration `010_sprint10_profiles_audit_notifications.sql`.
2. Set `RESEND_API_KEY` and `EMAIL_FROM` or confirm invitation links are logged in server console.
3. Invite a teammate from `/team`.
4. Confirm the email link points to `/api/invitations/[token]`.
5. Accept the invite as the matching email.
6. Visit `/notifications` as the inviter and confirm an acceptance notification appears.
7. Visit `/admin/audit-logs` and confirm invitation/member actions are recorded.
8. Edit `/settings` and confirm profile data persists.

## Risks
- Supabase email metadata may not include email in JWT in every auth configuration; acceptance also reads `auth.getUser()`, but RLS policies use JWT email. Test in hosted Supabase before production launch.
- Resend sender domain must be verified before customer-facing production email.
- Audit logs should become immutable with stricter database permissions before enterprise customers.

## Next sprint recommendation
Sprint 11 should focus on automated testing, CI, linting, E2E smoke tests, and security checks before more product features are added.
