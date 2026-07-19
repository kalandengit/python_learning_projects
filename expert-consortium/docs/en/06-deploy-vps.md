# 6 — Deploying to a cloud server (English)

Goal: your assistant available 24/7 from anywhere — web page **and** Telegram — on a small
rented server (VPS) at €5–9/month. Time: ~45 minutes.

## Step 1 — Rent a VPS

Recommended: **Hetzner** (hetzner.com/cloud, CX22: 2 vCPU / 4 GB / ~€5) or
**DigitalOcean** (basic droplet 2 GB / ~$12). During creation choose:

- Image: **Ubuntu 24.04 LTS**
- Authentication: **SSH key** if proposed (more secure) — otherwise a strong root password
- Note the server's **IP address** (e.g. `203.0.113.50`)

## Step 2 — Connect and secure the server

```bash
ssh root@203.0.113.50
```

Then, on the server, create a normal user and a firewall:

```bash
adduser kalan                     # choose a strong password
usermod -aG sudo kalan
ufw allow OpenSSH && ufw allow 80 && ufw allow 443 && ufw enable
```

Log out (`exit`) and reconnect as the new user: `ssh kalan@203.0.113.50`.

## Step 3 — Install Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
exit    # then reconnect so the docker group applies
```

## Step 4 — Install the project

```bash
git clone https://github.com/kalandengit/python_learning_projects.git
cd python_learning_projects/expert-consortium
cp .env.example .env
nano .env      # fill MISTRAL_API_KEY, WEB_PASSWORD, TELEGRAM_* (Ctrl+O to save, Ctrl+X to quit)
```

## Step 5 — Start everything

```bash
docker compose up -d --build
```

First build takes a few minutes. Check: `docker compose ps` — `web`, `bot`, and `qdrant`
should be "running". Your assistant is now at `http://203.0.113.50:8000` and your Telegram
bot is online.

Re-index your documents on the server (copy them into `uploads/` first, e.g. with
`scp -r ./uploads kalan@203.0.113.50:~/python_learning_projects/expert-consortium/`):

```bash
docker compose exec web python -m app.cli ingest
```

## Step 6 (recommended) — Real HTTPS with your own domain

1. Buy a domain (~€10/year) and add a DNS **A record**: `consortium.yourdomain.com → 203.0.113.50`.
2. In `.env` add: `DOMAIN=consortium.yourdomain.com`
3. In `docker-compose.yml`, uncomment the whole `caddy:` service block.
4. `docker compose up -d` — Caddy obtains the certificate automatically.

Your assistant is now at `https://consortium.yourdomain.com` with the padlock. If you skip
this, keep using `http://IP:8000` — but prefer HTTPS before using it from public Wi-Fi.

## Backups

```bash
./scripts/backup.sh              # writes backups/ archives (knowledge base + logs + uploads)
```

Run it before updates, and copy the archives off the server occasionally
(`scp kalan@IP:~/python_learning_projects/expert-consortium/backups/*.tar.gz .`).

## Updating the app

```bash
git pull
docker compose up -d --build
```

## Security checklist

- [ ] `.env` exists only on the server and your computer — never in git (already enforced).
- [ ] `WEB_PASSWORD` is long (12+ characters).
- [ ] `TELEGRAM_ALLOWED_USER_ID` is set (bot refuses everyone otherwise).
- [ ] Firewall active (`sudo ufw status` → 22, 80, 443 only; close 8000 once Caddy runs:
      remove the `ports:` lines of `web` in docker-compose.yml and `docker compose up -d`).
- [ ] Qdrant has no public port (default in our compose file).
- [ ] A spending limit is set in the Mistral console.
- [ ] Backups exist and have been tested once.
