# OpenClaw Handoff — Odoo Stage08 R9 Runtime-Certification Error HOLD

## Current verdict

`RESULT=HOLD`

`HOLD_REASON=UNEXPECTED_ERROR_AT_runtime_certification`

Stage08 has not been promoted. Production and the authoritative certification lab
remain unchanged. The R8 port-binding question is **still open**: R9 did not reach
a port verdict, so the R8 finding was neither confirmed nor refuted.

## Authoritative environment

- VPS: address withheld — this copy lives in a public repository; see the private channel or the operator's local copy
- Certification container: `kalanfa-lab-2604-cert`
- Product root: `/opt/kalanfa-installer-dev`
- State root: `/var/lib/kalanfa-installer`
- Platform: Ubuntu 26.04, Odoo Community 19, PostgreSQL 18.6, Docker 29.7.2, Compose 5.5.0
- Product version: `0.9.5-r7c8g-r3-r1-stage08-runtime-implementation-dev`
- State: `STATUS=READY`, `CURRENT_STAGE=08_odoo`, `LAST_SUCCESSFUL_STAGE=07_database`
- Marker `07_database.done`: present
- Marker `08_odoo.done`: **absent**
- PostgreSQL `18/main` authoritative baseline: down

## Safety contract

Unchanged from R8. Restated because R9 did not relax any of it:

- Every runtime attempt executes in a disposable privileged clone with outer network `none`.
- No host bind mounts or published outer ports.
- Certified local images are transferred without pull or download.
- PostgreSQL configuration, service state, temporary roles/databases, containers,
  networks and volumes are restored/removed during cleanup.
- Stage08 checkpoint/promotion remains forbidden unless the entire isolated
  certification passes.
- Never expose secret values; diagnostics must be bounded and redacted.

## Correction history

- R4 fixed stdin attachment and apply-contract problems; exposed PostgreSQL ownership/failure-propagation defects.
- R5 introduced clone-only PostgreSQL permission corrections and negative tests.
- R6 added bounded running/TCP/HTTP readiness and redacted diagnostics.
- R7 corrected crossed expectations: P1 gevent `8075`, P2 HTTP `8086`.
- R8 replaced `docker port` text parsing with structured `.NetworkSettings.Ports` inspection.
  Result: all three containers running, **effective bindings empty**, `STRUCTURED_PORT_MAPPING=FAIL`.
- R9 (this cycle) added the authorized rendered-Compose / HostConfig diagnostic delta.
  Result: **new failure mode before any port verdict was produced.**

## R9 construction

The originally supplied R9 patch was **not applied as written**. It was reviewed
first and found to violate the safety contract it was bound by, plus four defects
that would have aborted the run at the exact point the sought evidence is produced.

### Defects found in the supplied patch

1. **Secret leak (contract violation).** `docker compose config` resolves `env_file`
   contents inline and prints the fully-materialized `environment:` map. The patch
   piped that straight into the gate log, which is archived and hashed. This would
   have published `POSTGRES_PASSWORD` and `ODOO_ADMIN_PASSWD` into retained evidence.
   Gate authorization item 1 already required their exclusion; the patch did not
   implement it.
2. **Aborts under `set -euo pipefail`** — unguarded `sha256sum`, `$STATE_ROOT`,
   `$RID`, and `"${containers[@]}"`.
3. **Wrong Docker binary** — hardcoded `docker` instead of `$KALANFA_DOCKER_BIN`,
   against a *nested* daemon.
4. **Guessed compose path and project name** — would silently read a different file
   than the one the containers were created from.
5. **Authorization item 6 unimplemented** — no declared/requested/effective comparison.
6. Smaller: `compose config` stderr discarded, no version capture, silent truncation
   at 240 lines, `docker info` template failing as a unit.

### Hardened delta actually applied

Redacts every `environment` value (keys retained, values → `<REDACTED:len=N>`);
derives the compose file and project name from the containers' own
`com.docker.compose.*` labels with the state path only as fallback; captures
`compose config` stderr; wraps everything in a function invoked as
`r9_diagnostics || echo 'R9_DIAGNOSTIC=ERROR'` so a diagnostic fault cannot
convert a runtime result into a false failure; and classifies the outcome into
one of five root-cause classes:

| Class | Meaning | Defect location |
| --- | --- | --- |
| `COMPOSE_RENDER_FAILED` | `config` produced nothing | invalid compose file; see captured stderr |
| `COMPOSE_DECLARATION_ABSENT` | no `ports:` rendered | the generator, `installer/odoo.sh` |
| `COMPOSE_TO_HOSTCONFIG_LOSS` | declared, never requested | Compose→daemon at create time |
| `HOSTCONFIG_TO_RUNTIME_LOSS` | requested, not effective | nested daemon publishing path |
| `NO_DIVERGENCE` | bindings effective | R8 failure not reproduced |

### Builder

`build_R9_from_R8.sh` derives R9 from R8 deterministically and fail-closed:
verifies R8's SHA-256, requires exactly one `check_mapping()` anchor with the
`RUNTIME_CONTAINERS_RUNNING=PASS` guard preceding it, injects the delta,
`bash -n` checks the result, and publishes it `0444`.

Build output on the VPS:

```text
R8_SHA256_MATCH=PASS
ANCHOR_LINE=1060
GUARD_LINE=1058
ANCHOR_VALIDATION=PASS
R9_SYNTAX_CHECK=PASS
R9_LINES_ADDED=324
R9_MODE=444
BUILD_R9=PASS
```

### Pre-existing R9 placeholder

`/root/R7C8G_R3_R2_R9.sh` already existed at build time, mode `644`, mtime
`2026-08-30T04:15:13Z`, and was **byte-identical to R8** (same SHA-256
`d0c622ce…`, zero delta, no diagnostic markers). It was a placeholder, not a gate
revision. It was archived, not deleted:

`/root/_gate_archive/R7C8G_R3_R2_R9.placeholder-20260830T041513Z.sh`

## R9 invocation grammar

Recovered from the runner (shell history is not recorded on this host, and the R8
evidence does not record the invocation). Both values are defined inside the
runner itself — line 6 (`AUTH_TOKEN`) and line 32 (`SERVER_ID_EXPECTED`) — and are
compared at lines 117 and 121:

```
--server-id <SERVER_ID_EXPECTED> --authorize '<AUTH_TOKEN>'
```

Invoke without ever displaying either value:

```bash
eval "$(grep -m1 '^SERVER_ID_EXPECTED=' /root/R7C8G_R3_R2_R9.sh)"
eval "$(grep -m1 '^AUTH_TOKEN='         /root/R7C8G_R3_R2_R9.sh)"
bash /root/R7C8G_R3_R2_R9.sh --server-id "$SERVER_ID_EXPECTED" --authorize "$AUTH_TOKEN"
```

Do **not** use `--help`: it interpolates both values into its output.

Precheck order: `RUN_AS_ROOT_REQUIRED` → `SERVER_ID_MISMATCH` →
`AUTHORIZATION_TOKEN_MISMATCH` → `R5_DATABASE_SOURCE_SHA_MISMATCH` →
`R5_DATABASE_TEST_SHA_MISMATCH`.

## R9 result

`UTC=2026-08-30T05:05:31Z`, `RUNTIME_LAB=kalanfa-r7c8g-r3-r2-r2-20260830t050531z1693540`,
`OUTER_NETWORK=none`, `AUTHORIZATION=ACCEPTED`.

Passed (sections 1–7, identical to R8):

```text
PRODUCT_BASH_N=PASS
CERTIFIED_SOURCE_HASHES=PASS
AUTHORITATIVE_PG_STATUS_BEFORE=down
AUTHORITATIVE_CHECKPOINT_PRECHECK=PASS
LOCAL_IMAGE_AUTHORITY=PASS
RUNTIME_CLONE_ISOLATION=PASS
OUTER_NETWORK_NONE=PASS
HOST_BIND_MOUNTS=NONE
UNEXPECTED_MOUNTS=0
OUTER_PUBLISHED_PORTS=NONE
CLONE_SOURCE_AND_STATE_IDENTITY=PASS
R5_DATABASE_SOURCE_OVERLAY=PASS
R5_DATABASE_TEST_MATRIX=PASS
NESTED_DOCKER_RUNTIME=PASS
NESTED_DOCKER_COW_STORAGE=PASS
NESTED_DOCKER_FRESH_STORE=PASS
P1_CERTIFIED_LOCAL_IMAGE_LOAD=PASS
P2_CERTIFIED_LOCAL_IMAGE_LOAD=PASS
PORTABLE_CONFIG_ROOTFS_IDENTITY=PASS
REEXPORTED_CONFIG_DIGEST_CONTINUITY=PASS
STAGE08_RUNTIME_ENGINE_EXECUTION=PASS
```

Image identity, unchanged from R8:

```text
OUTER_P1_IMAGE_ID=sha256:e2d9c3855e458342d37bee61d30155bf41f7d7a37b910ebd1c3ae4c59beb0773
OUTER_P2_IMAGE_ID=sha256:7b40ce6232b6702b495b1683dae3b29fc48b031710657ed204a3c186ec69fd88
SEED_IMAGE_ID=sha256:cfcc032e168e605882d942473a616c1716caf472c9d27b626e9ac0ecb1c0266f
```

Failed:

```text
===== 8. RUNTIME CONTAINER / PORT / HTTP CERTIFICATION =====
<no stdout output whatsoever>
===== CLEANUP / ROLLBACK =====
HOLD_REASON=UNEXPECTED_ERROR_AT_runtime_certification
```

**This is a different failure mode from R8.** R8 reached
`RUNTIME_CONTAINERS_RUNNING=PASS` and then failed a specific assertion
(`STRUCTURED_PORT_MAPPING=FAIL`). R9 produced *no* section-8 stdout at all and
tripped an error trap. No `R9_RENDERED_COMPOSE_DIAGNOSTICS_BEGIN` marker appeared
in the tee'd run log.

## R9 artifacts

- Runner: `/root/R7C8G_R3_R2_R9.sh` (mode `0444`)
- Runner SHA256: `155fe17de3b4e4c7b1c6cb18debaefc556553f20883f7d8ff822d25481e4ad0f`
- Parent R8 SHA256: `d0c622ce1c634deac0ed2998c77aa7118a6e3e6135341088b8c37e70f2444d0a`
- Run log: `/root/R9_run_20260830T050531Z.log`
- Evidence directory: `/var/backups/kalanfa-gate-r7c8g-r3-r2-r2-stage08-overlay2-portable-identity-immutability-fix/20260830T050531Z`
- Evidence archive: same path with `.tar.gz`
- Evidence archive SHA256: `b7257a329e9d12c02eda53b9f7d3f82a44be38fe1a1ace7ab5737256753560fd`
- Builder + review, public repo `kalandengit/python_learning_projects`,
  branch `claude/vps-project-deployment-2cfufk`, commits `8035dd0`, `b290240`,
  path `_codex_gate_2026-08-30/`

## R9 cleanup truth

```text
RUNTIME_CLONE_CLEANUP=PASS
TEMP_DATA_VOLUME_CLEANUP=PASS
PRODUCTION_IMMUTABILITY=PASS
AUTHORITATIVE_CERT_LAB_IMMUTABILITY=PASS
TEMP_DATABASE_CLEANUP=PASS
TEMP_ROLE_CLEANUP=PASS
TEMP_CONTAINER_CLEANUP=PASS
TEMP_NETWORK_CLEANUP=PASS
POSTGRESQL_CONFIGURATION_RESTORED=PASS
POSTGRESQL_INITIAL_SERVICE_STATE_RESTORED=PASS
STAGE08_CHECKPOINT_EXECUTED=NO
MARKER_08_odoo=ABSENT
PRODUCTION_MUTATION=NO
DOCKER_PULL_EXECUTED=NO
REGISTRY_PULL_EXECUTED=NO
NETWORK_DOWNLOAD_EXECUTED=NO
```

Independently verified: a recursive scan of `/var/backups/kalanfa-gate-*/` for
credential-shaped assignments returned **no matches**. The unhardened patch was
never run, so no secret has entered retained evidence.

## The open question

Section 8 produced no stdout. Two mutually exclusive explanations, unresolved:

**(A) Section 8 redirects to the evidence file.** The evidence directory contains
`runtime_certification.log`, and the `PORT_MAPPING_OBSERVED|…` lines quoted in the
R8 handoff have exactly that file's shape. If so, the R9 diagnostic block ran
normally and its output is in that file — the tee'd stdout log simply never
carried it.

**(B) The injected delta errored** and tripped the trap.

The discriminator is the marker sequence. If R9's `runtime_certification.log`
stops *before* `RUNTIME_CONTAINERS_RUNNING`, the fault is upstream of the
injection point at line 1060 and the delta never executed — making this an
independent defect in the runtime stage. If R9 passes that marker and stops inside
the delta, the defect is in the delta.

Collect with (read-only):

```bash
D=/var/backups/kalanfa-gate-r7c8g-r3-r2-r2-stage08-overlay2-portable-identity-immutability-fix/20260830T050531Z
D8=/var/backups/kalanfa-gate-r7c8g-r3-r2-r2-stage08-overlay2-portable-identity-immutability-fix/20260830T040529Z

grep -c 'R9_RENDERED_COMPOSE_DIAGNOSTICS' "$D/runtime_certification.log"
sed -n '/R9_RENDERED_COMPOSE_DIAGNOSTICS_BEGIN/,/R9_RENDERED_COMPOSE_DIAGNOSTICS_END/p' "$D/runtime_certification.log"
tail -80 "$D/runtime_certification.log"
diff <(grep -oE '^[A-Z0-9_]+=' "$D8/runtime_certification.log") \
     <(grep -oE '^[A-Z0-9_]+='  "$D/runtime_certification.log") | head -40
cat "$D/STATUS.txt"
```

## Standing root-cause hypothesis for the original port defect

R8 observed `8069/tcp, 8071-8072/tcp` on all three containers — *exactly* the Odoo
image's own `EXPOSE` set, with zero additions and zero host bindings. A container
asked to publish ports normally records the request in `.HostConfig.PortBindings`
even when publishing subsequently fails. The likely classes are therefore
`COMPOSE_DECLARATION_ABSENT` or `COMPOSE_TO_HOSTCONFIG_LOSS`, implicating Compose
generation in `installer/odoo.sh` (an `expose:` key where `ports:` was intended, a
mis-indented `ports:` node, or an empty variable expansion) rather than Docker or
the nested runtime.

**Hypothesis only. R9 has not yet produced a verdict. Do not act on this without
the diagnostic output, and do not implement a correction without a separately
scoped correction gate.**

## Operational channel (new this cycle)

Manual copy-paste was replaced with a git-mediated command/evidence channel, built
and tested but **not yet activated**.

- `_codex_gate_2026-08-30/agent/gate-agent.sh` — polls a private branch for
  `queue/*.task.sh`, executes them, pushes redacted bounded output to `results/`.
- `_codex_gate_2026-08-30/agent/kalanfa-gate-agent.service` — systemd unit.
- `_codex_gate_2026-08-30/agent/queue/001-r9-evidence.task.sh` — the collection
  task above, pre-written.

Operating mode is **fully automatic** by operator decision: anything at
`queue/*.task.sh` runs as root with no prompt, so push access to that branch is
equivalent to root on the certification host. Enforced regardless: only
`queue/*.task.sh` executes; each task's SHA-256 is recorded in its result; a task
runs once per content hash; hard timeout per task; byte-capped output;
credential-shaped values redacted before commit; agent state kept outside the clone.

Verified against a local bare repo: execution and exit-code capture, result
push-back, redaction of a password assignment and a `ghp_` literal, idempotency,
re-execution on edit, and timeout enforcement (`exit=124`).

Blocked on operator action: create private repo `kalanfa-gate-channel`, create a
fine-grained PAT scoped to Contents:read-write on that repo alone, install the
unit. The assisting agent could not create the repository
(`403 Resource not accessible by integration`).

## Documentation authority

```text
DOCS_AUTHORITY_SKILL=developer-docs-authority
DOCS_GATE=NOT_EXERCISED_THIS_CYCLE
TECH_SURFACES=Odoo Community 19,Docker Compose,PostgreSQL 18,isolated deployment certification
ODOO_VERSION=19.0 Community
OFFICIAL_DOCS_USED=none this cycle — no version-specific question arose
DEPRECATION_CHECK=NOT_APPLICABLE
SECURITY_DOCS_CHECK=PASS (secret-leak defect identified and corrected pre-execution)
TEST_RESULT=HOLD
RUNTIME_VALIDATION=HOLD
```

## OpenClaw continuation prompt

Continue the Odoo Stage08 certification from R9 HOLD. Treat this document as
context, not as authorization beyond the already-recorded R9 diagnostic gate.

R9 was built (SHA-256 `155fe17d…`, mode `0444`) and executed. Sections 1–7 passed
identically to R8, but section 8 emitted no stdout and the run ended
`HOLD_REASON=UNEXPECTED_ERROR_AT_runtime_certification`. Cleanup, rollback and
immutability all passed; production is unmutated; `08_odoo.done` is absent; no
secret has entered evidence.

Your first task is **not** to correct anything. It is to read
`runtime_certification.log` in evidence directory `20260830T050531Z` and determine
whether the injected diagnostic block executed. Compare its marker sequence
against R8's `20260830T040529Z`. If the log stops before
`RUNTIME_CONTAINERS_RUNNING`, the runtime stage has an independent defect and the
R9 delta never ran. If it stops inside the delta, the delta is at fault and must be
corrected under a new sequential revision — never by mutating `R7C8G_R3_R2_R9.sh`,
which is immutable at `0444`.

Preserve all offline, immutability, cleanup, redaction and no-promotion controls.
Never expose `AUTH_TOKEN` or `SERVER_ID_EXPECTED` values. Never create
`08_odoo.done` or mutate production unless a later explicit promotion gate is
granted after a complete isolated certification PASS. If a source or nested-runtime
defect is proven, stop at HOLD and request a separately scoped correction gate.
