# DECISION_LOG — kalandengit/python_learning_projects

> ADR-style log reconstructed from the repo, git history (7 commits, PRs #1–#6
> referenced in commit messages), and the current development session.
> **[OBSERVED]** = evidenced in code/history; **[INFERRED]** = reasonable
> reconstruction of motivation.

---

## ADR-1: Repurpose the repo as a skills distribution repo

- **Decision [OBSERVED]:** Ship Claude Code skills from a repo originally
  created for Python learning (`68423f6 Initial commit` → `521a035 Add
  it-prompt-specialist Claude Code skill (#1)`).
- **Motivation [INFERRED]:** An existing GitHub repo with access already
  configured was the fastest path to a hosted, shareable skill.
- **Alternatives:** Create a dedicated repo from the start.
- **Trade-offs:** Misleading repo name and leftover Python `.gitignore` /
  placeholder README, in exchange for zero setup friction.
- **Consequences:** The `claude-skills/` bundle + publish script (ADR-4) exist
  partly to escape this: the marketplace can graduate to a clean repo later.

## ADR-2: Skills as pure SKILL.md prompt-content (no code, no hooks)

- **Decision [OBSERVED]:** Each skill is a single Markdown file with YAML
  frontmatter; no scripts, resources, or executable components inside skills.
- **Motivation [INFERRED]:** The source material was ChatGPT system prompts
  (both older skills carry `author: OpenAI`); Markdown-only skills are portable
  across Claude Code local/web and claude.ai chat zip upload.
- **Alternatives:** Skills with bundled scripts/references; Claude Code hooks.
- **Trade-offs:** Behavior is advisory (the model interprets it) rather than
  enforced; but maximal portability and trivial review/diff.
- **Consequences:** Distribution reduces to copying one file per skill, which
  makes the triple-copy strategy (ADR-3) tractable.

## ADR-3: Triple-copy distribution instead of a single source location

- **Decision [OBSERVED]:** Every skill exists in three copies —
  `.claude/skills/` (auto-discovery), `skills/` (standalone + README),
  `claude-skills/plugins/.../skills/` (plugin bundle).
- **Motivation [OBSERVED in READMEs]:** Each copy serves a channel with
  different reach; notably Claude Code on the web cannot load personal
  `~/.claude` skills, so in-repo and marketplace copies are the only paths
  that work there.
- **Alternatives:** Symlinks (not portable through GitHub raw/zip installs);
  build step generating copies (no build tooling exists in this repo);
  single copy + longer install paths.
- **Trade-offs:** Manual 3-way sync (drift risk, mitigated by `diff` checks at
  commit time) in exchange for every channel getting an idiomatic layout.
- **Consequences:** "Add a skill" is a 6-location checklist (see
  business rules in PROJECT_BLUEPRINT.md §7); a CI sync check is the obvious
  future improvement.

## ADR-4: Repo root doubles as a marketplace; bundle stays publishable

- **Decision [OBSERVED]:** `cddb466 Make repo installable as a Claude Code
  plugin marketplace (#6)` added root `.claude-plugin/marketplace.json`
  pointing into `./claude-skills/plugins/...`, while `claude-skills/` keeps its
  own catalog + README + LICENSE and a `publish-claude-skills.sh` force-push
  publisher.
- **Motivation [OBSERVED in script comments/README]:** Immediate installability
  (`/plugin marketplace add kalandengit/python_learning_projects`) without
  waiting for a dedicated repo, while preserving a one-command path to a clean
  standalone `kalandengit/claude-skills` repo.
- **Alternatives:** Publish the standalone repo first; or only the root
  marketplace.
- **Trade-offs:** Two catalogs to keep in sync; `plugin.json` `repository`
  fields already point at the future repo (currently a dangling reference).
- **Consequences:** Users have a working install path today; the standalone
  repo remains an open roadmap item.

## ADR-5: Per-skill installer scripts with managed CLAUDE.md blocks

- **Decision [OBSERVED]:** `scripts/install-<plugin>.sh` writes the skill file
  and maintains a `<!-- BEGIN <skill> (managed) -->…<!-- END -->` section in
  the target repo's `CLAUDE.md`, idempotently (awk in-place block replacement),
  with opt-in `COMMIT=1 PUSH=1` branch workflow.
- **Motivation [INFERRED]:** A skill file alone is discoverable but easy to
  ignore; a CLAUDE.md section actively instructs Claude to apply it. Managed
  markers let re-runs update only their own section, never user content.
- **Alternatives:** Manual copy instructions only; a single multi-skill
  installer.
- **Trade-offs:** One script per skill duplicates scaffolding; acceptable at
  four skills.
- **Consequences:** Two generations now exist (see ADR-6).

## ADR-6: Newer installers fetch SKILL.md from the raw URL instead of embedding

- **Decision [OBSERVED]:** `install-it-prompt-specialist.sh` and
  `install-planning-first.sh` embed the full SKILL.md as a heredoc;
  `install-project-knowledge-exporter.sh` and `install-export-project.sh`
  `curl` it from `raw.githubusercontent.com/.../main/skills/<skill>/SKILL.md`
  (overridable via `RAW_URL`).
- **Motivation [OBSERVED in script comment]:** "single source of truth" —
  embedded copies drift when the canonical skill is updated.
- **Alternatives:** Keep embedding (works offline); git sparse checkout.
- **Trade-offs:** Network dependency at install time and trust in `main`'s
  state, in exchange for zero-drift installs.
- **Consequences:** The two older installers should eventually be converged to
  the fetch pattern (open item).

## ADR-7: Alias skill `export_project` rather than renaming the exporter

- **Decision [OBSERVED]:** A second skill with a byte-identical body and its
  own frontmatter (`name: export_project`) provides the `/export_project`
  command; the descriptive `project-knowledge-exporter` skill remains.
- **Motivation [OBSERVED in this session / SKILL.md blockquote]:** The user
  wanted the short memorable command everywhere; renaming would lose the
  descriptive name and its auto-activation description. The alias file states
  both should be treated as one skill when co-installed.
- **Alternatives:** Rename; a thin pointer skill (rejected [INFERRED]: a
  pointer breaks when installed standalone without its target).
- **Trade-offs:** Yet another set of 3 copies to sync; both skills may appear
  in skill lists together.
- **Consequences:** Underscore skill names were verified working via live
  session discovery before propagation; plugin kept hyphenated name
  (`export-project`) per marketplace convention.

## ADR-8: PR-based workflow on feature branches

- **Decision [OBSERVED]:** Every non-initial commit on `main` references a PR
  (#1, #2, #5, #6); current work rides `claude/*` branches (PR #8).
- **Motivation [INFERRED]:** Review point before content reaches `main`, which
  matters because installers and marketplace adds consume `main` directly.
- **Consequences:** `main` is the de-facto release channel; nothing should be
  merged that isn't ready to be curl'd or plugin-installed.
