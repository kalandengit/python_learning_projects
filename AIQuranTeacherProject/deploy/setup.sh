#!/usr/bin/env bash
#
# One-time provisioning for a fresh Ubuntu 24.04 Linode VPS.
# Installs Docker + Compose plugin and configures the firewall.
# Run as root (or with sudo):  bash deploy/setup.sh
#
set -euo pipefail

echo "==> Updating packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y

echo "==> Installing Docker Engine + Compose plugin"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
docker --version
docker compose version

echo "==> Configuring UFW firewall"
# NOTE: Docker manipulates iptables directly and BYPASSES UFW for any port it
# *publishes* (compose `ports:`). This stack only publishes 80/443 (Caddy);
# the backend, signaling server, and Postgres use `expose` (internal Docker
# network only), so they are never reachable from the internet regardless of
# UFW. Do not add published ports for those services.
if ! command -v ufw >/dev/null 2>&1; then
  apt-get install -y ufw
fi
ufw default deny incoming
ufw default allow outgoing
# Rate-limit SSH to blunt brute-force (denies an IP with >6 connections/30s).
ufw limit OpenSSH 2>/dev/null || ufw limit 22/tcp
ufw allow 80/tcp      # HTTP  (Caddy; also used for Let's Encrypt challenges)
ufw allow 443/tcp     # HTTPS (Caddy)
ufw --force enable
ufw status verbose

echo "==> Sanity check: no database/app port should be world-reachable"
echo "    (only 22, 80, 443 expected above)"

echo "==> Enabling Docker on boot"
systemctl enable --now docker

echo "✅ Provisioning complete. Next:"
echo "   cd <repo>/AIQuranTeacherProject"
echo "   cp deploy/.env.example .env  &&  edit .env"
echo "   docker compose up -d --build"
