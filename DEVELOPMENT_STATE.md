# DEVELOPMENT_STATE — kalandengit/python_learning_projects

> Snapshot taken 2026-07-12 on branch
> `claude/project-knowledge-exporter-skills-15hrzl` (PR #8, open at export
> time). **[OBSERVED]** / **[INFERRED]** labels as in the blueprint.

## Completed work [OBSERVED]

- **4 skills shipped through all 3 channels:** `it-prompt-specialist` (PR #1),
  `planning-first` (PR #5), `project-knowledge-exporter` and its
  `/export_project` alias (PR #8, this branch).
- **Marketplace live in-repo** (PR #6): `/plugin marketplace add
  kalandengit/python_learning_projects` works against `main` for the first two
  skills, and will cover all four once PR #8 merges.
- **4 idempotent installer scripts** + the `claude-skills` bundle publisher.
- **CLAUDE.md** instructs Claude on all four skills (three sections under
  managed markers).
- **Docs:** per-skill READMEs under `skills/`, marketplace README under
  `claude-skills/` (table, install commands, layout), claude.ai zip-upload
  instructions in `skills/export_project/README.md`.
- **Verification practice established:** JSON `json.load` checks, `bash -n` on
  scripts, `diff` across the three copies of each SKILL.md, live skill
  auto-discovery confirmed in-session for the underscored name.

## In flight [OBSERVED]

- **PR #8** (`claude/project-knowledge-exporter-skills-15hrzl` → `main`): adds
  the exporter skill + `/export_project` alias across all channels. This
  knowledge package itself is being committed to that branch.

## Remaining work / missing features

- **Publish the standalone `kalandengit/claude-skills` repo [OBSERVED gap]:**
  `plugin.json` `repository` fields and `claude-skills/README.md` already
  reference it; the publish script is ready; the repo has not been observed to
  exist. Until then the only valid marketplace add is
  `kalandengit/python_learning_projects`.
- **Resolve the license conflict [OBSERVED]:** root `LICENSE` = GPLv3;
  `claude-skills/LICENSE`, all four `plugin.json`, and every skill README =
  MIT. Pick one (MIT is the majority and the stated intent everywhere except
  the root file [INFERRED]).
- **Real root `README.md` [OBSERVED]:** currently the single line
  `# python_learning_projects`; should present the marketplace, the skills
  table, and install commands (content can be adapted from
  `claude-skills/README.md`).
- **`.gitignore` cleanup [OBSERVED]:** Python-template ignores in a repo with
  no Python.
- **Converge installers [OBSERVED]:** migrate the two heredoc-embedding
  installers (`it-prompt-specialist`, `planning-first`) to the raw-URL fetch
  pattern used by the newer two.

## Known bugs

- None observed in the shipped content. Note: none of the installer scripts
  have been executed end-to-end against a third-party repo in this session
  [OBSERVED — only `bash -n` syntax checks were run]; treat first real runs as
  smoke tests.

## Technical debt

1. **3-way SKILL.md duplication with manual sync** — no CI guard; a drifted
   copy would ship silently. Highest-value fix: a GitHub Action that fails if
   `diff` across the three copies of any skill fails or any JSON doesn't parse.
2. **Dual marketplace catalogs** (root + bundle) that must be edited in pairs.
3. **Dangling `claude-skills` repo references** (see remaining work).
4. **License contradiction** (see remaining work).
5. **Two installer generations** (embedded vs fetched).

## Risks

- **`main` is the release channel:** raw-URL installers and marketplace adds
  consume `main` directly; a bad merge immediately affects installs. Mitigated
  by the PR-only workflow, not by CI [OBSERVED: no CI exists].
- **Skill behavior is advisory:** skills are prompt content; Claude's
  adherence can vary by model/version. [INFERRED] Periodically re-test skill
  activation (the session skill list) after Claude Code updates.
- **`publish-claude-skills.sh` force-pushes** the target repo's `main`;
  running it against the wrong remote is destructive. It expects a pre-created
  empty repo.
- **claude.ai chat installs differ:** the zip-uploaded skill cannot explore a
  repo; users must attach/connect project files. Documented in
  `skills/export_project/README.md`, but a support question magnet [INFERRED].

## Unknowns (not determinable from the repo)

- Whether the GitHub repo is public or private (affects raw-URL installers and
  `/plugin marketplace add` for other users).
- Whether PRs #3, #4, #7 existed and what they contained (gaps in the PR
  number sequence; possibly closed unmerged or issues).
- Original Python learning content, if any ever existed (history starts with
  an empty-ish initial commit).

## Suggested next steps (priority order) [INFERRED]

1. Merge PR #8, then re-test `/plugin install export-project@kalandengit-skills`
   from a clean project.
2. Fix the license conflict and root README (small, user-facing).
3. Add the CI sync/validity check (protects the release channel).
4. Publish `kalandengit/claude-skills` and verify the `plugin.json` links.
