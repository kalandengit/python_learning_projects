#!/usr/bin/env bash
#
# 00-bootstrap-root.sh — run ONCE as root on the fresh VPS.
#
#   ssh root@172.236.240.38
#   # upload/clone the repo, then:
#   cd ai-documentation-generator/deploy && bash 00-bootstrap-root.sh
#
# What it does (idempotent):
#   1. Creates a non-root "deploy" user (sudo + docker groups).
#   2. Installs the deploy public key so you log in with the key, not a password.
#   3. Installs Docker Engine + Compose plugin and enables it on boot.
#   4. Ensures a 2 GB swap file (Next.js builds are memory-hungry).
#
# It deliberately does NOT disable root/password SSH login yet — do that with
# 10-harden-ssh.sh only AFTER you confirm key-based login works, to avoid
# locking yourself out.
set -euo pipefail

DEPLOY_USER="deploy"
DEPLOY_PW="__SET_ME__"   # overwritten below; also passed via env if you prefer

# The deploy public key (its private half was delivered to you separately).
DEPLOY_PUBKEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEoDyvz+swsmec0k+huwPCcW2wZhHjpOiqFwKRDXHRmw docdgen-deploy@172.236.240.38'

if [[ $EUID -ne 0 ]]; then echo "Run as root." >&2; exit 1; fi

echo "==> [1/4] Creating user '${DEPLOY_USER}'"
if ! id -u "$DEPLOY_USER" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash "$DEPLOY_USER"
fi
# Password comes from the DEPLOY_USER_PASSWORD env var if set, else the literal.
PW="${DEPLOY_USER_PASSWORD:-$DEPLOY_PW}"
if [[ "$PW" != "__SET_ME__" ]]; then
  echo "${DEPLOY_USER}:${PW}" | chpasswd
fi
usermod -aG sudo "$DEPLOY_USER"

echo "==> [2/4] Installing deploy public key"
install -d -m 700 -o "$DEPLOY_USER" -g "$DEPLOY_USER" "/home/${DEPLOY_USER}/.ssh"
AUTH="/home/${DEPLOY_USER}/.ssh/authorized_keys"
touch "$AUTH"
grep -qF "$DEPLOY_PUBKEY" "$AUTH" || echo "$DEPLOY_PUBKEY" >> "$AUTH"
chmod 600 "$AUTH"; chown "${DEPLOY_USER}:${DEPLOY_USER}" "$AUTH"

echo "==> [3/4] Installing Docker Engine + Compose"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker
usermod -aG docker "$DEPLOY_USER"

echo "==> [4/4] Ensuring 2 GB swap"
if ! swapon --show | grep -q .; then
  fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile; mkswap /swapfile; swapon /swapfile
  grep -qF '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo
echo "Bootstrap complete."
echo "  Test key login from your machine:"
echo "    ssh -i docdgen_deploy_ed25519 ${DEPLOY_USER}@$(hostname -I | awk '{print $1}')"
echo "  Then deploy the app as '${DEPLOY_USER}' (see DEPLOY.md)."
echo "  Only AFTER confirming key login, harden SSH: sudo bash 10-harden-ssh.sh"
