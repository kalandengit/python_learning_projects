# Product Requirements Document (PRD) — Expert Consortium

*Version 1.0 — 2026-07-18 — (Résumé en français à la fin)*

## 1. Problem statement

Kalan works across four knowledge domains — **law & courts**, **N'Ko writing**,
**Islamic sciences in Arabic**, and **computer science** — with knowledge scattered across
PDFs, Word files, images, audio recordings, and videos. General-purpose chatbots do not know
these personal documents, handle Arabic sources inconsistently, and have essentially no N'Ko
capability. Kalan has no GPU and is a beginner in computer science, so any solution must be
API-based and documented step by step.

## 2. Goals

| # | Goal | Success metric |
|---|------|----------------|
| G1 | Ingest any personal file (PDF, DOCX, TXT, MD, images, audio, video) into a searchable knowledge base | A dropped file is queryable within minutes, no manual conversion |
| G2 | Chat with a "Multi-Expert Consortium" persona that answers **from the user's documents, with citations** | Every factual answer names its source file |
| G3 | Access from browser **and** Telegram | Both interfaces hit the same knowledge base |
| G4 | Build a personalized fine-tuned Mistral model from real usage | One-command dataset export + fine-tune job launch |
| G5 | Run on a cheap cloud server (~€5–10/mo) with no GPU | `docker compose up` on a fresh VPS works by following the guide |
| G6 | Fully usable by a computer-science beginner | Bilingual (FR/EN) step-by-step docs for every feature |

## 3. Non-goals (v1)

- **Fluent N'Ko text generation.** No 2026 frontier model generates reliable N'Ko. v1 stores,
  searches, and retrieves N'Ko documents; N'Ko generation is a Phase-3 research experiment
  (requires building a parallel corpus first).
- WhatsApp integration (Meta business verification is heavy; Telegram covers mobile).
- Multi-user accounts. This is a personal single-user system with one shared password.
- Real-time / streaming voice conversation.

## 4. Users

One primary user (owner). Beginner level: every workflow must work by copy-pasting documented
commands. Interfaces: web page (desktop) and Telegram (mobile).

## 5. Functional requirements

**FR-1 Ingestion.** Watch `uploads/` folder + web upload + Telegram upload. Route by type:
PDF/images → Mistral OCR 4; DOCX/TXT/MD → local parsing; audio (mp3, wav, m4a, ogg) →
Voxtral transcription; video (mp4, mkv, webm) → ffmpeg audio extraction → Voxtral.
Each document gets metadata: `domain` (law | nko | islamic | cs | general — auto-suggested,
user-overridable), `language`, `source_file`, `ingested_at`.

**FR-2 Indexing.** Structure-aware chunking (~512 tokens, 15 % overlap, split on headings/
paragraphs) → `mistral-embed` dense vectors + BM25 sparse vectors → Qdrant collection with
payload metadata. Re-ingesting the same file replaces its chunks (no duplicates).

**FR-3 Retrieval.** Hybrid query (dense + sparse, Reciprocal Rank Fusion), top-20 candidates
→ top-6 context chunks, optional domain filter, each chunk carries its citation.

**FR-4 Chat.** Mistral chat model with consortium system prompt (4 named experts, cites
sources as [filename], says "I don't have this in your documents" instead of inventing).
Conversation history within a session. Every exchange appended to a local JSONL log.

**FR-5 Interfaces.** (a) Web: single chat page, password-protected, file upload, domain
filter, FR/EN labels, sources shown under each answer. (b) Telegram: private bot, answers
questions, accepts document/audio uploads, restricted to the owner's Telegram user ID.

**FR-6 Fine-tuning.** `dataset` command builds train/eval JSONL from curated chat logs +
manual Q&A files; `train` command uploads and launches a Mistral fine-tuning job; `evaluate`
command compares base vs fine-tuned answers on a held-out set. Chat can switch to the
fine-tuned model via config.

## 6. Non-functional requirements

- **Security:** API keys only in `.env` (gitignored); web UI password; Telegram allowlist;
  no document content ever committed to git; HTTPS via Caddy in deployment.
- **Cost:** development on Mistral free Experiment tier; personal production use target
  < $10/mo API + €5–9/mo VPS. See docs/en/07-costs.md.
- **Reliability:** ingestion failures are logged per-file and never crash the pipeline;
  all Mistral calls have retry with backoff.
- **Portability:** identical behavior locally (embedded Qdrant, no Docker needed) and on a
  VPS (Docker Compose).
- **Maintainability:** typed Python, pytest suite, one module per concern.

## 7. Phases

- **Phase 1 (this build):** ingestion + RAG chat + web UI + Telegram + fine-tuning pipeline
  + VPS deployment. ← MVP
- **Phase 2:** reranker model, OCR quality review UI, scheduled re-indexing, WhatsApp.
- **Phase 3 (research):** N'Ko generation — collect parallel N'Ko corpus from ingested
  documents, fine-tune with it, evaluate with native-speaker review.

## 8. Key decisions & rationale

| Decision | Why |
|----------|-----|
| Mistral end-to-end (OCR, Voxtral, embed, chat, fine-tune) | One API key, one bill, best-in-class Arabic OCR, API fine-tuning without GPU |
| RAG as backbone, fine-tuning as enhancement | Knowledge lives in documents that change; fine-tuning shapes style/behavior and needs data RAG usage generates |
| Qdrant | Hybrid search + rich metadata filters (legal queries), embedded mode for laptops, Docker for VPS |
| Telegram over WhatsApp | Free, 5-minute setup, no business verification |
| FastAPI + vanilla JS page | Minimal moving parts for a beginner to operate |

---

# Résumé en français

**Problème :** les connaissances de Kalan (droit, N'Ko, sciences islamiques en arabe,
informatique) sont dispersées dans des PDF, Word, images, audios et vidéos. Les chatbots
généralistes ne connaissent pas ces documents personnels et ne gèrent pas le N'Ko.

**Solution :** un assistant personnel basé sur l'API Mistral (sans GPU) : dépôt de fichiers →
OCR/transcription automatique → base de connaissances Qdrant → chat « Consortium
Multi-Experts » avec citations, sur navigateur et Telegram → les meilleures conversations
alimentent un fine-tuning Mistral personnalisé → déploiement sur un VPS à ~5 €/mois.

**Hors périmètre v1 :** génération de texte N'Ko fluide (aucun modèle 2026 n'en est capable —
objectif de recherche Phase 3), WhatsApp, multi-utilisateurs.

**Critère de succès :** chaque fonctionnalité utilisable par un débutant en copiant-collant
les commandes des guides bilingues, réponses toujours sourcées, coût < 15 €/mois au total.
