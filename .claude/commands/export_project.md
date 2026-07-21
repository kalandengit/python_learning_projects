---
description: Export a project folder as a distributable archive (zip and/or tar.gz)
argument-hint: "[project-dir] [zip|tgz|both]"
allowed-tools: Bash(mkdir:*), Bash(tar:*), Bash(zip:*), Bash(ls:*), Bash(du:*), Bash(git:*), Bash(rm:*), Bash(sha256sum:*)
---

Export a project directory into a clean, distributable archive.

## Arguments
- `$1` — project directory to export, relative to the repo root. Optional.
  Default: the whole repository root (`.`).
- `$2` — format: `zip`, `tgz`, or `both`. Optional. Default: `both`.

## Steps

1. Resolve the target directory from `$1` (default: repo root). If it does not
   exist, list the top-level directories and ask which one to export. Do not
   guess.
2. Create an output directory `dist/` at the repo root (`mkdir -p dist`).
3. Build a timestamped base name: `<dirname>-YYYYMMDD-HHMMSS`.
4. Produce the requested archive(s) from the target directory, **excluding**
   noise and anything sensitive:
   - VCS/build: `.git`, `dist`, `build`, `*.egg-info`
   - Python: `__pycache__`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache`,
     `*.pyc`, `.venv`, `venv`
   - JS: `node_modules`
   - Local data/secrets: `.env`, `*.db`, `*.sqlite*`, `*.log`
   - OS cruft: `.DS_Store`
   Suggested commands (run from the repo root, adjust `TARGET`/`BASE`):
   - tar.gz: `tar --exclude-vcs --exclude='__pycache__' --exclude='*.pyc' \
     --exclude='.venv' --exclude='venv' --exclude='node_modules' \
     --exclude='.pytest_cache' --exclude='.ruff_cache' --exclude='.mypy_cache' \
     --exclude='dist' --exclude='*.db' --exclude='*.sqlite*' --exclude='.env' \
     --exclude='*.log' --exclude='.DS_Store' \
     -czf "dist/BASE.tar.gz" -C "<parent-of-target>" "<target-name>"`
   - zip: `cd "<parent-of-target>" && zip -r "<repo>/dist/BASE.zip" \
     "<target-name>" -x '*/.git/*' '*/__pycache__/*' '*.pyc' '*/.venv/*' \
     '*/venv/*' '*/node_modules/*' '*/.pytest_cache/*' '*/.ruff_cache/*' \
     '*/dist/*' '*.db' '*.sqlite*' '*.env' '*.log' '*.DS_Store'`
5. Verify: list the archive(s) with size (`ls -lh dist/`), print a
   `sha256sum` of each, and confirm the archive does NOT contain `.env`,
   `*.db`, or `.git` (e.g. `tar -tzf` / `unzip -l` piped through a check).
6. Report the archive path(s) and size(s), then **offer to send the file(s)**
   to the user with the SendUserFile tool (display: attach). Do not send
   without confirming unless the user already asked to receive it.

## Notes
- Never include `.env`, database files, or credentials in the archive — if the
  verification in step 5 finds any, delete the archive and rebuild with the
  exclusion fixed.
- Keep archives out of version control (they live in `dist/`, which the
  exclusions and `.gitignore` should ignore). If `dist/` is not gitignored at
  the repo root, add it.
