#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# gate-agent.sh — command/evidence channel for the Kalanfa Stage08 gate.
#
# Polls a private git branch for queued task scripts, executes them, and
# pushes the (redacted, bounded) output back so results can be read remotely
# without anyone copying terminal text by hand.
#
# OPERATING MODE: fully automatic. Any script placed at queue/*.task.sh on the
# watched branch is executed as this user with no prompt. Anyone with push
# access to that branch therefore has code execution on this host. This is a
# deliberate choice by the operator; keep the repository private and its
# collaborator list short.
#
# Safety properties that are enforced regardless:
#   * only files matching queue/*.task.sh are ever executed;
#   * each task's SHA-256 is recorded in its result, so the audit trail shows
#     exactly what ran;
#   * a task runs once per content hash — editing a task re-runs it, a
#     re-poll of unchanged content does not;
#   * every task is wrapped in a hard timeout;
#   * output is byte-capped so a runaway task cannot fill the disk or the repo;
#   * output is redacted for credential-shaped values before it is committed.
# ---------------------------------------------------------------------------
set -uo pipefail

REPO_URL=""
BRANCH="main"
WORKDIR="/root/kalanfa-gate-agent"
TOKEN_FILE="/root/.kalanfa-gate-agent.token"
INTERVAL=20
TASK_TIMEOUT=10800          # 3h — a full gate run is long
MAX_OUTPUT_BYTES=524288     # 512 KiB per result

usage() {
  cat <<'USAGE'
Usage: gate-agent.sh --repo <https-url> [options]

  --repo URL          Private repository to watch (required), e.g.
                      https://github.com/<owner>/kalanfa-gate-channel.git
  --branch NAME       Branch to watch and push to        (default: main)
  --workdir PATH      Local clone location               (default: /root/kalanfa-gate-agent)
  --token-file PATH   File containing a GitHub PAT       (default: /root/.kalanfa-gate-agent.token)
  --interval SECONDS  Poll interval                      (default: 20)
  --task-timeout SEC  Per-task hard timeout              (default: 10800)
  --once              Run a single poll cycle and exit (useful for testing)
USAGE
}

ONCE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --repo)         REPO_URL="${2:?--repo needs a value}"; shift 2 ;;
    --branch)       BRANCH="${2:?--branch needs a value}"; shift 2 ;;
    --workdir)      WORKDIR="${2:?--workdir needs a value}"; shift 2 ;;
    --token-file)   TOKEN_FILE="${2:?--token-file needs a value}"; shift 2 ;;
    --interval)     INTERVAL="${2:?--interval needs a value}"; shift 2 ;;
    --task-timeout) TASK_TIMEOUT="${2:?--task-timeout needs a value}"; shift 2 ;;
    --once)         ONCE=1; shift ;;
    -h|--help)      usage; exit 0 ;;
    *) echo "AGENT=FAIL reason=unknown_argument:$1" >&2; usage >&2; exit 2 ;;
  esac
done

[ -n "$REPO_URL" ] || { echo "AGENT=FAIL reason=missing_--repo" >&2; usage >&2; exit 2; }

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

# --- credentials ------------------------------------------------------------
# The token is written to a 0600 credential store and referenced by config, so
# it never appears in the remote URL, in `git remote -v`, or in the process
# list.
# Agent state lives OUTSIDE the clone: the clone directory must be empty for
# `git clone`, and nothing the agent writes for itself belongs in the repo.
STATE_DIR="${WORKDIR%/}.state"
CRED_FILE="$STATE_DIR/gitcred"
REDACT_PY="$STATE_DIR/redact.py"

setup_credentials() {
  [ -f "$TOKEN_FILE" ] || { log "AGENT=FAIL reason=token_file_not_found:$TOKEN_FILE"; exit 2; }
  local token host
  token="$(tr -d ' \t\r\n' <"$TOKEN_FILE")"
  [ -n "$token" ] || { log "AGENT=FAIL reason=token_file_empty"; exit 2; }
  host="$(printf '%s' "$REPO_URL" | sed -E 's#^https://([^/]+)/.*#\1#')"
  umask 077
  printf 'https://x-access-token:%s@%s\n' "$token" "$host" >"$CRED_FILE"
  chmod 600 "$CRED_FILE"
  unset token
}

git_c() { git -C "$WORKDIR" -c "credential.helper=store --file=$CRED_FILE" "$@"; }

# --- redaction --------------------------------------------------------------
write_redactor() {
  cat >"$REDACT_PY" <<'REDACT_EOF'
import re, sys

MAXB = int(sys.argv[1])

# Credential-shaped assignments: keep the key, drop the value.
PAT = re.compile(
    r'(?i)([A-Za-z0-9_.-]*(?:password|passwd|secret|token|api[_-]?key|'
    r'auth[_-]?token|private[_-]?key|credential)[A-Za-z0-9_.-]*)'
    r'(\s*[:=]\s*)(["\']?)([^\s"\',}]+)(\3)')
# Anything that looks like a bearer/PAT literal on its own.
PAT2 = re.compile(r'\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b')

data = sys.stdin.buffer.read(MAXB + 1)
truncated = len(data) > MAXB
text = data[:MAXB].decode('utf-8', errors='replace')
text = PAT.sub(lambda m: m.group(1) + m.group(2) + m.group(3) + '<REDACTED>' + m.group(5), text)
text = PAT2.sub('<REDACTED_TOKEN>', text)
sys.stdout.write(text)
if truncated:
    sys.stdout.write('\n<AGENT_OUTPUT_TRUNCATED_AT_%d_BYTES>\n' % MAXB)
REDACT_EOF
}

redact() { python3 "$REDACT_PY" "$MAX_OUTPUT_BYTES"; }

# --- repository -------------------------------------------------------------
ensure_clone() {
  if [ ! -d "$WORKDIR/.git" ]; then
    mkdir -p "$(dirname "$WORKDIR")"
    log "cloning $REPO_URL"
    git -c "credential.helper=store --file=$CRED_FILE" \
        clone --branch "$BRANCH" "$REPO_URL" "$WORKDIR" \
      || { log "AGENT=FAIL reason=clone_failed"; exit 2; }
  fi
  git_c config user.email "gate-agent@kalanfa.local"
  git_c config user.name  "Kalanfa Gate Agent"
}

sync_down() {
  git_c fetch --quiet origin "$BRANCH" || { log "fetch failed; will retry"; return 1; }
  git_c reset --quiet --hard "origin/$BRANCH" || return 1
  return 0
}

push_up() {
  local attempt
  for attempt in 1 2 3 4; do
    if git_c push --quiet origin "HEAD:$BRANCH" 2>/dev/null; then
      return 0
    fi
    log "push rejected (attempt $attempt); rebasing onto origin/$BRANCH"
    git_c fetch --quiet origin "$BRANCH" || true
    git_c rebase --quiet "origin/$BRANCH" || { git_c rebase --abort >/dev/null 2>&1 || true; }
    sleep $((attempt * 3))
  done
  log "AGENT=WARN reason=push_failed_results_remain_local"
  return 1
}

# --- task execution ---------------------------------------------------------
run_task() {
  local task="$1"
  local name sha short started finished rc out_file
  name="$(basename "$task" .task.sh)"
  sha="$(sha256sum "$task" | awk '{print $1}')"
  short="${sha:0:12}"

  local marker="$WORKDIR/results/${name}.${short}.done"
  [ -f "$marker" ] && return 0

  mkdir -p "$WORKDIR/results"
  started="$(date -u +%Y%m%dT%H%M%SZ)"
  out_file="$WORKDIR/results/${name}.${short}.out"

  log "running task=$name sha=$short timeout=${TASK_TIMEOUT}s"

  local raw
  raw="$(mktemp)"
  timeout --signal=TERM --kill-after=60 "$TASK_TIMEOUT" \
    bash "$task" >"$raw" 2>&1
  rc=$?
  finished="$(date -u +%Y%m%dT%H%M%SZ)"

  {
    echo "AGENT_TASK=$name"
    echo "AGENT_TASK_SHA256=$sha"
    echo "AGENT_HOST=$(hostname)"
    echo "AGENT_STARTED_UTC=$started"
    echo "AGENT_FINISHED_UTC=$finished"
    echo "AGENT_EXIT_CODE=$rc"
    [ "$rc" -eq 124 ] && echo "AGENT_NOTE=task_hit_timeout_${TASK_TIMEOUT}s"
    echo "AGENT_OUTPUT_BEGIN"
    redact <"$raw"
    echo "AGENT_OUTPUT_END"
  } >"$out_file"
  rm -f "$raw"

  printf 'sha256=%s\nexit=%s\nfinished=%s\n' "$sha" "$rc" "$finished" >"$marker"

  git_c add -- "results/${name}.${short}.out" "results/${name}.${short}.done" >/dev/null 2>&1 || true
  git_c commit --quiet -m "agent: result for ${name} (${short}) exit=${rc}" >/dev/null 2>&1 || true
  log "completed task=$name exit=$rc"
}

poll_once() {
  sync_down || return 0

  [ -d "$WORKDIR/queue" ] || return 0
  local found=0 task
  # Only queue/*.task.sh is ever executed.
  while IFS= read -r task; do
    [ -n "$task" ] || continue
    found=1
    run_task "$task"
  done < <(find "$WORKDIR/queue" -maxdepth 1 -type f -name '*.task.sh' | sort)

  if [ "$found" -eq 1 ] && ! git_c diff --quiet HEAD "origin/$BRANCH" 2>/dev/null; then
    push_up || true
  fi
}

# --- main -------------------------------------------------------------------
mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"
setup_credentials
ensure_clone
write_redactor

log "agent started repo=$REPO_URL branch=$BRANCH interval=${INTERVAL}s mode=AUTOMATIC"
log "watching queue/*.task.sh — queued scripts run with no prompt"

while :; do
  poll_once || log "poll cycle error (continuing)"
  [ "$ONCE" -eq 1 ] && break
  sleep "$INTERVAL"
done

log "agent stopped"
