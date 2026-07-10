#!/usr/bin/env bash
#
# 10-harden-ssh.sh — run as root AFTER you have confirmed that key-based login
# as the 'deploy' user works. It disables root SSH login and password auth, so
# only holders of the deploy private key can get in.
#
#   sudo bash 10-harden-ssh.sh
#
# SAFETY: keep your current root session open while you run this and test a NEW
# key-based login in a second terminal. If something is wrong, revert by
# deleting /etc/ssh/sshd_config.d/99-docdgen-hardening.conf and restarting sshd.
set -euo pipefail
if [[ $EUID -ne 0 ]]; then echo "Run as root (sudo)." >&2; exit 1; fi

CONF=/etc/ssh/sshd_config.d/99-docdgen-hardening.conf
cat > "$CONF" <<'EOF'
# Managed by ai-documentation-generator/deploy/10-harden-ssh.sh
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
KbdInteractiveAuthentication no
EOF

# Validate before applying so a typo can't break sshd.
sshd -t
systemctl reload ssh 2>/dev/null || systemctl reload sshd
echo "SSH hardened: root login + password auth disabled. Key-only from now on."
