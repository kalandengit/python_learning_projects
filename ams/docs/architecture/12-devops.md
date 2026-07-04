# Section 12 — DevOps Architecture

Concrete artefacts in this repo:

| Artefact | Location |
|---|---|
| CI pipeline (build, test, SAST, secret scan, container scan, SBOM, push) | `.github/workflows/ci.yaml` (repo root) |
| CD pipeline (Helm deploy, env promotion, prod gate) | `.github/workflows/cd.yaml` |
| Terraform modules (AKS, PostgreSQL, Redis) + prod composition | `ams/infra/terraform/` |
| Helm chart for a .NET service | `ams/deploy/helm/badge-service/` |

## 12.1 CI (see `.github/workflows/ci.yaml`)

Stages per PR/merge: restore+build (.NET 10, warnings-as-errors) → unit + architecture
tests with coverage gate → **Gitleaks** secret scan (the NFR-012 pipeline gate) →
**CodeQL** SAST → container build (multi-stage, distroless-style runtime, non-root) →
**Trivy** image scan (fail on HIGH/CRITICAL) → **SBOM** (Syft, SPDX) attached as artifact
→ push to ACR with immutable tag `sha-<git-sha>` → **cosign** keyless signing.

## 12.2 CD & environment promotion (see `.github/workflows/cd.yaml`)

`dev → test → uat → prod`. Dev/test auto-promote on green; UAT on QA approval; **prod
requires a manual environment gate** (GitHub environment protection, 2 reviewers, business
hours). The CD job does not `kubectl apply` — it opens a PR against the `ams-gitops` repo
bumping the image tag in the target env's values file; ArgoCD reconciles (ADR-012).

## 12.3 GitOps repository structure (ArgoCD)

```
ams-gitops/
├── bootstrap/app-of-apps.yaml          # ArgoCD Application generating all others
├── clusters/
│   ├── weu-prod/  neu-prod/  weu-uat/  weu-test/  weu-dev/
│   │   └── apps/<service>.yaml         # Application: chart ref + values + target revision
└── envs/
    ├── dev/ test/ uat/ prod/
    │   └── <service>/values.yaml       # image.tag bumped by CD PRs
```

Reconciliation: automated sync with prune + self-heal in dev/test; prod is
`syncPolicy: manual` behind the same 2-reviewer PR gate — drift is *detected* everywhere,
auto-corrected below prod, human-approved in prod. Rollback = `git revert` of the tag-bump
PR (audit trail preserved).

## 12.4 Deployment strategies

- **Canary (default, Flagger):** steps 5 % → 20 % → 50 % → 100 %, 2-min analysis
  intervals. Gate metrics: request success rate ≥ 99.5 % and P95 latency ≤ SLO threshold
  (per-service, e.g. 200 ms for access-control) from the service's OTel/Prometheus
  metrics. **Auto-rollback trigger:** either metric failing 2 consecutive intervals →
  Flagger aborts, routes 100 % to primary, marks release failed, pages the owning team.
- **Blue/Green (schema-sensitive releases):** parallel stack + expand-and-contract DB
  migrations (new columns nullable first; contract only after full rollout); switch at the
  service mesh; blue kept warm 24 h for instant rollback.
- **Rollback procedure (runbook):** (1) Flagger auto-abort or `git revert` tag PR →
  ArgoCD converges ≤ 2 min; (2) DB: migrations are always backward-compatible one version
  (expand/contract), so no down-migration on rollback; (3) events: consumers tolerate one
  schema version back (ADR-014); (4) verify via canary dashboard + synthetic probes;
  (5) incident note auto-created with the diff link.

## 12.5 DORA targets

| Metric | Target (month 12) | Measured from |
|---|---|---|
| Deployment frequency | ≥ daily per service (on demand) | ArgoCD sync history |
| Lead time for change | < 1 day merge → prod (P75) | GitHub merge → ArgoCD healthy |
| Change failure rate | < 10 % | Flagger aborts + incident-linked deploys / total |
| MTTR | < 1 h (P75) | incident open → resolved (PagerDuty/ServiceNow export) |

## 12.6 Supply-chain controls (Zero Trust for the pipeline)

- OIDC federation GitHub↔Azure — no long-lived cloud credentials in CI (NFR-012).
- Branch protection: required checks (build, tests, Gitleaks, CodeQL, Trivy), signed
  commits, no direct pushes to `main`.
- Images signed (cosign) and verified by AKS admission policy; SBOM retained 7 years with
  release evidence (compliance mapping row 11).
- Terraform: `plan` on PR with cost diff (Infracost) and policy checks (tfsec/Checkov);
  `apply` from CI only, remote state locked, prod workspace behind the same manual gate.

<!-- SECTION 12 COMPLETE -->
