# CI/CD Guide

## Local quality gate
Run before every pull request:

```bash
npm run ci
npm run build
npm run test:e2e
```

## GitHub Actions
The main CI workflow runs:

1. Install dependencies with `npm ci`.
2. Lint.
3. Typecheck.
4. Unit tests.
5. Security header check.
6. Dependency audit.
7. Production build.
8. Playwright smoke tests.

## Required GitHub secrets

```bash
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
OPENAI_API_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
```

## Deployment model
Recommended flow:

1. Pull request creates preview deployment on Vercel.
2. GitHub Actions validates code.
3. Supabase migrations are reviewed and applied to staging.
4. Product owner approves preview.
5. Merge to `main` deploys production.
6. Production smoke tests run manually or from a protected workflow.

## Notes
- Do not run destructive database migrations automatically against production until rollback strategy is mature.
- Keep Supabase staging and production projects separate.
- Store service-role keys only in secure server/CI environments.
