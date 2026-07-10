# Sprint 02 Review

## Goal
Connect the product shell to Supabase persistence so users can create projects, upload screenshots, generate documents, edit Markdown, and share generated docs.

## Implemented
- Organization auto-creation for first dashboard access
- Project creation/list page
- Upload form backed by Supabase Storage and `uploads` table
- Upload detail page with signed preview URL
- Generate document action from upload using signed URL
- Document record persistence
- Document list and detail pages
- Markdown edit/save flow
- Markdown export endpoint connected to database
- Share link generation and public shared page
- Migration `002_sprint02_persistence.sql` with RLS, indexes, triggers, and storage bucket policies

## Review Notes
- The workflow is synchronous for now. This is acceptable for Sprint 02 but should move to BullMQ/background jobs in Sprint 03 or 04 for reliability.
- AI generation depends on `OPENAI_API_KEY`. Without it, uploads/projects still work but generation fails.
- Storage bucket is private; previews use signed URLs. This is the right MVP security posture.
- RLS has been improved to organization membership checks instead of only `created_by` ownership.

## Known Gaps
- No visual loading state for server actions yet.
- No background retry queue.
- No OCR fallback provider.
- No PDF export yet.
- No automated tests in this sprint.
- No Stripe gating yet.

## Definition of Done Status
- Functional code generated: yes
- Persistence added: yes
- Security/RLS improved: yes
- Runtime tested with real credentials: no
- Automated tests: no
