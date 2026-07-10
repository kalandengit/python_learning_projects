# Architecture

## Sprint 01 decision

Use a modular Next.js application instead of a premature monorepo. This is faster for MVP delivery and still allows later extraction into packages.

## Request flow

1. User signs up with Supabase Auth.
2. Middleware protects `/dashboard`, `/upload`, and `/documents` through the route group path.
3. User uploads a screenshot to Supabase Storage.
4. AI generation endpoint accepts a public or signed image URL and returns structured JSON.
5. Generated content is edited in TipTap and exported as Markdown.

## Tradeoff

Supabase is chosen over a custom NestJS backend for speed, built-in Auth, RLS, Storage, and PostgreSQL. If enterprise complexity grows, background workers and a dedicated API service can be added later.
