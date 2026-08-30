# R9 review — defects in the supplied patch, and the hardened delta

Reviewed: `R9_rendered_compose_hostconfig_diagnosis.patch`
(`R7C8G_R3_R2_R8.sh` → `R7C8G_R3_R2_R9.sh`, +43 lines at `@@ -1057,4 +1057,43 @@`).

The gate runner is immutable once created, and R9 runs inside a disposable
clone that is destroyed afterwards. A defect in the diagnostic therefore costs
a whole certification cycle, so the patch was reviewed before being built.

## 1. Contract violation — the patch leaks secrets into evidence

`docker compose config` **resolves `env_file` contents inline** and prints the
fully-materialized `environment:` map for every service. The patch pipes that
output straight into the gate log:

```bash
docker compose --project-name "kalanfa-${RID}" -f "$COMPOSE_FILE" \
  config --format json || true
```

Stage08's `runtime.env` carries `POSTGRES_PASSWORD` and `ODOO_ADMIN_PASSWD`.
As written, both land in the evidence directory and in the archive that gets
hashed and retained — directly against the safety contract:

> Never expose secret values; diagnostics must be bounded and redacted.

The same applies to `sed -n '1,240p' "$COMPOSE_FILE"` if the generator ever
inlines `environment:` instead of referencing `env_file:`.

This is not a deviation from the authorized scope — it is what the authorized
scope already required. Item 1 of the gate says "with secret-bearing env-file
contents excluded"; the patch does not implement it. The hardened delta
redacts every `environment` value (keys retained, values replaced with
`<REDACTED:len=N>`) and text-redacts the raw YAML dump.

## 2. Aborts that would destroy the run before the mapping check

The block is injected *after* `RUNTIME_CONTAINERS_RUNNING=PASS` but *before*
`check_mapping()`. R8 runs under `set -euo pipefail`, so anything in the block
that returns non-zero or dereferences an unset variable kills the gate at the
point where the evidence being sought is produced.

| Line | Problem |
| --- | --- |
| `sha256sum "$COMPOSE_FILE"` | No `\|\| true`. Missing file ⇒ non-zero ⇒ `set -e` aborts. |
| `$STATE_ROOT` | Assumed in scope. Unset under `set -u` ⇒ abort. |
| `${RID}` | Same. Also only a guess at the project name. |
| `"${containers[@]}"` | Unset/empty array under `set -u` ⇒ abort. |

The hardened delta wraps the whole body in a function invoked as
`r9_diagnostics || echo 'R9_DIAGNOSTIC=ERROR'`, which suspends `errexit` for
the call, and uses `${VAR:-default}` plus the `${arr[@]+"${arr[@]}"}` idiom
throughout. A diagnostic fault can no longer convert a runtime result into a
false failure.

## 3. Wrong Docker binary

The patch hardcodes `docker` / `docker compose`. The project defines
`KALANFA_DOCKER_BIN` precisely because this runs against a **nested** daemon.
If the variable is set, the patch inspects the wrong daemon and the evidence is
meaningless. Now `${KALANFA_DOCKER_BIN:-docker}`.

## 4. Guessed compose file and project name

`$STATE_ROOT/runtime/stage08/compose.yaml` and `kalanfa-${RID}` are both
assumptions. If either is wrong the diagnostic silently reads a *different*
file than the one the containers were created from — the worst possible
outcome for a root-cause investigation.

The hardened delta derives both from the running containers themselves:

- `com.docker.compose.project.config_files` → the compose file actually used;
- `com.docker.compose.project` → the real project name;

falling back to the derived path only if the labels are unavailable, and
printing `R9_COMPOSE_FILE_SOURCE=container_label|derived_state_path` so the
reader knows which was used.

## 5. Gate item 6 was not implemented

The authorization asks for "a comparison between declared Compose ports,
requested HostConfig bindings, and effective NetworkSettings bindings". The
patch dumps the three structures but never compares them, leaving the
conclusion to manual eyeballing of JSON.

Added: a per-port comparison line and an explicit classification.

```
R9_PORT_COMPARISON|service=..|container=..|target=8069/tcp
                  |declared=127.0.0.1:8084|requested=[]|effective=[]
                  |verdict=DECLARED_NOT_REQUESTED
R9_ROOT_CAUSE_CLASS=COMPOSE_TO_HOSTCONFIG_LOSS
```

| Class | Meaning | Where the defect is |
| --- | --- | --- |
| `COMPOSE_RENDER_FAILED` | `config` produced nothing | compose file is invalid; see captured stderr |
| `COMPOSE_DECLARATION_ABSENT` | no `ports:` in rendered config | the generator, `installer/odoo.sh` |
| `COMPOSE_TO_HOSTCONFIG_LOSS` | declared, never requested | Compose→daemon: stale containers, or ports not applied at create time |
| `HOSTCONFIG_TO_RUNTIME_LOSS` | requested, not effective | nested daemon publishing path (proxy / netfilter / network driver) |
| `NO_DIVERGENCE` | bindings effective | R8 failure not reproduced |

## 6. Smaller omissions, now covered

- `compose config` **stderr** was discarded. Compose warnings about ignored or
  unparsable keys are frequently the entire answer. Now captured and redacted.
- `docker compose version` / `docker --version` were not recorded, despite
  Compose 5.5.0 behaviour being one of the hypotheses.
- `.HostConfig.PublishAllPorts` and `.State.Status` were not captured.
- The `docker info` template in the patch fails as a unit if any field is
  missing. Replaced with `{{json .}}` plus a safe key subset extracted in
  Python.
- `sed -n '1,240p'` truncates silently. Now byte-bounded with an explicit
  `<R9_TRUNCATED_AT_N_BYTES>` marker.
- Network list captured, for the `HOSTCONFIG_TO_RUNTIME_LOSS` case.

## 7. Root-cause hypothesis (to be confirmed or refuted by R9)

R8 recorded that `docker ps` showed `8069/tcp, 8071-8072/tcp` for all three
containers. That set is *exactly* the Odoo image's own `EXPOSE` directives,
with **zero additions and zero host bindings**. Containers that were asked to
publish ports — even unsuccessfully — normally carry the request in
`.HostConfig.PortBindings` regardless of what `NetworkSettings` ends up
showing.

So the most probable classes are `COMPOSE_DECLARATION_ABSENT` or
`COMPOSE_TO_HOSTCONFIG_LOSS`: the publish request was most likely **never
made**, which points at Compose generation in `installer/odoo.sh` (an `expose:`
key where `ports:` was intended, a mis-indented `ports:` node attaching to the
wrong parent, or an empty variable expansion collapsing the entries) rather
than at Docker or the nested runtime.

`HOSTCONFIG_TO_RUNTIME_LOSS` — a genuine nested-daemon publishing failure — is
the less likely branch, but R9 distinguishes them without ambiguity.

**This remains a hypothesis. R9 is diagnostic; no correction is proposed here,
and none may be applied without a separately scoped correction gate.**

## 8. Verification performed

The builder and the injected diagnostic were exercised against synthetic
fixtures (no VPS access was used or required):

- builder refuses a mismatched R8 hash — `BUILD_R9=FAIL reason=r8_sha256_mismatch`;
- builder refuses to overwrite an existing R9 — `output_exists_refusing_to_overwrite`;
- builder rejects ambiguous/missing anchors and enforces guard-before-anchor ordering;
- generated R9 passes `bash -n` and is written `0444`;
- redaction confirmed on both the raw YAML and the rendered JSON, including a
  value present only after `env_file` resolution;
- all four root-cause classes reproduced from fixtures and classified correctly.
