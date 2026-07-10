# Deploying the AI Documentation Generator to a Linode VPS

Target: **172.236.240.38** (Ubuntu/Debian). The stack runs under Docker Compose
(web + AI worker + Redis + Caddy) and **auto-starts on every boot**.

> **Security first.** The root password was shared in a chat and must be treated
> as compromised. This guide moves you onto an **SSH key + non-root `deploy`
> user**, then disables root/password login. Change the root password now:
> `ssh root@172.236.240.38` → `passwd`.

---

## 0. Prerequisites you must supply

The app is not standalone — it needs external services. Have these ready:

| Service | Needed for | Where |
| ------- | ---------- | ----- |
| **Supabase** project | auth + database + storage | https://supabase.com (free tier OK) |
| **OpenAI** API key | AI document generation | https://platform.openai.com |
| **Stripe** keys (test OK) | billing pages/webhooks | https://dashboard.stripe.com |
| (optional) a **domain** | HTTPS + Stripe webhooks | your DNS provider |

---

## 1. Get the code onto the VPS

```bash
ssh root@172.236.240.38          # first (and last) password login
apt-get update && apt-get install -y git
git clone https://github.com/kalandengit/python_learning_projects.git /opt/docdgen
cd /opt/docdgen/ai-documentation-generator/deploy
```

## 2. Bootstrap as root (creates the deploy user, installs Docker)

```bash
# Optional: set the deploy user's password (otherwise use the one delivered to you)
export DEPLOY_USER_PASSWORD='paste-the-delivered-password'
bash 00-bootstrap-root.sh
```

This creates user **`deploy`**, installs the **deploy public key**, installs
Docker + Compose, enables Docker on boot, and adds a 2 GB swap file.

## 3. Confirm key login, then switch to the deploy user

From **your local machine** (using the private key delivered to you):

```bash
chmod 600 docdgen_deploy_ed25519
ssh -i docdgen_deploy_ed25519 deploy@172.236.240.38
```

Once that works, harden SSH (disables root + password login):

```bash
sudo bash /opt/docdgen/ai-documentation-generator/deploy/10-harden-ssh.sh
```

## 4. Configure secrets

```bash
cd /opt/docdgen/ai-documentation-generator/deploy
cp .env.production.example .env
nano .env      # fill Supabase, OpenAI, Stripe; set NEXT_PUBLIC_APP_URL + SITE_ADDRESS
```

- Raw-IP test: `NEXT_PUBLIC_APP_URL=http://172.236.240.38` and `SITE_ADDRESS=:80`
- Domain + HTTPS: point the domain's DNS **A record** at `172.236.240.38`, then
  set `NEXT_PUBLIC_APP_URL=https://docs.yourdomain.com` and
  `SITE_ADDRESS=docs.yourdomain.com`.

## 5. Apply database migrations

```bash
./run-migrations.sh      # needs SUPABASE_DB_URL in .env
```

(Or paste `../supabase/migrations/*.sql` in order into the Supabase SQL editor.)

## 6. Deploy

```bash
./deploy.sh
```

Builds the image, starts all services, installs the `docdgen.service` systemd
unit, enables auto-start on boot, and runs the smoke test.

## 7. Test

```bash
BASE=http://172.236.240.38 ./smoke-test.sh
```

Then open **http://172.236.240.38** (or your domain) in a browser, sign up, and
create a document.

---

## Auto-start on reboot (how it works)

- Every service has `restart: unless-stopped`.
- `systemctl enable docker` — Docker starts at boot.
- `docdgen.service` — runs `docker compose up -d --build` at boot.

Verify: `sudo systemctl status docdgen` and `sudo reboot`, then re-check
`docker compose ps`.

## Day-2 operations

```bash
cd /opt/docdgen/ai-documentation-generator/deploy
docker compose ps                 # status
docker compose logs -f web worker # logs
git pull && ./deploy.sh           # ship an update
docker compose down               # stop everything
```

## Troubleshooting

- **Build OOM**: swap is added by bootstrap; if it still fails, resize the
  Linode to ≥2 GB RAM.
- **Home page 500**: usually missing/wrong Supabase env — recheck `.env`, then
  `docker compose up -d --build web`.
- **HTTPS not issued**: DNS A record must point at the VPS and ports 80+443 must
  be open before Caddy can get a certificate.
- **PDF export fails**: the web image bundles Chromium; check
  `docker compose logs web` for Playwright errors.
