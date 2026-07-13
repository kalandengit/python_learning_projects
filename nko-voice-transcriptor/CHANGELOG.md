# Changelog

## 1.3.0 - 2026-07-13

### Features

- On-screen N'Ko keyboard now includes the combining **tone diacritics**
  (short high/low/rising, long descending/high/low/rising) plus the
  nasalization and double-dot marks. These carry the tone and length that
  Latin ASR cannot supply, so users can complete the orthography by hand on
  the editable output.

### Security

- Login now performs a dummy Argon2 verification for unknown usernames, so
  the failure path takes the same time as a real wrong password (removes the
  timing side-channel for user enumeration). Addresses a 1.2.0 audit finding.
- `scripts/publish-claude-skills.sh` no longer force-pushes by default: it
  prints the resolved remote, requires `CONFIRM_FORCE_PUSH=1`, and uses
  `--force-with-lease`. Addresses the audit's highest operational finding.

### Documentation

- Added the full compiled N'Ko research link sets under `docs/nko-research/`
  for provenance, referenced from `NKO_RESOURCES.md`.

## 1.2.0 - 2026-07-13

### Interface

- Refresh visual hierarchy, responsive behavior, focus states, and RTL-friendly
  workspace sections.
- Add a keyboard-accessible skip link, reduced-motion handling, and sign-out action.

### Security review

- Add a repository-wide security assessment with prioritized open risks.

## 1.1.0 - 2026-07-13

### Security

- Bound multipart audio reads to the configured maximum upload size plus one byte.
- Treat non-numeric JWT subjects as invalid credentials.
- Handle concurrent duplicate registrations without leaking a database error.
- Disable caching on sensitive API routes and add browser isolation, microphone,
  and production HSTS headers.

### Packaging

- Separate test and lint tools into `requirements-dev.txt`.
- Add a curated N'Ko technical and learning resource guide.

### Tests

- Add regression coverage for malformed JWT subjects.

## 1.0.0 - 2026-07-11

- Initial release.
