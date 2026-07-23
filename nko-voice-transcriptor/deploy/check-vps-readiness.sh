#!/usr/bin/env bash
# Read-only VPS readiness check for N'Ko Voice Transcriptor.
set -u

PASS=0; WARN=0; FAIL=0
green='\033[1;32m'; yellow='\033[1;33m'; red='\033[1;31m'; reset='\033[0m'
pass() { PASS=$((PASS+1)); printf "${green}PASS${reset}  %s\n" "$*"; }
warn() { WARN=$((WARN+1)); printf "${yellow}WARN${reset}  %s\n" "$*"; }
fail() { FAIL=$((FAIL+1)); printf "${red}FAIL${reset}  %s\n" "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

echo "N'Ko Voice Transcriptor — VPS readiness report"
echo "Generated: $(date -u '+%Y-%m-%d %H:%M UTC')"
echo

if [ -r /etc/os-release ]; then
  . /etc/os-release
  echo "OS: ${PRETTY_NAME:-unknown}"
  case "${ID:-}" in ubuntu|debian) pass "Supported Linux family" ;; *) warn "Ubuntu 24.04 LTS is recommended" ;; esac
else
  fail "Cannot identify the operating system"
fi

ARCH="$(uname -m)"
case "$ARCH" in x86_64|aarch64) pass "CPU architecture: $ARCH" ;; *) warn "Untested CPU architecture: $ARCH" ;; esac
CPU="$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)"
RAM_MB="$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 0)"
DISK_GB="$(df -Pk / | awk 'NR==2 {print int($4/1024/1024)}')"

[ "$CPU" -ge 2 ] && pass "CPU: $CPU cores" || warn "CPU: $CPU core; upgrade to at least 2"
[ "$RAM_MB" -ge 1900 ] && pass "RAM: ${RAM_MB} MB" || warn "RAM: ${RAM_MB} MB; upgrade to at least 2 GB"
[ "$DISK_GB" -ge 8 ] && pass "Free disk: ${DISK_GB} GB" || fail "Free disk: ${DISK_GB} GB; at least 8 GB is required"

if have python3; then
  PY="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  python3 -c 'import sys; raise SystemExit(sys.version_info[:2] < (3,11))' \
    && pass "Python $PY" || fail "Python $PY; version 3.11 or newer is required"
else
  fail "Python 3 is missing"
fi

for cmd in systemctl curl git nginx; do
  have "$cmd" && pass "$cmd is installed" || warn "$cmd is not installed (deployment can install it)"
done

if curl -fsS --max-time 8 https://github.com/ >/dev/null 2>&1; then
  pass "Outbound HTTPS works"
else
  fail "Cannot reach GitHub over HTTPS; check DNS/firewall/proxy"
fi

if have ss; then
  for port in 80 443; do
    if ss -ltn "sport = :$port" 2>/dev/null | grep -q LISTEN; then
      warn "TCP port $port is already in use (normal if Nginx is installed)"
    else
      pass "TCP port $port is available"
    fi
  done
fi

echo
echo "Capacity recommendation"
if [ "$RAM_MB" -ge 7800 ] && [ "$CPU" -ge 4 ] && [ "$DISK_GB" -ge 20 ]; then
  echo "  Suitable for local MMS ASR: 4+ CPU, 8 GB+ RAM, 20 GB+ free disk."
  echo "  External LLM cleanup is also suitable; it adds little local resource usage."
elif [ "$RAM_MB" -ge 1900 ] && [ "$CPU" -ge 2 ] && [ "$DISK_GB" -ge 8 ]; then
  echo "  Suitable for the web/API backend and an external LLM provider."
  echo "  For local MMS ASR, upgrade to 4 vCPU, 8 GB RAM, and 20 GB free disk."
else
  echo "  Upgrade to at least 2 vCPU, 2 GB RAM, and 8 GB free disk for the basic backend."
  echo "  Recommended production/local MMS size: 4 vCPU, 8 GB RAM, 20 GB free disk."
fi

echo
echo "Result: $PASS passed, $WARN warnings, $FAIL failed"
[ "$FAIL" -eq 0 ]
