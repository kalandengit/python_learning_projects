# Project review — version 1.1.0

## Scope

The complete archive was inventoried, including the FastAPI application, browser
client, tests, Docker and CI configuration, shell installers, skill sources,
plugin manifests, and documentation. Three supplied N'Ko research documents
were compared and distilled into `nko-voice-transcriptor/NKO_RESOURCES.md`.

## Implemented findings

| Area | Finding | Resolution |
| --- | --- | --- |
| Uploads | The server buffered an entire request before enforcing its size limit. | Read only the configured limit plus one byte before rejection. |
| Authentication | A signed token with a non-integer subject caused an unhandled conversion error. | Reject malformed subjects with HTTP 401. |
| Registration | Concurrent inserts could bypass the friendly duplicate pre-check and expose an integrity error. | Catch the unique-constraint race, roll back, and return HTTP 409. |
| Privacy | Sensitive API responses did not explicitly prevent browser/proxy caching. | Add `Cache-Control: no-store` to auth, transcription, and history routes. |
| Browser security | Microphone scope, opener isolation, and production HSTS were not declared. | Add Permissions Policy, COOP, and production-only HSTS. |
| Packaging | Test and lint packages were installed in production containers. | Move them to `requirements-dev.txt`; update CI and setup docs. |
| CI | Action majors and the dependency install path were outdated after the split. | Update the workflow and install development requirements. |
| Documentation | The repository landing page was effectively empty. | Add project, skill, setup, and license guidance. |
| N'Ko accuracy | Research confirms native N'Ko normally needs information absent from plain Latin input, especially tone. | Keep output editable and document it as a draft, not full orthographic transcription. |

## Verification performed

- Parsed and byte-compiled all Python application and test modules.
- Validated plugin marketplace JSON files.
- Syntax-checked all shell scripts.
- Integrity-tested the release ZIP.
- Checked current FastAPI, Uvicorn, SQLAlchemy, Pydantic Settings, PyJWT, GitHub
  action, Unicode, W3C, Keyman, and ACL references against their primary pages.

The build environment did not contain the project's third-party Python test and
lint packages, so the full Pytest and Ruff suites were not executed locally.
CI remains configured to run both after installing `requirements-dev.txt`.

## Prioritized future work

1. Native-speaker review and a licensed gold evaluation corpus for N'Ko output.
2. Database migrations (Alembic) before making production schema changes.
3. A lock file or constraints file with automated dependency updates and supply-
   chain scanning.
4. Self-hosted Noto Sans NKo for consistent shaping and offline use.
5. Streaming or temporary-file ASR processing if upload limits grow beyond the
   current small-payload design.
6. End-to-end browser accessibility tests for RTL, keyboard navigation, recording,
   and all four interface languages.
