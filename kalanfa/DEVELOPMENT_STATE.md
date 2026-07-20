# DEVELOPMENT STATE — Kalanfa

"Where we are and what's next" handoff. Snapshot at commit `2a2ab1d`, branch
`claude/school-management-clone-uicab0`. Labels: `[verified]` this pass,
`[reported]` executed earlier in history (not re-run here).

---

## Completed

- **Fork & rebrand** — Kolibri vendored and renamed to Kalanfa; MIT `LICENSE` +
  `ATTRIBUTION.md` + `UPSTREAM_KOLIBRI_*` preserved. `[verified: tree]`
- **Boot** — `pip install -e .` works (with SETUPTOOLS_SCM pretend version);
  `pnpm build` → 29 bundles, 0 errors; `migrate` OK; server serves French
  sign-in at `/fr-fr/auth/` (HTTP 200). `[reported]`
- **Multi-tenant SaaS** — Facility = tenant; `createschool` onboarding command;
  pilot facility **École MOUMA** provisioned (formal preset, fr-fr). `[reported]`
- **Plugin `ecole`** — nested `ecole_gestion` app; 9 models; migration
  `0001_initial` applied; DRF API at `/ecole/api/` with facility scoping,
  role gating, and actions `bulletin` / `impayes` / `progression`. `[verified: code]`
- **Messaging** — Mattermost integration (`messagerie.py`, `provisionmessagerie`
  command, compose file); Slack + WhatsApp connectors (`connecteurs.py`);
  announcement fan-out + WhatsApp endpoints; `ADR-006`. `[verified: code]`
- **Tests** — 29 passing (isolation, roles, bulletin math, messaging, connectors),
  external APIs mocked. `[reported]`
- **Docs** — `MASTER_PROMPT.{md,json}` v2.2.0; this knowledge package.

## Remaining work

| Priority | Item |
|---|---|
| P0 | Reproducible audit report; **gap analysis vs Kolibri 0.19.4** (fork is off `develop`, ahead of 0.19.4) |
| P1 | Import real École MOUMA documents (5 Drive folders) + transcribe 4 Montessori videos; build source→field→model→screen→export matrix before freezing schema |
| P2 | Richer academic model (AnneeScolaire/Classe/Matiere/InscriptionAnnuelle, Evaluation/Bareme, GrilleBulletin/VersionBulletin); **PDF bulletins & reçus** (WeasyPrint); audit log |
| P3 | **Vue UI** for school modules (currently API-only); **parent portal** (spec'd in MASTER_PROMPT §7, `/ecole/api/parents/*`) |
| P4 | **Orange Money** payments + reconciliation; **Orange SMS**; live Mattermost/Slack/WhatsApp against real services; pilot deployment |

## Known bugs / risks / unknowns

- **Telemetry** — upstream `telemetry.learningequality.org` pingback still fires;
  must be neutralized in production. `[verified: boot logs]`
- **Integrations mock-only** — Mattermost/Slack/WhatsApp verified via mocks, never
  against live endpoints; WhatsApp needs Meta Business onboarding + approved
  templates. `[verified]`
- **School data not synced** — `ecole` models are plain Django (not morango);
  offline sync of school-management data is not wired yet. `[verified]`
- **No SSO** — Kalanfa and Mattermost accounts are separate in v1. `[verified]`
- **Ops** — `createschool`/`provisionmessagerie` print initial passwords to
  stdout; no CI for the fork; vendored built assets bloat the tree. `[verified]`
- **Unknown until documents arrive** — exact bulletin layout, fiche fields,
  Montessori referential, fiches de poste content. Do **not** freeze the schema
  first. `[verified: MASTER_PROMPT source_materials = source_to_import]`
- **Legal** — Mali data-protection law n°2013-015 review pending for student/
  family/health data. `[reported: externally_verified in MASTER_PROMPT]`

## Technical debt

- Fork divergence from upstream undocumented → write ADR-008 + gap report.
- Large vendored frontend/dist assets → revisit build pipeline.
- Add CI (lint + `ecole` test suite) for the fork.

## How to resume (fast path)

```bash
cd kalanfa
python -m venv .venv && . .venv/bin/activate
SETUPTOOLS_SCM_PRETEND_VERSION_FOR_KALANFA=0.1.0 \
  pip install -e . --no-deps   # + base deps from pyproject
export KALANFA_HOME=$PWD/.kalanfa_home
kalanfa plugin enable kalanfa.plugins.ecole
kalanfa manage migrate
KALANFA_PLUGIN_APPLY=kalanfa.plugins.ecole \
  python -m pytest kalanfa/plugins/ecole/gestion/test/   # expect green
kalanfa start --foreground --port 8000                    # French UI at /fr-fr/auth/
```

Then pick up at **P0** (audit) or jump to the highest-value build item:
**PDF bulletins** or the **parent portal** (both well-specified).
