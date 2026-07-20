# PROJECT REBUILD PROMPT — Kalanfa

> A directly reusable Master Prompt. Give this to a capable LLM (or team) to
> rebuild Kalanfa from scratch with high fidelity, even if the repo, git
> history, and conversations are lost. Pairs with `PROJECT_CONTEXT.json`
> (structured facts) and `MASTER_PROMPT.md` (business/product vision).

---

You are a founding engineering team — senior Django/Vue architect + security
lead + francophone EdTech product lead. Build **Kalanfa**, a multi-tenant,
**offline-first** school-management + digital-learning **SaaS** for francophone
West-African private schools. Work in **French** for all domain-facing content.
Method: **planning-first** (analyze → numbered plan → explicit decisions for
risky/irreversible changes → incremental implementation → **reproducible
verification**: migrations + tests + real HTTP boot). Secure by default,
French-first, offline-first. Never present a guess as verified fact.

## Context & origin

- Pilot customer: **École MOUMA**, Bamako, Mali (cycles Montessori/maternelle +
  Collège), 2026. Locale: French, currency XOF (FCFA), timezone `Africa/Bamako`.
- Base the platform on **Kolibri** (Learning Equality, MIT) — an offline-first
  Django learning platform — and **rebrand it to Kalanfa**. Preserve the MIT
  `LICENSE` and add attribution (this is legally required; keep upstream
  copyright). Compare against **Kolibri 0.19.4** as the baseline.

## Goals

1. Reuse Kolibri's learning platform (content channels, lessons, quizzes, coach
   dashboards, attendance, morango sync, auth/RBAC) rebranded as Kalanfa.
2. Add francophone **school-management** modules as a Kalanfa plugin.
3. Make it a **multi-tenant SaaS**: one school = one tenant, strict isolation.
4. Add **messaging** (self-hosted Mattermost) with **Slack** and **WhatsApp**
   connectors for announcements and parent reminders.

## Stack (match this)

- Backend: **Django 3.2 + Django REST Framework + morango**; DB SQLite (dev) →
  PostgreSQL (prod). Frontend: **Vue 2** pnpm monorepo (Kolibri’s), Kolibri
  Design System. Python package name `kalanfa`; CLI `kalanfa`.

## Build order (milestones — verify each before moving on)

**M-A. Fork & rebrand.** Vendor Kolibri source; rename `kolibri`→`kalanfa`
across ~930 paths and ~3078 text files (all cases). Keep `LICENSE`,
`ATTRIBUTION.md`, and reference copies of upstream agent files. Retire the old
scaffold.

**M-B/C. Make it boot.** Fix the known pitfalls (see below). Verify: `pip
install -e .` works, `pnpm build` compiles all frontend bundles, `kalanfa manage
migrate` runs, and `kalanfa start` serves the French sign-in page (HTTP 200 at
`/fr-fr/auth/`). Provision the pilot: `kalanfa manage provisiondevice --facility
"École MOUMA" --preset formal --language_id fr-fr`.

**M-D. Multi-tenant SaaS.** Tenant = Kolibri **Facility**. Add
`kalanfa manage createschool --nom … --admin … --motdepasse … --preset formal`
to onboard a school (Facility + preset + school admin, in a transaction).

**M-E. School plugin `kalanfa.plugins.ecole`.** Because Kolibri gives plugins a
**dotted `app_label`** that breaks relational migrations, put the data layer in
a **nested ordinary Django app** `gestion` (label `ecole_gestion`), registered
via the plugin’s `settings.py` (`INSTALLED_APPS = [".gestion.apps.GestionConfig"]`).
Use an **explicit junction model** instead of `ManyToManyField`.

Models (UUID pk; base `EtablissementScopedModel` adds `facility` FK +
timestamps): `DossierEleve` (fiche de renseignement: état civil, sexe,
naissance, nationalité, adresse; santé: groupe sanguin, allergies, contact
d'urgence; scolarité antérieure + documents; boursier/réduction%), `Tuteur`,
`DossierTuteur` (junction, `unique_together`), `Periode` (annee_scolaire + nom
+ ordre), `Note` (valeur 0–20, coefficient, matiere, appreciation), `EcheanceFrais`
(montant_du FCFA int; `solde`/`montant_paye` computed), `Paiement` (montant,
mode, reference_recu), `ObservationMontessori` (domaine∈{Vie pratique, Sensoriel,
Langage, Mathématiques, Culture}; niveau∈{Présenté, En cours, Acquis, Maîtrisé}),
`FichePoste`.

DRF API at `/ecole/api/` (namespace `kalanfa:kalanfa.plugins.ecole`). Base
viewset `EcoleBaseViewSet`: filter queryset to `request.user.facility`;
`perform_create` force-assigns that facility. Permission `EstMembreEtablissement`:
authenticated facility members read; only admin/coach of the facility (or device
superuser) write. Endpoints: `dossiers`, `tuteurs`, `periodes`, `notes` (+ action
`bulletin/?eleve=&periode=` → moyenne pondérée `Σ(note·coef)/Σcoef`, rang across
the facility, effectif), `frais` (+ `impayes/`), `paiements`, `observations`
(+ `progression/?enfant=`), `fiches-poste`.

**M-F. Messaging & connectors** (see `docs/adr/ADR-006-messagerie.md` to record
the decision). Choose **Mattermost Team Edition** (MIT, single binary +
PostgreSQL, ~2 GB RAM/1000 users — fits a school server) over Zulip
(Django but 5 services), Rocket.Chat, Matrix.
- `gestion/messagerie.py`: minimal Mattermost REST v4 client; **one invite-only
  team per facility**; default channels `annonces`(open)/`enseignants`/`direction`;
  idempotent user provisioning. Command `provisionmessagerie --etablissement`.
  Compose file `deployment/messagerie/docker-compose.yml` (French default).
- `gestion/connecteurs.py`: `SlackConnector` (incoming webhook) and
  `WhatsAppConnector` (Meta Graph v20 Cloud API: free text in 24 h window, else
  pre-approved template; normalize Malian numbers).
- API (staff-only): `POST /ecole/api/messagerie/annonce/` fans out to every
  configured channel (Mattermost + Slack); `POST /ecole/api/messagerie/whatsapp/`.
- All config via env: `KALANFA_MATTERMOST_URL/TOKEN`, `KALANFA_SLACK_WEBHOOK_URL`,
  `KALANFA_WHATSAPP_TOKEN/PHONE_ID`. No secrets in repo.

## Known pitfalls (apply the fixes)

1. **Version**: setuptools-scm needs a git tag → install with
   `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_KALANFA=0.1.0 pip install -e . --no-deps`;
   deps come from `pyproject.toml` `base` dependency-group.
2. **npm names**: `kalanfa-constants`/`kalanfa-design-system` don’t exist on npm →
   pnpm catalog alias to upstream `kolibri-*`; add a packageExtension injecting
   `browserslist-config-kolibri` into `kolibri-design-system`.
3. **Frontend build** shells out to `python` for plugin discovery → run
   `pnpm build` with the venv active.
4. **Dotted plugin app_label** breaks relational migrations → nested plain app
   (see M-E); explicit junction model, not `ManyToManyField`.
5. **Usernames**: letters/digits/underscores only.
6. A GitHub-tarball npm dependency (aphrodite) may be blocked by egress policy →
   use a `git+https` reference.

## Security

Session auth + RBAC per role and per facility; staff-only writes; DRF validation;
secrets via env; onboarding passwords ≥ 8 chars; external-service failures →
HTTP 502 with clean (secret-free) messages. **Neutralize upstream telemetry**
(`telemetry.learningequality.org`) in production. Add append-only audit for
payments/grades/permissions; encrypted 3-2-1 backups with tested restore;
data-protection review under Mali law n°2013-015 for student/family/health data.

## Testing

Django/pytest with external APIs mocked; `APITestCase` with `databases='__all__'`;
`provision_device()` in setup. Cover: tenant isolation (cross-facility 404/empty),
role gating (403), bulletin math (e.g. Maths 15×coef3 + Français 12×coef2 →
13.8/20, rang 2), messaging idempotence/slugs/config, connector payloads and
number normalization, endpoint access. Target: full green suite before shipping.

## Deliverables & house rules

Keep `MASTER_PROMPT.{md,json}` (business/product) and this knowledge package in
sync. Small explicit commits; never commit secrets/DB/venv/node_modules. Record
durable divergences from upstream as ADRs. Do not freeze the school data schema
until the real École MOUMA documents (Drive folders + Montessori videos) are
imported and validated with the school.
