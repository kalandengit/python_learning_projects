# Sprint 05 Review — Editor Hardening and Version History

## Goal
Make the document editor safer for real use by adding version snapshots, restore flows, document metadata, and autosave-ready APIs.

## What changed
- Added `document_versions` table with organization-scoped RLS.
- Added document metadata columns: excerpt, word count, last editor, last saved timestamp.
- Added save flow that snapshots every manual edit.
- Added restore flow that creates a new snapshot after restoration.
- Added version history sidebar in the document detail page.
- Added autosave API endpoint for future debounced client autosave.
- Added version listing and restore API endpoints for future richer editor UX.

## Design decisions
- Version snapshots are immutable rows instead of overwriting old content.
- Restore creates a new version rather than deleting history.
- The MVP editor remains Markdown-first to avoid premature complexity.
- TipTap remains in the project as the future rich editor path, but Sprint 05 keeps persistence stable first.

## Trade-offs
- Snapshotting every save is simple and reliable, but can create many rows. Later sprints should add debounce, diffing, and retention policies.
- Markdown-first editing is faster to ship than a complete TipTap editor, but less polished for non-technical users.
- Autosave API is present, but the client does not autosave yet to avoid accidental excessive writes before rate limiting.

## Security review
- Version rows use organization membership RLS.
- Restore operations require authenticated access and RLS-visible version/document rows.
- Client cannot choose organization_id directly in server actions.

## Next sprint
Sprint 06 should implement PDF export, HTML export, export tracking, and share page polish.
