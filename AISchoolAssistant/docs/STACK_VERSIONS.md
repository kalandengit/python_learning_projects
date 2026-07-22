# Stack Versions & Upgrade Notes

Current stable versions for the AI School Assistant platform, verified against
the npm registry / official sources on **2026-07-21**. "Chosen" is what this
repo pins; where it differs from "Latest", the reason is given.

## Toolchain (workspace root — applied)

| Tool | Latest | Chosen | Notes |
| --- | --- | --- | --- |
| Node.js | 26 (Current), **24 LTS** | `>=22` engine, target **24 LTS** | Sandbox runs 22 (maintenance LTS); engine allows 22 & 24. Target Node 24 LTS in CI/prod. |
| pnpm | 11.15.1 | **11.15.1** | Pinned via `packageManager`. (v12 Rust port exists via self-update; not adopted yet.) |
| Turborepo | 2.10.5 | **^2.10.5** | Upgraded from 2.3. |
| TypeScript | **7.0.2** | **^5.9.3** | ⚠️ TS 7 (native port) **not adopted**: `@typescript-eslint/parser@8.65` peer is `typescript >=4.8.4 <6.1.0` — TS 7 would break ESLint (a §16-mandatory tool). 5.9.3 is the latest toolchain-compatible line. TS 7 migration tracked as future work (blocked on `@typescript-eslint` support). |
| Prettier | 3.9.6 | **^3.9.6** | Upgraded from 3.4. |
| @typescript-eslint | 8.65.0 | **^8.65.0** | Bounds the TypeScript decision above. |

## Frameworks (to be applied in later work packages)

| Component | Latest stable | Planned | Notes |
| --- | --- | --- | --- |
| NestJS | 11.1.28 | **11.x** | v12 (ESM, Standard Schema) is upcoming Q3 2026 — adopt after GA. |
| Next.js | 16.2.11 | **16.x** | Turbopack default, React 19.2. For the web app (WP‑5). |
| React | 19.2 | **19.x** | Bundled with Next 16. |
| Flutter/Dart | current stable channel | stable | Mobile (later WP); pinned at build time. |

## Infrastructure images (pinned when `docker-compose.dev.yml` is authored)

To be pinned to explicit, current stable tags at WP‑0 infra step (not `latest`):
PostgreSQL 17, Redis 7.4, Keycloak 26, Qdrant 1.x, OpenSearch 2.x, NATS 2.x
(JetStream), Temporal 1.x, MinIO (current). Exact patch tags are verified and
pinned in the compose file and Helm charts when authored.

## Policy

- Pin to the **latest stable that the whole toolchain supports** — never adopt a
  major (e.g. TS 7) that breaks a mandatory tool (§16, §21 "never break modules").
- Renovate/Dependabot proposes upgrades; majors land via a dedicated ADR.
- Re-verify this table at the start of each work package.

## Sources
- [turbo (npm)](https://www.npmjs.com/package/turbo) · [pnpm releases](https://github.com/pnpm/pnpm/releases)
- [TypeScript releases](https://github.com/microsoft/typescript/releases) · [TS 7.0 RC announcement](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0-rc/)
- [@nestjs/core (npm)](https://www.npmjs.com/package/@nestjs/core) · [NestJS 12 roadmap](https://www.infoq.com/news/2026/04/nestjs-12-roadmap-esm/)
- [Next.js blog](https://nextjs.org/blog) · [Node.js releases](https://github.com/nodejs/Release)
