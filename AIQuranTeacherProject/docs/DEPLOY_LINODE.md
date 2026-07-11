# Deploy a test version to a Linode VPS

This deploys the whole stack — **Postgres + backend API + signaling server +
Caddy reverse proxy** — to a single Linode VPS with Docker Compose. Caddy
serves plain HTTP on the VPS IP for a quick test, or automatic HTTPS if you
point a domain at it.

> Scope: a runnable **test** deployment. `DB_SYNCHRONIZE=true` auto-creates the
> schema (no migrations yet), and secrets live in a `.env` file. See the
> production hardening notes at the end before going live.

## 0. Prerequisites
- A Linode account.
- (Optional, for HTTPS) a domain you can point at the server.

## 1. Create the Linode
- **Distribution:** Ubuntu 24.04 LTS
- **Plan:** Shared CPU, **Nanode 1 GB works for a light test; 2 GB recommended**
  (the backend image builds faster and Postgres is happier).
- **Region:** closest to your users.
- Add your SSH key, then **Create**. Note the public **IP**.

## 2. Provision the server
SSH in and install Docker + firewall:

```bash
ssh root@YOUR_VPS_IP

# Get the code (either clone, or scp it up):
apt-get update -y && apt-get install -y git
git clone https://github.com/kalandengit/python_learning_projects.git
cd python_learning_projects/AIQuranTeacherProject

# One-time provisioning (Docker, Compose, UFW firewall):
bash deploy/setup.sh
```

## 3. Configure secrets
```bash
cp deploy/.env.example .env
nano .env
```
Set at least:
- `POSTGRES_PASSWORD` — `openssl rand -base64 24`
- `JWT_SECRET` — `openssl rand -base64 48`
- `PUBLIC_URL` — `http://YOUR_VPS_IP` (used for CORS)
- `MISTRAL_API_KEY` — optional; AI endpoints return 503 until set.

**For HTTPS with a domain:** point an A record at the VPS IP, then set
`SITE_ADDRESS=api.yourdomain.com`, `PUBLIC_URL=https://api.yourdomain.com`, and
`ACME_EMAIL=you@example.com`. Caddy fetches a Let's Encrypt certificate
automatically on first start.

## 4. Launch
```bash
docker compose up -d --build
docker compose ps          # all services should be "running"/"healthy"
docker compose logs -f backend
```

## 5. Verify
```bash
# From the server or your laptop (swap in your IP/domain):
curl http://YOUR_VPS_IP/api/health
curl http://YOUR_VPS_IP/api/quran/surahs

# Register a user and call a protected route:
TOKEN=$(curl -s http://YOUR_VPS_IP/api/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"you@example.com","displayName":"You","password":"StrongPass123"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["accessToken"])')
curl http://YOUR_VPS_IP/api/gamification/me -H "Authorization: Bearer $TOKEN"
```
Swagger docs are disabled in production by design.

## 6. Operate
```bash
docker compose logs -f              # tail all logs
docker compose restart backend      # restart one service
git pull && docker compose up -d --build   # deploy an update
docker compose down                 # stop (keeps volumes/data)
```

## Stripe webhooks (if using billing)
Create a webhook in the Stripe dashboard pointing at
`https://YOUR_DOMAIN/api/billing/webhook`, put its signing secret in
`STRIPE_WEBHOOK_SECRET`, set the price IDs, and `docker compose up -d`.
(Requires HTTPS — use a domain, not the bare IP.)

## Architecture on the box
```
Internet ─▶ Caddy :80/:443 ─┬─ /api/*        ─▶ backend:3000 ─▶ db:5432
                            └─ /socket.io/*  ─▶ signaling:3001
```
Only Caddy is exposed publicly; the app and database sit on an internal Docker
network.

## Before production (beyond this test)
- Replace `DB_SYNCHRONIZE=true` with **TypeORM migrations**.
- Move secrets out of `.env` into a secrets manager; rotate the `JWT_SECRET`.
- Use a **domain + HTTPS** (set `SITE_ADDRESS`), and restrict `CORS_ORIGINS`.
- Add off-host **Postgres backups** (e.g. `pg_dump` to object storage) and
  monitoring/alerting.
- Run `docker compose` behind an unprivileged user and enable automatic
  security updates (`unattended-upgrades`).
