# ADR-0001: Turborepo monorepo + golden service template

- **Status:** Accepted
- **Date:** 2026-07-22
- **Context:** WP-0 (Platform Foundation)

## Decision
Use a **Turborepo + pnpm** monorepo. All backend services are generated from a
single **golden NestJS service template** and depend on shared packages
(`@asa/config`, `@asa/logger`, `@asa/errors`, `@asa/contracts`). Cross-cutting
concerns (health/live/ready, OpenAPI, `/metrics`, structured logging, config
validation, the problem+json error model, pagination) live in the template and
shared packages — never re-implemented per service.

## Motivation
- One toolchain, one lint/format/test config, atomic cross-package changes.
- Enforces §5 (no duplication, DI, interfaces) and §21 (never break modules):
  a fix in a shared package propagates to every service.
- API-first consistency (§8): every service exposes the same operational surface.

## Alternatives considered
- **Polyrepo per service** — rejected: duplication, drift, hard cross-cutting changes.
- **Nx** — viable; Turborepo chosen for simplicity and the team's stack familiarity.

## Trade-offs
- Monorepo needs disciplined boundaries (package ownership, `exports` maps) and
  good caching (Turborepo remote cache) to stay fast.

## Consequences
- New service = copy the template, wire its bounded context. Nothing operational
  is written from scratch.
- Shared packages are versioned within the workspace (`workspace:*`).
