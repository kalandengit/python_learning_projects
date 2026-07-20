# AI School Assistant — Planning Package

> **Project:** AI Teacher & Student Assistant ("AI School Assistant")
> **Status:** 📋 PLANNING — awaiting stakeholder approval before any implementation
> **Date:** 2026-07-20
> **Method:** planning-first workflow (analysis → architecture → plan → approval → incremental build)

## What this is

A complete, research-backed planning package for building a production-grade AI assistant
that serves **both teachers and students**. It was produced after analyzing the current
market of AI teaching assistants (Khanmigo, MagicSchool, Eduaide, Brisk, Jill Watson,
and ~20 open-source projects), current LLM benchmarks and pricing (July 2026), and
education-sector safety/compliance requirements.

## Documents

| # | Document | Purpose |
|---|----------|---------|
| 1 | [01_MARKET_RESEARCH.md](01_MARKET_RESEARCH.md) | Landscape analysis, pros/cons of existing tools, gap analysis, positioning |
| 2 | [02_PRD.md](02_PRD.md) | Product Requirements Document — personas, features, non-functional requirements, success metrics |
| 3 | [03_MVP.md](03_MVP.md) | Minimum Viable Product — scope, cut lines, acceptance criteria |
| 4 | [04_ARCHITECTURE.md](04_ARCHITECTURE.md) | System architecture — components, tech stack with trade-offs, security, scalability |
| 5 | [05_WORKFLOWS.md](05_WORKFLOWS.md) | Workflow designs — tutoring loop, grading pipeline, lesson planning, safety escalation |
| 6 | [06_LLM_SELECTION.md](06_LLM_SELECTION.md) | LLM comparison (July 2026), routing strategy, cost model, recommendation |
| 7 | [07_ROADMAP.md](07_ROADMAP.md) | Implementation roadmap & guide — phases, milestones, files preview, approval gate |

## Executive summary (TL;DR)

- **The gap:** existing tools are either *teacher productivity suites* (MagicSchool, Eduaide,
  Brisk) or *student tutors* (Khanmigo) — almost none close the loop between the two.
  Our differentiator: **one platform where the teacher's curriculum grounds the student's
  tutor, and the student's struggles feed the teacher's dashboard.**
- **Product:** a web platform with (a) a teacher workbench — lesson planning, rubric-based
  grading assistance, differentiation; (b) a student Socratic tutor grounded via RAG in the
  teacher's actual course materials; (c) an insight loop — misconception analytics back to
  the teacher. Teacher stays in the loop for anything high-stakes (grades are *drafts* until
  approved).
- **LLM choice (July 2026):** a **routing strategy** on the Claude family — **Claude Sonnet 5**
  as the workhorse (near-Opus quality at $3/$15 per MTok, 1M context), **Claude Opus 4.8**
  for complex generation/grading, **Claude Haiku 4.5** for high-volume classification and
  moderation — behind a thin provider-abstraction layer so Gemini/GPT can be substituted
  per-task. Batch API (−50%) for overnight grading; prompt caching (−90% on reads) for
  per-class curriculum context.
- **MVP (~10 weeks):** auth + class setup, curriculum upload → RAG index, student Socratic
  tutor with guardrails, teacher lesson-plan generator, draft grading on rubrics, basic
  misconception dashboard.
- **Stack:** Python 3.12 / FastAPI backend, Next.js frontend, PostgreSQL + pgvector, Redis,
  Docker; secure by default (OWASP ASVS, least privilege, encryption, FERPA/COPPA-aligned
  data handling).

## ⚠️ Approval gate (planning-first)

Per the project's planning-first policy, **no application code will be written until this
plan is explicitly approved.** Review the documents, then reply with one of:

- ✅ *"Approved / proceed"* — implementation starts at Milestone 0 of [07_ROADMAP.md](07_ROADMAP.md)
- ✏️ *"Change X"* — the plan is revised and re-submitted
