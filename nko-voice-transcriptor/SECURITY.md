# Security

## Threat model & mitigations

| Threat | Mitigation |
|---|---|
| Credential stuffing / brute force | Argon2id hashing; per-IP rate limits (10/h register, 20/h login); uniform 401 for unknown user vs wrong password (no enumeration) |
| Token theft / forgery | Short-lived HS256 JWT (60 min default), `exp`+`sub` required, type claim checked; secret ≥32 chars enforced at boot; token in `sessionStorage` (cleared on tab close) |
| Malicious uploads | Declared MIME **and** magic-byte sniffing must both pass; 10 MiB size cap; duration cap; audio processed in memory, never written to disk, never executed |
| IDOR on history | Every history read/delete is filtered by the authenticated `user_id`; cross-user access returns 404 |
| XSS | Strict CSP (`default-src 'self'`, no inline/external scripts); all dynamic DOM via `textContent`, never `innerHTML` |
| Clickjacking / MIME sniffing | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` |
| DoS | Global + per-route rate limits; upload caps; lazy model load keeps unauthenticated paths cheap |
| Injection | SQLAlchemy bound parameters everywhere; Pydantic validation on every body (username pattern, password policy, text length) |
| Secrets | Config only via environment; `.env` git-ignored; fail-fast on weak/missing key; no secrets or request bodies in logs |
| Container escape blast radius | Non-root user, slim base image, healthcheck |

## Privacy

* **Audio is not retained.** Uploads are validated, transcribed in memory and
  discarded; only the text results and byte-count metadata are stored.
* Transcriptions are private to the account that created them and deletable
  by the owner.

## Trade-offs / accepted risks

* JWT in `sessionStorage` (vs httpOnly cookie): simpler CORS-free API and no
  CSRF surface, at the cost of XSS-readability — mitigated by the strict CSP
  and no-inline-script discipline. Revisit if third-party JS is ever added.
* No refresh tokens: users re-login after expiry. Add rotation before
  extending token lifetime.
* CORS is off by default (same-origin). Only set `NKO_CORS_ORIGINS` for
  trusted origins, never `*` with credentials.

## Production checklist

- [ ] TLS-terminating reverse proxy (HSTS) in front of the container
- [ ] `NKO_ENVIRONMENT=production` (disables `/api/docs` and the OpenAPI dump)
- [ ] PostgreSQL with least-privilege role; automated backups
- [ ] Rotate `NKO_SECRET_KEY` via a secrets manager (invalidates live tokens)
- [ ] Alembic migrations replacing `create_all`
- [ ] Central log aggregation + alerting on `login_failed` bursts
