# 02 — Product Requirements Document (PRD)

**Product:** AI School Assistant — an integrated AI teacher & student assistant
**Version:** 1.0 (planning) · **Date:** 2026-07-20 · **Status:** awaiting approval

---

## 1. Problem statement

Teachers lose 10–15 h/week to planning, grading, and differentiation. Students get either no
individual help or unsupervised general chatbots that hand out answers, ignore the class
curriculum, and create academic-integrity risk. No mainstream tool closes the loop between
teacher materials, student tutoring, and learning analytics.

## 2. Goals & non-goals

**Goals**
1. Cut teacher time on planning/grading/differentiation by ≥40% while keeping the teacher in
   control of every high-stakes output.
2. Give every student a 24/7 Socratic tutor grounded in *their class's* actual materials.
3. Surface actionable learning analytics (misconceptions, at-risk signals) to teachers.
4. Be deployable in real schools: FERPA/COPPA-aligned, auditable, affordable at scale.

**Non-goals (v1)**
- Not an LMS replacement (we integrate/export; Google Classroom/Canvas remain systems of record).
- No autonomous grade release — AI grades are always drafts.
- No proctoring/surveillance features.
- No native mobile apps (responsive web only).
- No fine-tuned/custom models in v1 (prompting + RAG + routing).

## 3. Personas

| Persona | Needs | Key jobs-to-be-done |
|---------|-------|---------------------|
| **Teacher (primary)** | Save time, keep control, trust outputs | Plan lessons; grade with rubrics; differentiate; monitor students |
| **Student (primary)** | Understand, not just finish | Get unstuck on homework; practice; prepare for tests — without being handed answers |
| **School admin (secondary)** | Compliance, cost, adoption | Provision accounts, review audit logs, manage data agreements |
| **Parent (tertiary, later)** | Visibility | Progress summaries (post-MVP) |

## 4. Functional requirements

Priority: **P0** = MVP, **P1** = v1.x, **P2** = later.

### 4.1 Teacher Workbench
| ID | Requirement | Priority |
|----|-------------|----------|
| T1 | Create classes; invite/roster students; assign roles | P0 |
| T2 | Upload curriculum materials (PDF, DOCX, PPTX, MD, links) → indexed for RAG | P0 |
| T3 | Generate lesson plans from objectives + standards + uploaded materials, editable before save | P0 |
| T4 | Generate quizzes/worksheets aligned to uploaded materials, with answer keys | P1 |
| T5 | Rubric-based **draft** grading of text submissions: per-criterion score, evidence quotes, suggested feedback; teacher edits & approves | P0 |
| T6 | Differentiation: re-level any material (reading level, language, scaffolding, extension) | P1 |
| T7 | Misconception dashboard: clustered student struggles per topic, suggested re-teach actions | P0 (basic) |
| T8 | Tutor policy controls per class/assignment: strictness, allowed topics, off/on windows | P1 |
| T9 | Full transcript access to their students' tutor conversations | P0 |
| T10 | Export artifacts (PDF/DOCX/Google Docs) | P1 |

### 4.2 Student Tutor
| ID | Requirement | Priority |
|----|-------------|----------|
| S1 | Chat tutor scoped to enrolled classes, grounded (RAG) in class materials with citations | P0 |
| S2 | Enforced Socratic pedagogy: guiding questions, hints ladder, worked examples — never direct final answers to active assignments | P0 |
| S3 | Answer-leak guard: output filter blocks verbatim solutions to active assessment items | P0 |
| S4 | Mastery check-ins: tutor asks the student to explain back; logs mastery signal | P1 |
| S5 | "I'm still stuck" → escalation note queued to teacher | P0 |
| S6 | Practice mode: generated practice problems with step-by-step feedback | P1 |
| S7 | Multilingual support (student may chat in home language) | P1 |
| S8 | Image input (photo of handwritten problem) | P2 |

### 4.3 Platform & safety
| ID | Requirement | Priority |
|----|-------------|----------|
| P1 | AuthN/AuthZ: email+SSO (Google), roles teacher/student/admin, class-scoped access | P0 |
| P2 | Input & output moderation (self-harm, harassment, jailbreak attempts); age-appropriate persona | P0 |
| P3 | Safety escalation: flagged conversations alert teacher/admin within 5 min | P0 |
| P4 | Audit log of all AI outputs and approvals (who/what/when/model/version) | P0 |
| P5 | Data controls: no student data used for model training; retention policy; delete-on-request | P0 |
| P6 | Admin console: org setup, usage & cost reporting | P1 |
| P7 | LMS integration (Google Classroom import/export; Canvas LTI) | P2 |

## 5. Non-functional requirements

| Category | Requirement |
|----------|-------------|
| **Latency** | First streamed token < 2 s p95 for tutor chat; full lesson plan < 60 s |
| **Availability** | 99.5% (v1), graceful degradation if LLM provider down (fallback model/provider) |
| **Scale target** | v1: 50 schools ≈ 2,000 teachers / 30,000 students; architecture must not preclude 10× |
| **Security** | OWASP ASVS L2; TLS everywhere; AES-256 at rest; secrets in a secrets manager; least-privilege IAM; dependency scanning in CI |
| **Privacy/compliance** | FERPA-aligned (school owns data, we're "school official"); COPPA (<13 via school consent); GDPR-ready (EU later); DPA template; PII minimization & pseudonymized analytics |
| **Cost** | ≤ $1.50 per student-month LLM spend at target usage (see 06_LLM_SELECTION cost model) |
| **Accessibility** | WCAG 2.1 AA |
| **Observability** | Structured logs, traces on every LLM call (prompt/version/model/tokens/cost), eval dashboards |
| **Quality** | Automated eval suite (grounding accuracy, answer-leak rate, rubric agreement vs teacher) gating releases |

## 6. Success metrics

| Metric | Target (6 months post-launch) |
|--------|-------------------------------|
| Teacher weekly active / registered | ≥ 60% |
| Self-reported teacher hours saved | ≥ 4 h/week median |
| Draft-grade acceptance rate (approved w/ minor edits) | ≥ 75% |
| Tutor grounding accuracy (evals: answer supported by cited material) | ≥ 90% |
| Answer-leak rate on active assignments (evals) | ≤ 1% |
| Safety flags triaged < 5 min | ≥ 99% |
| LLM cost per student-month | ≤ $1.50 |

## 7. Assumptions & open questions

**Assumptions:** English-first launch; text submissions only for grading v1; schools provide
consent under FERPA "school official" exception; LLM APIs remain available at July-2026 pricing.

**Open questions for stakeholder (do not block MVP start):**
1. Initial target segment: middle/high school (recommended — COPPA simpler ≥13) vs. elementary?
2. Deployment preference: managed cloud (recommended) vs. district on-prem option later?
3. Monetization: per-school license vs. freemium teacher tool? (Affects admin console priority.)

## 8. Constraints

- Solo/small-team build → managed services over self-hosted infra wherever safe.
- Budget-conscious: start on one region, one cloud, no Kubernetes until scale demands it.
- All AI features must degrade gracefully to "manual mode" (the app remains a useful
  planner/gradebook shell if the LLM is unavailable).
