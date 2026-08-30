#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# build_R9_from_R8.sh
#
# Deterministically derives the immutable R9 runner from the immutable R8
# runner by injecting the authorized R9 diagnostic delta.
#
# Authorized gate:
#   "authorize isolated Stage08 R9 rendered Compose and HostConfig diagnosis"
#
# The delta is DIAGNOSTIC ONLY. It does not modify authoritative source, does
# not promote Stage08, does not create 08_odoo.done, does not mutate
# production, and does not attempt a correction.
#
# Fail-closed: refuses to produce R9 unless the R8 hash matches, the injection
# anchors are unambiguous, and the result passes `bash -n`.
# ---------------------------------------------------------------------------
set -euo pipefail

R8_PATH="/root/R7C8G_R3_R2_R8.sh"
OUT_PATH="/root/R7C8G_R3_R2_R9.sh"
EXPECT_SHA="d0c622ce1c634deac0ed2998c77aa7118a6e3e6135341088b8c37e70f2444d0a"

usage() {
  cat <<'USAGE'
Usage: build_R9_from_R8.sh [--r8 PATH] [--out PATH] [--expect-sha SHA256]

  --r8 PATH          Source R8 runner   (default /root/R7C8G_R3_R2_R8.sh)
  --out PATH         Destination R9     (default /root/R7C8G_R3_R2_R9.sh)
  --expect-sha SHA   Required SHA-256 of the R8 source. Defaults to the value
                     recorded in the R8 handoff. Overriding it is an explicit,
                     auditable act; there is no way to skip the check.
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --r8)         R8_PATH="${2:?--r8 needs a value}"; shift 2 ;;
    --out)        OUT_PATH="${2:?--out needs a value}"; shift 2 ;;
    --expect-sha) EXPECT_SHA="${2:?--expect-sha needs a value}"; shift 2 ;;
    -h|--help)    usage; exit 0 ;;
    *) echo "BUILD_R9=FAIL reason=unknown_argument:$1" >&2; usage >&2; exit 2 ;;
  esac
done

fail() { echo "BUILD_R9=FAIL reason=$1" >&2; exit 1; }

# --- preconditions ---------------------------------------------------------
[ -f "$R8_PATH" ] || fail "r8_not_found:$R8_PATH"
[ -e "$OUT_PATH" ] && fail "output_exists_refusing_to_overwrite:$OUT_PATH"

ACTUAL_SHA="$(sha256sum "$R8_PATH" | awk '{print $1}')"
echo "R8_PATH=$R8_PATH"
echo "R8_SHA256_ACTUAL=$ACTUAL_SHA"
echo "R8_SHA256_EXPECTED=$EXPECT_SHA"
[ "$ACTUAL_SHA" = "$EXPECT_SHA" ] || fail "r8_sha256_mismatch"
echo "R8_SHA256_MATCH=PASS"

# --- anchor validation -----------------------------------------------------
# The delta is injected immediately before the check_mapping() definition, and
# strictly after the running-containers assertion, so the diagnostic observes
# the runtime in exactly the state the R8 mapping check saw it in.
ANCHOR='^[[:space:]]*check_mapping[[:space:]]*\(\)[[:space:]]*\{'
GUARD="RUNTIME_CONTAINERS_RUNNING=PASS"

anchor_count="$(grep -cE "$ANCHOR" "$R8_PATH" || true)"
[ "$anchor_count" = "1" ] || fail "anchor_not_unique:check_mapping:count=$anchor_count"

anchor_line="$(grep -nE "$ANCHOR" "$R8_PATH" | head -1 | cut -d: -f1)"
guard_line="$(grep -nF "$GUARD" "$R8_PATH" | head -1 | cut -d: -f1 || true)"
[ -n "$guard_line" ] || fail "guard_marker_not_found:$GUARD"
[ "$guard_line" -lt "$anchor_line" ] || fail "anchor_order_unexpected"

echo "ANCHOR_LINE=$anchor_line"
echo "GUARD_LINE=$guard_line"
echo "ANCHOR_VALIDATION=PASS"

# --- assemble --------------------------------------------------------------
TMP_OUT="$(mktemp)"
TMP_BLOCK="$(mktemp)"
trap 'rm -f "$TMP_OUT" "$TMP_BLOCK"' EXIT

cat >"$TMP_BLOCK" <<'R9_BLOCK_EOF'

# ===========================================================================
# R9 DIAGNOSTIC DELTA -- BEGIN
#
# Authorized gate: isolated Stage08 R9 rendered Compose and HostConfig
# diagnosis. Purpose: prove *where* the declared loopback port publishing is
# lost, rather than guess. Captures the three-stage port model:
#
#     declared (rendered Compose)
#         -> requested (.HostConfig.PortBindings)
#             -> effective (.NetworkSettings.Ports)
#
# Constraints honoured here:
#   * read-only: no docker run/create/rm, no source or state mutation;
#   * bounded: every dump is byte-capped;
#   * redacted: no environment value is ever printed, because
#     `docker compose config` resolves env_file contents inline and would
#     otherwise leak POSTGRES_PASSWORD / ODOO_ADMIN_PASSWD into evidence;
#   * non-fatal: the whole block runs under `|| true` so a diagnostic problem
#     can never convert a runtime result into a false failure.
# ===========================================================================
echo 'R9_RENDERED_COMPOSE_DIAGNOSTICS_BEGIN'

r9_diagnostics() {
  local docker_bin max_bytes work compose_file config_files first_container project
  docker_bin="${KALANFA_DOCKER_BIN:-docker}"
  max_bytes=200000

  work="$(mktemp -d 2>/dev/null || true)"
  if [ -z "$work" ] || [ ! -d "$work" ]; then
    work="/tmp/r9-diag.$$"
    mkdir -p "$work" || { echo 'R9_DIAGNOSTIC=SKIPPED reason=no_workdir'; return 0; }
  fi

  # Safe under `set -u` even when the array is unset or empty.
  local -a r9_containers=()
  r9_containers=(${containers[@]+"${containers[@]}"})
  echo "R9_CONTAINER_COUNT=${#r9_containers[@]}"
  first_container="${r9_containers[0]:-}"

  # --- resolve the compose file from the runtime itself ---------------------
  # The container's own compose labels are authoritative; the derived state
  # path is only a fallback, so a wrong assumption about STATE_ROOT cannot
  # silently point the diagnostic at the wrong file.
  compose_file=""
  project=""
  if [ -n "$first_container" ]; then
    config_files="$("$docker_bin" inspect \
      --format '{{index .Config.Labels "com.docker.compose.project.config_files"}}' \
      "$first_container" 2>/dev/null || true)"
    compose_file="${config_files%%,*}"
    project="$("$docker_bin" inspect \
      --format '{{index .Config.Labels "com.docker.compose.project"}}' \
      "$first_container" 2>/dev/null || true)"
  fi
  if [ -z "$compose_file" ] || [ ! -f "$compose_file" ]; then
    compose_file="${STATE_ROOT:-${KALANFA_STATE_ROOT:-/var/lib/kalanfa-installer}}/runtime/stage08/compose.yaml"
    echo 'R9_COMPOSE_FILE_SOURCE=derived_state_path'
  else
    echo 'R9_COMPOSE_FILE_SOURCE=container_label'
  fi
  [ -n "$project" ] || project="kalanfa-${RID:-unknown}"

  echo "R9_COMPOSE_FILE=$compose_file"
  echo "R9_COMPOSE_PROJECT=$project"
  if [ -f "$compose_file" ]; then
    echo 'R9_COMPOSE_FILE_PRESENT=yes'
    echo "R9_COMPOSE_FILE_SHA256=$(sha256sum "$compose_file" 2>/dev/null | awk '{print $1}')"
    echo "R9_COMPOSE_FILE_BYTES=$(wc -c <"$compose_file" 2>/dev/null | tr -d ' ')"
  else
    echo 'R9_COMPOSE_FILE_PRESENT=no'
  fi

  # --- toolchain and daemon context ----------------------------------------
  echo "R9_COMPOSE_VERSION=$("$docker_bin" compose version --short 2>/dev/null || echo unknown)"
  echo "R9_DOCKER_VERSION=$("$docker_bin" --version 2>/dev/null || echo unknown)"
  "$docker_bin" info --format '{{json .}}' >"$work/info.json" 2>/dev/null || true

  # --- rendered compose configuration --------------------------------------
  # stderr is captured too: Compose warnings about ignored or unparsable keys
  # are frequently the actual explanation.
  if [ -f "$compose_file" ]; then
    "$docker_bin" compose --project-name "$project" -f "$compose_file" config --format json \
      >"$work/config.json" 2>"$work/config.err" || true
  fi

  # --- container inspection -------------------------------------------------
  if [ "${#r9_containers[@]}" -gt 0 ]; then
    "$docker_bin" inspect "${r9_containers[@]}" >"$work/inspect.json" 2>/dev/null || true
  fi

  # --- structured model, redaction, and comparison --------------------------
  cat >"$work/r9_model.py" <<'R9_MODEL_PY_EOF'
import json, re, sys

MAXB       = int(sys.argv[1])
P_YAML     = sys.argv[2]
P_CONFIG   = sys.argv[3]
P_CFGERR   = sys.argv[4]
P_INSPECT  = sys.argv[5]
P_INFO     = sys.argv[6]

# Any key whose *name* suggests a credential has its scalar value replaced.
SECRET_KEY = re.compile(r'(?i)pass|secret|token|credential|api[_-]?key|auth')
# Textual "key: value" / "key=value" redaction for the raw YAML dump.
SECRET_TXT = re.compile(
    r'(?i)([A-Za-z0-9_.-]*(?:password|passwd|secret|token|api[_-]?key)[A-Za-z0-9_.-]*)'
    r'(\s*[:=]\s*)(["\']?)([^\s"\',}]+)(\3)')


def read(path):
    try:
        with open(path, 'r', errors='replace') as fh:
            return fh.read()
    except Exception:
        return ''


def load(path):
    raw = read(path)
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def emit_block(tag, text):
    print(tag + '_BEGIN')
    sys.stdout.write(text[:MAXB])
    if not text[:MAXB].endswith('\n'):
        print()
    if len(text) > MAXB:
        print('<R9_TRUNCATED_AT_%d_BYTES>' % MAXB)
    print(tag + '_END')


def redact_text(s):
    return SECRET_TXT.sub(lambda m: m.group(1) + m.group(2) + m.group(3) + '<REDACTED>' + m.group(5), s)


def redact_env(value):
    # Keys are kept (they carry structural meaning); values never are.
    if isinstance(value, dict):
        return {k: '<REDACTED:len=%d>' % len(str(v)) for k, v in value.items()}
    if isinstance(value, list):
        out = []
        for item in value:
            name = str(item).split('=', 1)[0]
            out.append(name + '=<REDACTED>')
        return out
    return '<REDACTED>'


def redact_obj(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in ('environment', 'Env', 'secrets', 'x-secrets'):
                out[k] = redact_env(v)
            elif isinstance(k, str) and SECRET_KEY.search(k) and not isinstance(v, (dict, list)):
                out[k] = '<REDACTED>'
            else:
                out[k] = redact_obj(v)
        return out
    if isinstance(obj, list):
        return [redact_obj(v) for v in obj]
    return obj


# --- 1. raw generated compose file (redacted, bounded) ----------------------
emit_block('R9_COMPOSE_YAML_REDACTED', redact_text(read(P_YAML)))

# --- 2. rendered compose configuration (redacted, bounded) ------------------
cfg = load(P_CONFIG)
cfg_err = read(P_CFGERR).strip()
if cfg_err:
    emit_block('R9_COMPOSE_CONFIG_STDERR', redact_text(cfg_err))
if cfg is None:
    print('R9_COMPOSE_CONFIG_RENDERED=no')
else:
    print('R9_COMPOSE_CONFIG_RENDERED=yes')
    emit_block('R9_COMPOSE_CONFIG_JSON_REDACTED',
               json.dumps(redact_obj(cfg), indent=1, sort_keys=True))

# --- 3. declared port model -------------------------------------------------
services = ((cfg or {}).get('services') or {})
for name in sorted(services):
    svc = services[name] or {}
    ports = svc.get('ports')
    print('R9_SERVICE_DECLARATION|service=%s|ports_key=%s|ports_count=%d'
          '|expose_key=%s|network_mode=%s|container_name=%s' % (
              name,
              'present' if ports is not None else 'absent',
              len(ports) if isinstance(ports, list) else 0,
              'present' if svc.get('expose') is not None else 'absent',
              svc.get('network_mode') or '-',
              svc.get('container_name') or '-'))
    for p in (ports if isinstance(ports, list) else []):
        if isinstance(p, dict):
            print('R9_DECLARED_PORT|service=%s|host_ip=%s|published=%s|target=%s'
                  '|protocol=%s|mode=%s' % (
                      name, p.get('host_ip') or '0.0.0.0', p.get('published'),
                      p.get('target'), p.get('protocol') or 'tcp', p.get('mode') or '-'))
        else:
            print('R9_DECLARED_PORT|service=%s|raw=%s' % (name, p))

# --- 4. observed container port model --------------------------------------
inspect = load(P_INSPECT) or []
models = {}
for x in inspect:
    conf = x.get('Config') or {}
    host = x.get('HostConfig') or {}
    net = x.get('NetworkSettings') or {}
    labels = conf.get('Labels') or {}
    service = labels.get('com.docker.compose.service') or '-'
    model = {
        'Name': (x.get('Name') or '').lstrip('/'),
        'Service': service,
        'State': (x.get('State') or {}).get('Status'),
        'ConfigImage': conf.get('Image'),
        'ExposedPorts': sorted((conf.get('ExposedPorts') or {}).keys()),
        'HostConfigPortBindings': host.get('PortBindings'),
        'HostConfigNetworkMode': host.get('NetworkMode'),
        'HostConfigPublishAllPorts': host.get('PublishAllPorts'),
        'NetworkSettingsPorts': net.get('Ports'),
        'Networks': sorted((net.get('Networks') or {}).keys()),
        'ComposeLabels': {k: v for k, v in labels.items()
                          if k.startswith('com.docker.compose.')},
    }
    models[service] = model
    print('R9_CONTAINER_PORT_MODEL|' + json.dumps(model, sort_keys=True,
                                                  separators=(',', ':')))

# --- 5. declared -> requested -> effective comparison -----------------------
any_declared = any_requested = any_effective = False


def fmt(bindings):
    if not bindings:
        return '[]'
    return ','.join('%s:%s' % (b.get('HostIp', ''), b.get('HostPort', ''))
                    for b in bindings)


for name in sorted(services):
    svc = services[name] or {}
    ports = svc.get('ports') if isinstance(svc.get('ports'), list) else []
    model = models.get(name) or {}
    requested_all = model.get('HostConfigPortBindings') or {}
    effective_all = model.get('NetworkSettingsPorts') or {}
    for p in ports:
        if isinstance(p, dict):
            target = '%s/%s' % (p.get('target'), p.get('protocol') or 'tcp')
            declared = '%s:%s' % (p.get('host_ip') or '0.0.0.0', p.get('published'))
        else:
            target, declared = str(p), str(p)
        any_declared = True
        requested = requested_all.get(target) or []
        effective = effective_all.get(target) or []
        if requested:
            any_requested = True
        if effective:
            any_effective = True
        if not requested and not effective:
            verdict = 'DECLARED_NOT_REQUESTED'
        elif requested and not effective:
            verdict = 'REQUESTED_NOT_EFFECTIVE'
        else:
            verdict = 'EFFECTIVE'
        print('R9_PORT_COMPARISON|service=%s|container=%s|target=%s|declared=%s'
              '|requested=%s|effective=%s|verdict=%s' % (
                  name, model.get('Name', '-'), target, declared,
                  fmt(requested), fmt(effective), verdict))

# --- 6. root-cause classification -------------------------------------------
if cfg is None:
    cls = 'COMPOSE_RENDER_FAILED'
    where = 'compose configuration could not be rendered; see R9_COMPOSE_CONFIG_STDERR'
elif not any_declared:
    cls = 'COMPOSE_DECLARATION_ABSENT'
    where = 'rendered Compose declares no published ports; defect is in the compose generator (installer/odoo.sh)'
elif not any_requested:
    cls = 'COMPOSE_TO_HOSTCONFIG_LOSS'
    where = 'ports declared but never requested at container creation; defect is between Compose and the daemon (stale containers, or Compose not applying ports)'
elif not any_effective:
    cls = 'HOSTCONFIG_TO_RUNTIME_LOSS'
    where = 'bindings requested but not effective; defect is in the nested daemon publishing path (proxy/netfilter/network driver)'
else:
    cls = 'NO_DIVERGENCE'
    where = 'declared ports are effective; the earlier failure was not reproduced'
print('R9_ROOT_CAUSE_CLASS=%s' % cls)
print('R9_ROOT_CAUSE_LOCATION=%s' % where)

# --- 7. daemon networking context (safe subset) ------------------------------
info = load(P_INFO) or {}
keep = ('Driver', 'DockerRootDir', 'OperatingSystem', 'OSType', 'Architecture',
        'ServerVersion', 'KernelVersion', 'CgroupDriver', 'CgroupVersion',
        'LiveRestoreEnabled', 'BridgeNfIptables', 'BridgeNfIp6tables',
        'IPv4Forwarding', 'Isolation')
print('R9_DAEMON|' + json.dumps({k: info.get(k) for k in keep if k in info},
                                sort_keys=True, separators=(',', ':')))
plugins = (info.get('Plugins') or {}).get('Network')
print('R9_DAEMON_NETWORK_PLUGINS=%s' % (','.join(sorted(plugins)) if plugins else '-'))
R9_MODEL_PY_EOF

  python3 "$work/r9_model.py" "$max_bytes" \
    "$compose_file" "$work/config.json" "$work/config.err" \
    "$work/inspect.json" "$work/info.json" || echo 'R9_MODEL=ERROR'

  # --- network-level view, for the HOSTCONFIG_TO_RUNTIME_LOSS case ----------
  "$docker_bin" network ls --format '{{.Name}}|{{.Driver}}|{{.Scope}}' 2>/dev/null \
    | sed 's/^/R9_NETWORK|/' || true

  rm -rf "$work" 2>/dev/null || true
  echo 'R9_DIAGNOSTIC=PASS'
}

r9_diagnostics || echo 'R9_DIAGNOSTIC=ERROR'
echo 'R9_RENDERED_COMPOSE_DIAGNOSTICS_END'
# R9 DIAGNOSTIC DELTA -- END
# ===========================================================================

R9_BLOCK_EOF

# Insert the block immediately before the anchor line.
head -n "$((anchor_line - 1))" "$R8_PATH"  >"$TMP_OUT"
cat "$TMP_BLOCK"                          >>"$TMP_OUT"
tail -n "+$anchor_line" "$R8_PATH"        >>"$TMP_OUT"

# --- validate --------------------------------------------------------------
bash -n "$TMP_OUT" || fail "generated_r9_failed_syntax_check"
echo "R9_SYNTAX_CHECK=PASS"

added="$(( $(wc -l <"$TMP_OUT") - $(wc -l <"$R8_PATH") ))"
echo "R9_LINES_ADDED=$added"
[ "$added" -gt 0 ] || fail "no_lines_added"

# --- publish immutably -----------------------------------------------------
install -m 0444 "$TMP_OUT" "$OUT_PATH"
echo "R9_PATH=$OUT_PATH"
echo "R9_SHA256=$(sha256sum "$OUT_PATH" | awk '{print $1}')"
echo "R9_MODE=$(stat -c '%a' "$OUT_PATH")"
echo "BUILD_R9=PASS"
