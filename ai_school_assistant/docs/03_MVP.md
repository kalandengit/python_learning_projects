# 03 — MVP Definition

**Goal of the MVP:** prove the *closed loop* — teacher curriculum → grounded student tutor →
misconception insights → teacher action — with real classes, in ~10 weeks of build time.

## 1. MVP scope (what's IN)

| # | Feature | Why it's in |
|---|---------|-------------|
| 1 | Auth (email + Google SSO), roles: teacher / student / admin | Foundation; class-scoped authorization is the security core |
| 2 | Class management: create class, invite students via code/link | Minimal rostering, no LMS dependency |
| 3 | Curriculum upload (PDF/DOCX/MD) → chunk → embed → per-class RAG index | The grounding layer everything else depends on |
| 4 | **Student Socratic tutor**: streamed chat, class-scoped RAG with citations, hints ladder, answer-leak guard, "still stuck" escalation | The student-side hero feature |
| 5 | **Lesson plan generator**: objectives + grade level + selected materials → structured editable plan | The teacher-side hero feature, fastest time-to-value |
| 6 | **Draft grading**: teacher pastes/uploads rubric + text submissions → per-criterion draft scores with evidence quotes → edit → approve (batch overnight mode) | Highest time-savings claim; draft-only keeps risk low |
| 7 | Misconception dashboard (basic): topic-clustered summary of tutor conversations per class, weekly digest | Closes the loop; can be simple (LLM-summarized clusters) |
| 8 | Safety layer: input/output moderation, jailbreak-resistant system prompts, flag → teacher alert, full transcript visibility | Non-negotiable for minors |
| 9 | Audit log + LLM observability (model, tokens, cost, latency per call) | Compliance + cost control from day one |

## 2. Explicitly OUT of MVP (cut lines)

| Cut | Deferred to | Rationale |
|-----|-------------|-----------|
| Quiz/worksheet generator | v1.1 | Lesson plans prove generation value first |
| Differentiation/re-leveling tools | v1.1 | Depends on generation quality baseline |
| Practice mode & mastery tracking | v1.1 | Tutor first; mastery model needs data |
| LMS integrations (Classroom, Canvas LTI) | v1.2 | Invite codes suffice for pilots |
| Multilingual tutoring | v1.1 | Prompt-level change, but eval burden now |
| Image/handwriting input | v2 | Multimodal pipeline + cost |
| Parent portal, admin analytics console | v2 | Not needed for pilot |
| Mobile apps | v2 | Responsive web covers it |
| Fine-tuning / custom models | v2+ | Routing + prompting + RAG is enough (see 06) |

## 3. MVP user journeys (acceptance criteria)

### Journey A — Teacher sets up (day 1, < 15 min)
1. Sign up with Google → create "Algebra I – Period 3" → get invite code.
2. Upload syllabus PDF + 3 unit PDFs → indexing completes < 5 min with visible status.
3. Generate a lesson plan for "solving linear inequalities" → structured plan (objectives,
   warm-up, direct instruction, practice, exit ticket) citing the uploaded unit → edit → save.
   **AC:** plan references uploaded material by name; generation < 60 s; fully editable.

### Journey B — Student gets help (ongoing)
1. Student joins with code, opens tutor, asks "how do I solve 3x + 5 > 20?".
2. Tutor responds Socratically (asks what they'd do first), cites the class worksheet,
   escalates hint specificity over 3–4 turns, never states "x > 5" while the related
   assignment is active.
   **AC:** first token < 2 s p95; citation shown; answer-leak evals ≤ 1%; "I'm still stuck"
   button files an escalation the teacher sees.

### Journey C — Teacher grades (weekly)
1. Teacher creates assignment with rubric (4 criteria), pastes 28 submissions (or CSV upload).
2. Chooses "overnight batch" → next morning: per-criterion draft scores + evidence quotes +
   suggested comment per student.
3. Teacher adjusts 5, approves all → feedback exported/copied.
   **AC:** batch completes < 8 h; UI diff of teacher edits captured (for quality tracking);
   nothing visible to students until approval.

### Journey D — Loop closes (weekly)
1. Dashboard shows: "12 students struggled with inequality sign flips this week" + 3 example
   anonymized exchanges + suggested re-teach mini-lesson.
   **AC:** digest generated weekly per class; links to transcripts (teacher-only).

## 4. MVP quality gates (must pass before pilot)

- Grounding eval set (≥100 curated Q/A per subject pilot): ≥ 90% supported-by-citation.
- Answer-leak eval set (≥100 adversarial "just give me the answer" prompts incl. jailbreaks): ≤ 1% leak.
- Moderation eval: 0 unsafe outputs on standard red-team suite.
- Rubric-agreement eval: draft scores within 1 point of teacher on ≥ 80% of a 50-submission
  calibration set.
- Load: 200 concurrent tutor chats without p95 latency regression.

## 5. Pilot plan

2–3 friendly teachers, 1 subject (recommend middle-school math or HS English), 4 weeks,
weekly feedback call, kill-switch per feature. Success = Journey A–D all exercised weekly and
teacher states they'd keep using it.
