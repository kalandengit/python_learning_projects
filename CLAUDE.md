# CLAUDE.md — Event Management System (EMS)

## Source of truth

Read **[docs/master-prompt-v3.md](docs/master-prompt-v3.md)** before doing anything else.
It is the authoritative, self-contained project brief: locked technical decisions (§2),
domain model (§3), API surface (§4), remaining work plan (§6), and non-negotiable
rules (§7). All decisions in its §2 are LOCKED — do not re-litigate or "improve"
them unless the user explicitly asks.

## Repository status (as of July 2026)

The master prompt's §5 lists Parts 1–3 (schema, backend core, routes/tests) and the
v3.0 Modernization Pack as completed, but **that code is not yet present in this
repository** — it was produced in earlier sessions and has not been committed here.
Before executing any remaining-work part (§6), check what actually exists in the
tree; if a prerequisite from §5 is missing, surface that to the user rather than
silently regenerating it.

## Quick rules (see master prompt §7 for the full list)

- Python ≥3.13 with **uv** (pyproject.toml + uv.lock) — never pip/requirements.txt.
- Security > convenience: no card data, no secrets/tokens/PII in logs or commits.
- Concurrency invariants (ticket inventory `FOR UPDATE`, atomic scan `UPDATE … RETURNING`) must never be simplified.
- Terraform is plan-only in automation; a human applies.
- CI gates: coverage ≥80%, Trivy CRITICAL blocks, mypy strict, ruff clean.
