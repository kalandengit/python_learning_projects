# DECISION LOG — Kalanfa

ADR-style record of major engineering decisions, evidenced from the code, git
history, and this session's work. `[verified]` = observable in repo;
`[reported]` = executed earlier, not re-run this pass.

---

## ADR-A — Fork Kolibri and rebrand to Kalanfa

- **Decision** — Base the product on Kolibri (Learning Equality) and rename
  `kolibri`→`kalanfa` across the whole codebase (~930 paths, ~3078 text files,
  all cases). `[verified: kalanfa/ package, rebrand commits 427c9d1/5cde1ef]`
- **Motivation** — Kolibri is a mature, offline-first, Django-based learning
  platform used in 220+ countries — exactly the low-connectivity target. Forking
  is faster and more capable than building learning + sync from scratch.
- **Alternatives** — (a) Inspired rebuild on a clean Django base (more control,
  far more work); (b) keep Kolibri name (rejected: product identity is Kalanfa).
- **Trade-offs** — Inherits a large unfamiliar codebase and upstream maintenance
  burden; wholesale rename risks breakage.
- **Consequences** — Must track upstream (gap analysis vs 0.19.4, ADR-008);
  keep MIT `LICENSE` + `ATTRIBUTION.md` + `UPSTREAM_KOLIBRI_*`. `[verified]`

## ADR-B — Tenant boundary = Kolibri Facility

- **Decision** — Model each school as a Kolibri **Facility**; every
  school-management record carries a `facility` FK; API querysets are filtered
  to `request.user.facility`. `[verified: EcoleBaseViewSet, tests]`
- **Motivation** — Facility already provides users, roles, and data isolation in
  Kolibri; reusing it avoids a parallel tenancy system.
- **Alternatives** — Schema-per-tenant (heavier ops); separate tenant table
  (duplicates Facility).
- **Trade-offs** — Shared-schema isolation depends on disciplined query scoping;
  a missed filter would leak data → covered by isolation tests.
- **Consequences** — Onboarding = create a Facility (`createschool` command).
  `[verified]`

## ADR-C — School data in a nested ordinary Django app (`ecole_gestion`)

- **Decision** — Put models/migrations in a nested plain Django app `gestion`
  (label `ecole_gestion`) registered via the plugin's `settings.py`, rather than
  directly in the plugin package. Use an explicit `DossierTuteur` junction model
  instead of `ManyToManyField`. `[verified]`
- **Motivation** — Kolibri assigns plugins a **dotted `app_label`**
  (`kalanfa.plugins.ecole`); Django's relational-field deconstruction does
  `app_label, model = ref.split('.')` and fails with *"too many values to
  unpack"* on migration. `[reported: reproduced during build]`
- **Alternatives** — Force a non-dotted label on the plugin AppConfig (fought
  the framework, still failed); avoid all relations (unworkable).
- **Trade-offs** — Slightly more nesting; a second `settings.py` indirection.
- **Consequences** — Clean migrations (`0001_initial`, 9 models);
  URL namespace is `kalanfa:kalanfa.plugins.ecole`. `[verified]`

## ADR-D — Messaging: Mattermost Team Edition (full ADR at `docs/adr/ADR-006-messagerie.md`)

- **Decision** — Self-hosted **Mattermost Team Edition** for Slack-like
  messaging; one invite-only team per facility; Kalanfa provisions and posts via
  REST v4. `[verified: gestion/messagerie.py, ADR-006]`
- **Motivation** — MIT (matches our license), single Go binary + PostgreSQL,
  ~2 GB RAM ≈ 1000 users (fits a school server), UX closest to Slack.
- **Alternatives** — Zulip (Django like us, but 5 services / more RAM),
  Rocket.Chat (MongoDB, heavier), Matrix/Element (AGPL, federation not needed).
- **Trade-offs** — A second service to operate; separate accounts (no SSO in v1).
- **Consequences** — `provisionmessagerie` command; `docker-compose.yml`; SSO via
  OIDC is a future revision.

## ADR-E — External notification connectors (Slack, WhatsApp)

- **Decision** — Add `SlackConnector` (incoming webhook) and `WhatsAppConnector`
  (Meta Graph v20 Cloud API); announcements fan out to all configured channels.
  `[verified: gestion/connecteurs.py, tests]`
- **Motivation** — Reach staff on existing Slack and, crucially, parents on
  **WhatsApp** — the dominant channel in Bamako.
- **Alternatives** — SMS-only (planned separately via Orange SMS); email
  (unreliable adoption locally).
- **Trade-offs** — WhatsApp requires Meta Business onboarding and pre-approved
  templates outside the 24 h window; verified via mocks only so far.
- **Consequences** — All config via env vars; failures degrade to HTTP 502.

## ADR-F — Configuration & secrets via environment variables

- **Decision** — All external integration config (`KALANFA_MATTERMOST_*`,
  `KALANFA_SLACK_WEBHOOK_URL`, `KALANFA_WHATSAPP_*`) via env; nothing in the
  repo; generated passwords via `secrets`. `[verified]`
- **Motivation** — Secure by default; secrets never enter git history.
- **Consequences** — `est_configure()` guards let features stay dormant until
  configured; `.gitignore` excludes `.env`, `.kalanfa_home`, venv, DB. `[verified]`

## ADR-G — Version pinning for the fork build `[verified]`

- **Decision** — Install with `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_KALANFA=0.1.0`.
- **Motivation** — setuptools-scm derives the version from git tags; the fork has
  none, so `import kalanfa` failed on a missing `_version`.
- **Consequences** — Documented in README/rebuild prompt; deps resolved from the
  `base` dependency-group in `pyproject.toml`.

## ADR-H — Frontend dependency resolution after rebrand `[verified]`

- **Decision** — pnpm catalog aliases `kalanfa-constants`/`kalanfa-design-system`
  → upstream `kolibri-*`; packageExtension injects `browserslist-config-kolibri`;
  pin the `aphrodite` GitHub dependency via `git+https`.
- **Motivation** — Renamed npm names don't exist upstream; KDS internally extends
  a browserslist config; the codeload tarball host is blocked by egress policy.
- **Consequences** — `pnpm build` compiles all 29 bundles clean. `[reported]`
