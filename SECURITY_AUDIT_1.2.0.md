# Security audit — version 1.2.0

Date: 2026-07-13

## Executive summary

No embedded production secrets, obvious SQL injection, DOM HTML injection, path
traversal, or cross-user history access was found. Existing controls are sound
for a small deployment: Argon2id passwords, short-lived JWTs, ownership-scoped
queries, bounded application reads, restrictive CSP, non-root containers, and
production-disabled API docs.

The release is not yet hardened for an internet-facing, high-availability
deployment. The largest risks are supply-chain reproducibility, proxy-aware rate
limiting, multipart request enforcement before route handling, mutable ML model
artifacts, and an intentionally destructive publishing helper.

## Findings

| Severity | Finding | Evidence and impact | Recommendation |
| --- | --- | --- | --- |
| High (operational) | Publishing helper force-pushes `main` | `scripts/publish-claude-skills.sh` accepts a remote argument and executes `git push --force origin main`. A typo can overwrite the wrong repository branch. | Require an explicit `CONFIRM_FORCE_PUSH=1`, display and verify the normalized remote, prefer `--force-with-lease`, and document branch protection. |
| Medium | Dependencies and images are not reproducible | Python packages use lower bounds without a lock/hash file; Docker base and PostgreSQL tags are mutable. A later build can resolve different code. | Generate reviewed constraints with hashes, pin container image digests, and add automated dependency/image scanning. |
| Medium | Rate limiting is not proxy-aware by design | SlowAPI keys on the direct peer address. Behind a reverse proxy, users may share one limit; careless forwarded-header trust can allow spoofing. | Define the trusted proxy topology explicitly and test the effective client-IP key. Never trust forwarded headers from arbitrary peers. |
| Medium | Upload limit applies after multipart parsing begins | The endpoint reads only `limit + 1`, but the ASGI multipart layer has already accepted/spooled the request. Large bodies can still consume bandwidth, parser work, or temporary storage. | Enforce body size at the TLS reverse proxy and add an ASGI receive-layer limit if the app is exposed directly. |
| Medium | MMS model revision is mutable | `NKO_MMS_MODEL_ID` selects a remote model without a pinned revision or artifact checksum. Model downloads expand the supply-chain boundary. | Pin an approved model revision, prefer safetensors, prefetch during a controlled image build, and run offline in production. |
| Low | Login behavior is response-uniform but not timing-uniform | Unknown users skip Argon2 verification and can respond faster than incorrect passwords for real users. | Verify against a precomputed dummy Argon2 hash when the username is absent. |
| Low | CSP permits inline styles | `style-src 'unsafe-inline'` weakens style injection resistance even though scripts remain restricted. | Remove it after confirming no required inline style attributes, or use a nonce/hash strategy. |
| Low | Health endpoint exposes version and ASR engine | This assists fingerprinting, though it contains no credentials or user data. | Keep a minimal liveness endpoint externally and expose detailed readiness only to internal monitoring. |

## Positive checks

- No private keys, GitHub tokens, or AWS access-key patterns were detected.
- SQL access uses SQLAlchemy expressions and bound values.
- Dynamic browser content uses `textContent`/form values rather than HTML sinks.
- JWT decoding restricts the algorithm and requires expiration and subject claims.
- Uploaded audio is not persisted by application code.
- History reads and mutations enforce user ownership.
- CORS is disabled by default and configured through an explicit allowlist.
- The runtime container uses a non-root account.
- GitHub Actions jobs request read-only repository contents.

## Verification limits

This was a source/configuration review plus targeted secret and dangerous-pattern
scanning. No deploy-time penetration test, container daemon scan, software bill
of materials, live proxy test, or installed-package CVE scan was possible in the
available environment. Because dependencies are not locked, a definitive CVE
statement requires the exact resolved production environment.
