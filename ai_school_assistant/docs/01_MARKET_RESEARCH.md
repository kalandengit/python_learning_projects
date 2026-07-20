# 01 — Market Research & Landscape Analysis

*Research date: July 2026. Sources listed at the bottom.*

## 1. Why this product category exists

Teachers report spending **10–15 hours/week** on non-teaching work: lesson planning, grading,
differentiation, parent communication, admin. Students increasingly get unsupervised help from
general chatbots (ChatGPT, Gemini) that will happily *give answers* instead of *teaching*, are
not grounded in the class curriculum, and give teachers zero visibility. The U.S. Department of
Education's AI report and EdWeek's reliability coverage both stress the same two requirements:
**human-in-the-loop oversight** and **grounding in vetted instructional materials**.

## 2. Landscape: the three clusters

### Cluster A — Teacher productivity suites
Tools that generate teaching artifacts (lesson plans, quizzes, rubrics, IEP language, parent emails).

| Tool | Strengths | Weaknesses |
|------|-----------|------------|
| **MagicSchool AI** | 80+ generator tools, big K-12 adoption, LMS exports, teacher-friendly UX | Shallow generators (template-fill), no student-side loop in base product, quality varies by tool |
| **Eduaide.ai** | Strong instructional-design framing (learning objectives, UDL), good free tier | Content generation only; no grading pipeline, no student data loop |
| **Brisk Teaching** | Chrome-extension "works where teachers work" (Docs/Slides), feedback-on-writing | Extension-bound; limited grounding in class materials; feedback not rubric-anchored |
| **Diffit / Curipod** | Leveled reading passages / interactive slides | Single-purpose |
| **Alayna / Teacher AI / Goeddie** | Niche assistants (LMS integration, planning) | Small feature surface, limited moats |

**Cluster pros:** immediate time savings, low risk (teacher reviews everything), easy adoption.
**Cluster cons:** no connection to what students actually do; outputs not grounded in the
teacher's own curriculum; "generator sprawl" (80 shallow tools instead of 5 deep workflows).

### Cluster B — Student-facing tutors
| Tool | Strengths | Weaknesses |
|------|-----------|------------|
| **Khanmigo (Khan Academy)** | Best-in-class Socratic pedagogy (guides, doesn't answer), safety guardrails, teacher visibility into chats, low cost | Locked to Khan Academy content; weak on teacher-authored curriculum; math-centric |
| **Code.org AI TA** | Free, CS-specific, grading assistance for code | Domain-limited |
| **Generic chatbots (ChatGPT/Gemini used by students)** | Free, capable | Gives answers not learning; no grounding; no oversight; academic-integrity risk |

**Cluster pros:** 24/7 individualized help; Socratic prompting demonstrably works when enforced.
**Cluster cons:** content lock-in; teachers can't inject their own materials; analytics thin.

### Cluster C — Academic / open-source (validation of architecture)
- **Jill Watson (Georgia Tech)** — the canonical research TA: RAG grounded in course
  documents (syllabus, lectures), answered student Q&A across multiple course offerings with
  published results (Springer AIED papers). Validates: *document-grounded QA + skill-based
  routing + refusal when out of scope* is the right technical core.
- **GitHub projects** (VirtuTA, learning-buddy, Gen-AI-Teaching-Assistant, aimathtutor,
  steacher, Spark-IQ, TAi, arete, ai_tutor, ShikshaVaani…) — consistent pattern across ~20
  repos: **FastAPI/Flask + vector DB + LLM API + chat UI**. None ship the safety layer,
  compliance posture, or teacher-student loop needed for real school deployment — this is
  precisely where an open project can differentiate.

## 3. Pros/cons of building vs. adopting

| Option | Pros | Cons |
|--------|------|------|
| Adopt MagicSchool + Khanmigo | Fast, proven | Two silos, no shared data, per-seat cost, no curriculum grounding for tutor |
| Build on a raw chatbot | Cheapest | Unsafe for minors, answer-giving, no analytics, integrity risk |
| **Build integrated platform (this plan)** | Closed teacher↔student loop, own data, curriculum-grounded, tailored pedagogy | Engineering cost, compliance burden, must reach quality bar |

## 4. Gap analysis → our positioning

The differentiators no incumbent covers together:

1. **Closed loop:** teacher uploads curriculum → tutor is grounded in it → student struggles
   are mined into misconception analytics → teacher gets targeted re-teach suggestions.
2. **Rubric-anchored draft grading** with teacher approval (grades never auto-released).
3. **Pedagogy-enforced tutoring** (Socratic, mastery-checked, integrity-aware) on *teacher's
   own materials*, not a fixed content library.
4. **Compliance-first**: FERPA/COPPA-aligned data handling, audit logs, no training on
   student data — a hard requirement for district procurement that most GitHub projects and
   several startups ignore.

## 5. Key risks learned from the market

| Risk | Evidence | Mitigation carried into PRD |
|------|----------|------------------------------|
| Hallucinated feedback/grades | EdWeek "Are AI teacher assistants reliable?" (2025) | Draft-only grading, citations to rubric+submission, confidence flags |
| Answer-giving defeats learning | Khanmigo design rationale; HBS "Let ChatGPT be your TA" | Enforced Socratic policy + answer-leak detector on output |
| Student safety incidents | District procurement checklists | Moderation on input/output, escalation workflow, age gates |
| Teacher distrust / rubber-stamping | Ed.gov AI report | Explainable outputs, easy edit-before-approve UX, opt-out per assignment |
| Cost blow-up at scale | Per-seat pricing pain in Cluster A | Model routing + caching + batch (see 06_LLM_SELECTION) |

## Sources

- [Best AI Teaching Assistant Tools for Educators (Educators Technology)](https://www.educatorstechnology.com/2025/06/top-ai-teaching-assistants.html)
- [10+ Best AI Teaching Tools (Edcafe AI)](https://www.edcafe.ai/blog/best-ai-teaching-tools)
- [7 Best AI Tools for Lesson Plan Generation in 2026 (Forasoft)](https://www.forasoft.com/blog/article/automated-lesson-plan-generation-software)
- [Khanmigo vs MagicSchool comparison](https://a2zai.space/khanmigo-vs-magic-school)
- [16 Best AI Tools For Teachers (OfficeChai)](https://officechai.com/learn/ai-tools-for-teachers/)
- [Khanmigo](https://www.khanmigo.ai/) · [Eduaide](https://www.eduaide.ai/) · [Alayna](https://www.alayna.ai/) · [Code.org AI TA](https://code.org/en-US/artificial-intelligence/teaching-assistant)
- [Jill Watson — multimodal document-grounded AI (Georgia Tech)](https://krntneja.github.io/projects/multimodal-document-grounded-ai/) and [Springer AIED chapter](https://link.springer.com/chapter/10.1007/978-3-031-63028-6_7)
- [U.S. Dept. of Education — AI Report (PDF)](https://www.ed.gov/sites/ed/files/documents/ai-report/ai-report.pdf)
- [EdWeek — Are AI teacher assistants reliable?](https://www.edweek.org/technology/are-ai-teacher-assistants-reliable-what-to-know/2025/08)
- GitHub reference implementations: [VirtuTA](https://github.com/KayvanShah1/VirtuTA/), [teaching-assistant](https://github.com/DHRUVvkdv/teaching-assistant), [learning-buddy](https://github.com/Rahilyw/learning-buddy), [aimathtutor](https://github.com/gregor-dietrich/aimathtutor), [topic: ai-teaching-assistant](https://github.com/topics/ai-teaching-assistant)
