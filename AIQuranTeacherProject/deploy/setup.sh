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

echo "==> Configuring UFW firewall (allow SSH, HTTP, HTTPS)"
if command -v ufw >/dev/null 2>&1; then
  ufw allow OpenSSH || ufw allow 22/tcp
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw --force enable
  ufw status verbose
else
  echo "ufw not present; skipping firewall config."
fi

echo "==> Enabling Docker on boot"
systemctl enable --now docker

echo "✅ Provisioning complete. Next:"
echo "   cd <repo>/AIQuranTeacherProject"
echo "   cp deploy/.env.example .env  &&  edit .env"
echo "   docker compose up -d --build"
