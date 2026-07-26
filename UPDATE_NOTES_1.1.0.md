# Update notes — 1.1.0

Release date: 2026-07-13

## What changed

- Bounded audio-upload reads to prevent oversized requests from being fully
  buffered in application memory.
- Hardened JWT validation for malformed `sub` claims.
- Made duplicate registration race-safe and strengthened sensitive-response
  browser headers.
- Split runtime and development dependencies.
- Updated CI to current Node 24-based GitHub action majors and corrected CI to
  install the new development requirements file.
- Added regression coverage, a changelog, and useful root project documentation.
- Consolidated the supplied N'Ko research into a curated standards and learning
  guide, while clearly documenting the transliterator's tone limitation.

## Validation

- All Python application and test files compile and parse successfully.
- Full unit tests and Ruff linting require installation from
  `requirements-dev.txt`; those packages were not available in the build
  environment used to assemble this archive.

## Upgrade

Development environments should now install:

```bash
python -m pip install -r nko-voice-transcriptor/requirements-dev.txt
```

Production and Docker builds continue to use `requirements.txt`.
