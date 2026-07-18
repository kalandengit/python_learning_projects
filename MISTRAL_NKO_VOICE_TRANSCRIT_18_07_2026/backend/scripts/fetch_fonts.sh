#!/usr/bin/env bash
# Self-host Noto Sans NKo (SIL OFL 1.1) for consistent CSP-strict rendering.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p app/static/fonts
URL="https://github.com/notofonts/nko/raw/main/fonts/NotoSansNKo/googlefonts/ttf/NotoSansNKo-Regular.ttf"
curl -fsSL "$URL" -o app/static/fonts/NotoSansNKo-Regular.ttf
echo "Downloaded $(du -h app/static/fonts/NotoSansNKo-Regular.ttf | cut -f1) — done."
