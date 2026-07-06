#!/usr/bin/env bash
#
# End-to-end smoke test for the AI Quran Teacher backend + signaling server.
#
# Boots both services against an in-memory SQLite DB and a local mock of the
# Mistral API, then exercises every module over real HTTP. Exits non-zero on the
# first failed assertion. Intended for local verification and CI.
#
# Usage: bash scripts/smoke-test.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT=${BACKEND_PORT:-3300}
SIGNAL_PORT=${SIGNAL_PORT:-3301}
MOCK_PORT=${MOCK_PORT:-3399}
B="http://localhost:${BACKEND_PORT}/api"
TMP="$(mktemp -d)"
PIDS=()

pass() { echo "  ✓ $1"; }
fail() { echo "  ✗ $1"; exit 1; }

cleanup() {
  # Kill each service's whole process group (services are started with setsid),
  # so the node child is terminated too — not just its wrapper shell.
  for pid in "${PIDS[@]:-}"; do
    kill -- -"$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
  done
  rm -rf "$TMP"
}
trap cleanup EXIT

# --- assertion helpers ----------------------------------------------------
# assert_status METHOD URL EXPECTED [TOKEN] [BODY]
assert_status() {
  local method="$1" url="$2" expected="$3" token="${4:-}" body="${5:-}"
  local args=(-s -o /dev/null -w '%{http_code}' -X "$method")
  [ -n "$token" ] && args+=(-H "authorization: Bearer $token")
  [ -n "$body" ] && args+=(-H 'content-type: application/json' -d "$body")
  local code; code="$(curl "${args[@]}" "$url")"
  [ "$code" = "$expected" ] || fail "$method $url expected $expected got $code"
  pass "$method ${url#http://localhost:*/} -> $expected"
}

wait_for() {
  local url="$1" name="$2" i
  for i in $(seq 1 40); do
    curl -sf -o /dev/null "$url" && { pass "$name is up"; return 0; }
    sleep 0.25
  done
  fail "$name did not start"
}

# Ready as soon as the port accepts a connection (any HTTP status counts).
wait_for_conn() {
  local url="$1" name="$2" i
  for i in $(seq 1 40); do
    curl -s -o /dev/null "$url" && { pass "$name is up"; return 0; }
    sleep 0.25
  done
  fail "$name did not start"
}

echo "==> Writing mock Mistral server"
cat > "$TMP/mock-mistral.js" <<'EOF'
const http = require('http');
http.createServer((req, res) => {
  if (req.method === 'POST' && req.url.endsWith('/chat/completions')) {
    let b = ''; req.on('data', c => (b += c)); req.on('end', () => {
      const quiz = { questions: [ { prompt: 'What is Ikhfa?', options: ['Concealment','Clarity','Merging','Conversion'], correctIndex: 0, explanation: 'Ikhfa conceals the noon.' } ] };
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ choices: [{ message: { role: 'assistant', content: JSON.stringify(quiz) } }] }));
    });
  } else { res.writeHead(404); res.end(); }
}).listen(process.env.MOCK_PORT || 3399);
EOF

echo "==> Building backend"
(cd "$ROOT/backend" && npm run build >/dev/null 2>&1) || fail "backend build failed"

echo "==> Starting mock Mistral (:$MOCK_PORT)"
setsid bash -c "MOCK_PORT='$MOCK_PORT' exec node '$TMP/mock-mistral.js'" \
  >"$TMP/mock.log" 2>&1 & PIDS+=($!)
wait_for_conn "http://localhost:$MOCK_PORT/" "mock"

echo "==> Starting backend (:$BACKEND_PORT)"
setsid bash -c "cd '$ROOT/backend' && \
  PORT='$BACKEND_PORT' NODE_ENV=test DB_TYPE=sqlite DB_DATABASE=':memory:' DB_SYNCHRONIZE=true \
  JWT_SECRET='smoke-test-secret-that-is-at-least-32-chars' CORS_ORIGINS='http://localhost:$BACKEND_PORT' \
  MISTRAL_API_KEY=mock MISTRAL_API_URL='http://localhost:$MOCK_PORT/v1' \
  exec node dist/main.js" >"$TMP/backend.log" 2>&1 & PIDS+=($!)
wait_for "$B/health" "backend"

echo "==> Backend module checks"
assert_status GET "$B/health" 200
assert_status GET "$B/quran/surahs" 200
assert_status GET "$B/quran/surahs/1/ayahs/1" 200
assert_status GET "$B/quran/surahs/999" 404
assert_status GET "$B/gamification/me" 401   # protected, no token

# Buffer the whole response before parsing (curl output can arrive in chunks).
JSON_FIELD='let s="";process.stdin.on("data",d=>s+=d);process.stdin.on("end",()=>{try{process.stdout.write(String(JSON.parse(s)[process.argv[1]]||""))}catch{}})'
# Unique email per run so a persisted DB never collides on registration.
EMAIL="smoke-$$-$(date +%s)@example.com"
TOKEN="$(curl -s -X POST "$B/auth/register" -H 'content-type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"displayName\":\"Smoke\",\"password\":\"StrongPass123\"}" \
  | node -e "$JSON_FIELD" accessToken)"
[ -n "$TOKEN" ] || fail "registration did not return a token"
pass "registered user + received JWT"

assert_status POST "$B/auth/register" 400 "" '{"email":"x@y.com","displayName":"X","password":"weak"}'
assert_status GET "$B/auth/me" 200 "$TOKEN"

QUIZ="$(curl -s -X POST "$B/quiz/generate" -H "authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' -d '{"difficulty":"beginner","numQuestions":1}')"
echo "$QUIZ" | grep -q '"correctIndex"' && fail "quiz leaked correctIndex to client"
pass "quiz generated without leaking answers"
QID="$(echo "$QUIZ" | node -e "$JSON_FIELD" id)"

RESULT="$(curl -s -X POST "$B/quiz/$QID/submit" -H "authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' -d '{"answers":[0]}')"
echo "$RESULT" | grep -q '"correctCount":1' || fail "quiz grading incorrect: $RESULT"
echo "$RESULT" | grep -q '"pointsAwarded":30' || fail "expected 30 points (1 correct + perfect bonus): $RESULT"
pass "quiz graded and points awarded"

echo "$(curl -s "$B/gamification/me" -H "authorization: Bearer $TOKEN")" | grep -q '"first_steps"' \
  || fail "first_steps badge not awarded"
pass "gamification profile updated (badge earned)"
assert_status GET "$B/gamification/leaderboard" 200 "$TOKEN"

echo "==> Billing module checks (Stripe not configured in smoke env)"
echo "$(curl -s "$B/billing/me" -H "authorization: Bearer $TOKEN")" | grep -q '"isPremium":false' \
  || fail "billing/me should report isPremium=false"
pass "billing/me -> not premium"
assert_status POST "$B/billing/checkout" 503 "$TOKEN" '{"plan":"premium_monthly"}'  # Stripe not configured
assert_status POST "$B/billing/checkout" 400 "$TOKEN" '{"plan":"bogus"}'            # invalid plan rejected
assert_status POST "$B/billing/whitelist" 403 "$TOKEN" '{"userId":"00000000-0000-0000-0000-000000000000"}'  # non-admin
assert_status POST "$B/billing/webhook" 400 "" '{"id":"evt"}'                       # missing signature

echo "==> Signaling server (:$SIGNAL_PORT)"
setsid bash -c "cd '$ROOT/signaling-server' && \
  PORT='$SIGNAL_PORT' NODE_ENV=test ALLOW_ANONYMOUS=true \
  JWT_SECRET='smoke-test-secret-that-is-at-least-32-chars' CORS_ORIGINS='http://localhost:$BACKEND_PORT' \
  exec node src/server.js" >"$TMP/signal.log" 2>&1 & PIDS+=($!)
wait_for "http://localhost:$SIGNAL_PORT/health" "signaling"

echo ""
echo "✅ All modules passed the smoke test."
