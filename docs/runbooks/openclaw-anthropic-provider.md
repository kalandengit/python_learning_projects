# Runbook — Add Anthropic (Claude subscription) as a second model provider in OpenClaw

**Target:** OpenClaw gateway on the VPS, container `openclaw-openclaw-gateway-1`.
**Goal:** Add Claude as a *selectable alternative* while `openai/gpt-5.6-sol` stays the default.
**Non-goals:** no changes to WhatsApp config, allowlists, `tools.deny`, dashboard controls, or any unrelated setting.

> **Secret handling.** The Anthropic setup token is a long-lived credential scoped to Claude Code.
> Never paste it into a chat transcript, never pass it as a command-line argument (it lands in
> `~/.bash_history` and in `/proc/<pid>/cmdline`), and never write it to a file in a repo or workspace.
> Every command below takes the token via an interactive prompt or stdin only.

---

## 0. Prerequisites

Run on the workstation that has a browser (the Windows box):

```bash
claude setup-token
```

This prints a long-lived token. Copy it to the clipboard. Do not save it to a file, do not echo it
into any chat, and clear the clipboard when you are done.

---

## 1. Connect to the VPS

```bash
ssh -i "C:\Users\maitinnin\.ssh\codex_openclaw_deploy_ed25519" root@172.105.4.195
```

If an older OpenClaw auth prompt is still open in another terminal, abandon it. Do not paste the
token into a prompt you cannot see the provenance of — start a fresh command per step 4.

---

## 2. Record the pre-change state (so the verification in step 6 has a baseline)

```bash
docker exec openclaw-openclaw-gateway-1 openclaw config get agents.defaults.model --json
docker exec openclaw-openclaw-gateway-1 openclaw config get channels.whatsapp.dmPolicy --json
docker exec openclaw-openclaw-gateway-1 openclaw config get channels.whatsapp.groups --json
docker exec openclaw-openclaw-gateway-1 openclaw config get tools.deny --json
docker exec openclaw-openclaw-gateway-1 openclaw models status
docker exec openclaw-openclaw-gateway-1 openclaw models auth list --json
```

`models auth list` never prints token, API-key, or OAuth secret material, so it is safe to read.

---

## 3. Back up the configuration

```bash
TS=$(date -u +%Y%m%dT%H%M%SZ)
docker exec openclaw-openclaw-gateway-1 sh -c \
  "cp -a /root/.openclaw/openclaw.json /root/.openclaw/openclaw.json.bak.$TS"

# Copy the backup and the agent auth store off the container as well.
mkdir -p ~/openclaw-backups/$TS
docker cp openclaw-openclaw-gateway-1:/root/.openclaw ~/openclaw-backups/$TS/dot-openclaw
chmod -R go-rwx ~/openclaw-backups/$TS
```

The copied directory contains `openclaw-agent.sqlite`, which holds credentials — keep the `chmod`,
and do not commit it anywhere.

---

## 4. Read the help before choosing the command

```bash
docker exec openclaw-openclaw-gateway-1 openclaw models auth --help
docker exec openclaw-openclaw-gateway-1 openclaw models auth setup-token --help
docker exec -it openclaw-openclaw-gateway-1 openclaw --version
```

Confirm the installed build exposes `setup-token` before running it; the subcommand set varies by
version. Upstream documents these auth subcommands:

```
openclaw models auth add
openclaw models auth list [--provider <id>] [--json]
openclaw models auth login --provider <id> [--method <id>] [--profile-id <id>] [--set-default] [--force]
openclaw models auth paste-api-key --provider <id>
openclaw models auth setup-token --provider <id>
openclaw models auth paste-token --provider <id>
openclaw models auth logout <profileId> [--yes]
openclaw models auth order get|set|clear --provider <id>
```

---

## 5. Add the Anthropic setup token

`setup-token` requires an interactive TTY — hence `docker exec -it` — and runs the provider's
token-auth method. Note the deliberate absence of `--set-default`: omitting it is what keeps
`openai/gpt-5.6-sol` as the default model.

```bash
docker exec -it openclaw-openclaw-gateway-1 \
  openclaw models auth setup-token --provider anthropic
```

Paste the token at the prompt. It is not echoed and does not enter shell history.

**Fallback** if this build has no `setup-token` method for `anthropic`: `paste-token` prompts for
the value by default and accepts an expiry, since Anthropic setup tokens are time-limited.

```bash
docker exec -it openclaw-openclaw-gateway-1 \
  openclaw models auth paste-token --provider anthropic --expires-in 365d
```

Adding provider auth does **not** rewrite `agents.defaults.model.primary`. The default only changes
if you pass `--set-default` or run `openclaw models set` — so do neither.

### Restart

Not required. The gateway watches `~/.openclaw/openclaw.json` and hot-reloads it (default reload
mode `hybrid`), and auth profiles live in the agent SQLite store rather than in a file that needs a
process restart. If `openclaw config set` ever prints `Restart the gateway to apply.`, stop and
re-evaluate before restarting — a restart drops the WhatsApp session.

---

## 6. Make a Claude model selectable

List what the account actually exposes, then confirm the exact ref:

```bash
docker exec openclaw-openclaw-gateway-1 openclaw models list --provider anthropic
```

Pick a current Claude model from that output (e.g. an `anthropic/claude-opus-*` or
`anthropic/claude-sonnet-*` ref). **No config change is needed** for it to be selectable, unless
`agents.defaults.modelPolicy.allow` is a non-empty allowlist. Check:

```bash
docker exec openclaw-openclaw-gateway-1 openclaw config get agents.defaults.modelPolicy.allow --json
```

- Empty / unset → every model is selectable; you are done, do not touch config.
- Non-empty → it is an allowlist, and Claude must be added to it. This is the *only* config write in
  this runbook. Dry-run first:

```bash
docker exec openclaw-openclaw-gateway-1 \
  openclaw config set agents.defaults.modelPolicy.allow '["openai/*","anthropic/*"]' --dry-run
```

Re-run without `--dry-run` once the diff shows only that key changing, preserving every entry that
was already in the list.

---

## 7. Verify — without displaying secrets

```bash
# Anthropic auth present; OpenAI auth still present. No secret material is printed.
docker exec openclaw-openclaw-gateway-1 openclaw models auth list --json
docker exec openclaw-openclaw-gateway-1 openclaw models status

# Machine-readable health gate: exit 1 = expired/missing, 2 = expiring.
docker exec openclaw-openclaw-gateway-1 openclaw models status --check; echo "exit=$?"

# Both providers selectable.
docker exec openclaw-openclaw-gateway-1 openclaw models list --provider openai
docker exec openclaw-openclaw-gateway-1 openclaw models list --provider anthropic

# Default model unchanged — must still be openai/gpt-5.6-sol.
docker exec openclaw-openclaw-gateway-1 openclaw config get agents.defaults.model --json

# Guardrails unchanged (compare against the step-2 baseline).
docker exec openclaw-openclaw-gateway-1 openclaw config get channels.whatsapp.dmPolicy --json
docker exec openclaw-openclaw-gateway-1 openclaw config get channels.whatsapp.groups --json
docker exec openclaw-openclaw-gateway-1 openclaw config get tools.deny --json

# Container health.
docker inspect -f '{{.State.Status}} {{.State.Health.Status}}' openclaw-openclaw-gateway-1
docker exec openclaw-openclaw-gateway-1 openclaw doctor
```

> **Do not run `openclaw models status --probe`.** A direct probe run needs exclusive ownership of
> the state directory and upstream instructs you to `openclaw gateway stop` first. That would drop
> the WhatsApp connection. The read-only checks above are sufficient.

---

## 8. Switching between OpenAI and Claude

**In chat** (`/model`; `-s` session only, `-a` also the agent default, `-g` also the global default —
the default-writing scopes need owner/admin authority):

```
/model list
/model anthropic/claude-opus-4-6 -s     # switch this session to Claude
/model openai/gpt-5.6-sol -s            # switch this session back to OpenAI
/model default                          # clear a session pin, fall back to the configured default
```

Substitute the exact Claude ref that `openclaw models list --provider anthropic` reported.

**From the CLI** — this rewrites the persistent default, so use it only if you intend to change it:

```bash
docker exec openclaw-openclaw-gateway-1 openclaw models set anthropic/<model>
docker exec openclaw-openclaw-gateway-1 openclaw models set openai/gpt-5.6-sol   # restore
```

---

## 9. Rollback

```bash
docker exec -it openclaw-openclaw-gateway-1 openclaw models auth list --provider anthropic
docker exec -it openclaw-openclaw-gateway-1 openclaw models auth logout anthropic:<profileId> --yes
```

`logout` also drops the profile from `auth.profiles` and from every `auth.order` list, leaving no
stale reference. If a config key was changed in step 6, restore `openclaw.json` from the step-3
backup and let hot reload pick it up.

---

## References

- [OpenClaw — Gateway authentication](https://github.com/openclaw/openclaw/blob/main/docs/gateway/authentication.md)
- [OpenClaw — `openclaw models` CLI reference](https://github.com/openclaw/openclaw/blob/main/docs/cli/models.md)
- [OpenClaw — Model providers](https://github.com/openclaw/openclaw/blob/main/docs/concepts/model-providers.md)
- [OpenClaw — Models concept and `/model`](https://github.com/openclaw/openclaw/blob/main/docs/concepts/models.md)
- [OpenClaw — Configuration and hot reload](https://github.com/openclaw/openclaw/blob/main/docs/gateway/configuration.md)
