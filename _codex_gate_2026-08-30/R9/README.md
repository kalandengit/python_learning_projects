# R9 — Isolated Stage08 rendered-Compose / HostConfig diagnosis

Authorized gate:
`gate: authorize isolated Stage08 R9 rendered Compose and HostConfig diagnosis = yes`

Scope is **diagnostic only**. R9 must not modify authoritative source, promote
Stage08, create `08_odoo.done`, mutate production, or guess a correction.

## Files

| File | Purpose |
| --- | --- |
| `build_R9_from_R8.sh` | Verifies R8's SHA-256, injects the R9 diagnostic delta, writes an immutable `R7C8G_R3_R2_R9.sh` (mode `0444`) and prints its hash. |
| `R9_REVIEW.md` | Review of the originally supplied R9 patch, the defects found, and the root-cause hypothesis the diagnostic is designed to settle. |

## Usage on the VPS

```
bash build_R9_from_R8.sh \
  --r8 /root/R7C8G_R3_R2_R8.sh \
  --out /root/R7C8G_R3_R2_R9.sh
```

The builder is fail-closed: it refuses to run if the R8 hash does not match the
recorded value, if the output already exists, if the injection anchors are not
found exactly once, or if the produced R9 fails `bash -n`.

## Running R9 on the VPS

```
# 1. Build the immutable R9 runner from R8 (verifies R8's hash first)
bash build_R9_from_R8.sh --r8 /root/R7C8G_R3_R2_R8.sh --out /root/R7C8G_R3_R2_R9.sh

# 2. Run it exactly as R8 was run, with the same authorization variables.
#    R9 adds only read-only diagnostics; the surrounding gate is unchanged.
```

## What to send back

The block between these markers is the whole result:

```
R9_RENDERED_COMPOSE_DIAGNOSTICS_BEGIN
...
R9_RENDERED_COMPOSE_DIAGNOSTICS_END
```

The single most important line is `R9_ROOT_CAUSE_CLASS=...`. All environment
values in that block are redacted, so it is safe to paste verbatim.
