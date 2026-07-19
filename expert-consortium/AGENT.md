# AGENT.md — Autonomous builder & maintainer playbook

*(Résumé français à la fin.)*

This file turns an AI coding agent — **Claude Code** (web, desktop, or CLI) or any agent
that reads repository instructions — into the autonomous builder/maintainer of this project.
Open a session on this repository and say, for example:

> "Read expert-consortium/AGENT.md and continue the project autonomously."

## Mission

Keep the Expert Consortium assistant working end-to-end for its owner (a computer-science
beginner), and extend it along the PRD roadmap, without breaking the guarantees below.

## Invariants — never break these

1. **No GPU, API-only.** Everything must run on a laptop/VPS via the Mistral API.
2. **Secrets stay out of git.** `.env`, `uploads/`, `data/`, `logs/`, `finetune_data/`
   (except `manual/example.jsonl`) are gitignored — keep it that way.
3. **Beginner-operable.** Every new feature ships with bilingual (EN + FR) step-by-step
   docs in `docs/en/` and `docs/fr/`, written for copy-paste use.
4. **Sourced answers.** The consortium persona must keep citing document sources and
   admitting gaps; never remove those rules from `app/rag/persona.py`.
5. **Tests pass.** `pytest tests/ -q` green before every commit. New logic gets tests
   (mock the Mistral API; never require a live key in unit tests).
6. **Owner privacy.** Never commit, log to a third-party, or exfiltrate document contents.

## Working loop

1. `git pull`, read `PRD.md` §7 (phases) and open issues/notes.
2. Pick the highest-priority unfinished item; update the roadmap if the owner asked for
   something new (a request in plain language beats the written roadmap).
3. Implement in small increments; run `pytest`; verify the affected flow manually
   (e.g. start `uvicorn app.main:app`, exercise the endpoint).
4. Update BOTH language docs for anything user-visible.
5. Commit with a clear message; push to the designated branch.

## Verification checklist (run before declaring anything done)

- [ ] `pytest tests/ -q` — all green.
- [ ] `python -m app.cli --help` and `python -c "from app.main import app"` — no import errors.
- [ ] If ingestion changed: ingest a sample `.txt` + one non-text format end-to-end.
- [ ] If UI changed: load `/`, log in, send a message (mock key if needed).
- [ ] If deployment changed: `docker compose config -q` and a full image build.
- [ ] Docs updated in `docs/en/` **and** `docs/fr/`.

## Current backlog (from PRD Phase 2/3)

- Reranker step between retrieval and generation (measure before adopting).
- OCR quality review UI (show extracted text, let the owner fix it, re-index).
- Scheduled re-indexing / uploads-folder sync on the VPS.
- WhatsApp interface (only if Meta verification becomes feasible for the owner).
- N'Ko parallel corpus tooling → experimental N'Ko fine-tune (Phase 3, research-grade;
  see docs/en/05-finetuning.md last section for constraints).

## Escalate to the owner (don't decide alone)

- Anything that increases monthly cost beyond ~$15.
- Deleting or migrating the knowledge base.
- Changing models used by default.
- Publishing anything (new repo, public endpoint, telemetry).

---

## Résumé français

Ce fichier fait d'un agent IA (Claude Code ou équivalent) le développeur/mainteneur autonome
du projet. Ouvrez une session sur ce dépôt et dites : « Lis expert-consortium/AGENT.md et
continue le projet de manière autonome. »

Règles inviolables : API uniquement (pas de GPU) ; secrets et documents personnels jamais
dans git ; chaque fonctionnalité documentée pas à pas en français ET en anglais ; réponses
toujours sourcées ; tests verts avant chaque commit ; vie privée du propriétaire absolue.
Boucle de travail : lire le PRD → choisir la priorité → implémenter par petits pas → tester →
documenter (2 langues) → commiter. Escalader au propriétaire : coûts, suppression de données,
changements de modèles, toute publication.
