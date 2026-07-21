#!/usr/bin/env bash
#
# build-portable-prompts.sh
# -------------------------
# For every skill under skills/ that ships a portable PROMPT.md, regenerate the
# extract-ready, copy-free files from the single source of truth — the text
# between the "BEGIN PORTABLE PROMPT" / "END PORTABLE PROMPT" markers:
#
#   skills/<name>/prompt.txt         # pure instructions, markers stripped
#   skills/<name>/ollama/Modelfile   # Ollama build file wrapping SYSTEM """..."""
#
# Because both are derived from PROMPT.md, they never drift. Re-run after editing
# any PROMPT.md.
#
# Usage:
#   ./scripts/build-portable-prompts.sh                 # base model: llama3
#   OLLAMA_BASE=mistral ./scripts/build-portable-prompts.sh
#
set -euo pipefail

if git rev-parse --show-toplevel >/dev/null 2>&1; then
  ROOT="$(git rev-parse --show-toplevel)"
else
  ROOT="$(pwd)"
fi
cd "$ROOT"

BEGIN='<!-- BEGIN PORTABLE PROMPT -->'
END='<!-- END PORTABLE PROMPT -->'
OLLAMA_BASE="${OLLAMA_BASE:-llama3}"

found=0
for pm in skills/*/PROMPT.md; do
  [ -e "$pm" ] || continue
  dir="$(dirname "$pm")"
  name="$(basename "$dir")"

  if ! grep -qF "$BEGIN" "$pm"; then
    echo ">> Skipping $pm (no portable markers)"
    continue
  fi
  found=1

  # Extract the pure instruction block between the markers.
  block="$(awk -v b="$BEGIN" -v e="$END" '$0==b{f=1;next} $0==e{f=0} f' "$pm")"
  if [ -z "$block" ]; then
    echo "!! $pm has markers but no content between them — skipping." >&2
    continue
  fi

  # 1) prompt.txt — paste-ready, markers stripped.
  printf '%s\n' "$block" > "$dir/prompt.txt"
  echo ">> Wrote $dir/prompt.txt"

  # 2) ollama/Modelfile — wrap the same block in a SYSTEM directive.
  mkdir -p "$dir/ollama"
  {
    printf '# Ollama Modelfile — %s\n' "$name"
    printf '# Build:  ollama create %s -f Modelfile\n' "$name"
    printf '# Run:    ollama run %s\n' "$name"
    printf '# Change FROM to any local base model you prefer.\n'
    printf 'FROM %s\n\n' "$OLLAMA_BASE"
    printf 'SYSTEM """\n'
    printf '%s\n' "$block"
    printf '"""\n'
  } > "$dir/ollama/Modelfile"
  echo ">> Wrote $dir/ollama/Modelfile"
done

if [ "$found" != 1 ]; then
  echo "!! No PROMPT.md with portable markers found under skills/*/" >&2
  exit 1
fi
echo ">> Done."
