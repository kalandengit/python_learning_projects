# 05 — Workflow Designs

The five core workflows. Diagrams are Mermaid (render on GitHub).

## 1. Student tutoring loop (Socratic, grounded, guarded)

```mermaid
flowchart TD
    A[Student message] --> B{Input moderation<br/>Haiku + rules}
    B -- unsafe --> Z1[Block + supportive message<br/>+ escalation event]
    B -- pass --> C[Class-scoped RAG retrieval<br/>top-6 chunks + citations]
    C --> D[Tutor generation - Sonnet 5<br/>Socratic policy + hint-ladder state]
    D --> E{Output guards}
    E -- answer leak --> D2[Regenerate at stricter hint level<br/>max 2 retries → fallback hint]
    E -- unsafe --> Z1
    E -- pass --> F[Stream to student<br/>with citations]
    F --> G{Student action}
    G -- continues --> A
    G -- "I'm still stuck" --> H[Escalation queued<br/>teacher notified]
    G -- ends session --> I[Session summarizer - Haiku<br/>topic, misconception tags,<br/>mastery signal → analytics store]
```

**Hint-ladder state machine** (per problem, stored in session):
`L1 probe question → L2 concept reminder + citation → L3 analogous worked example →
L4 first-step scaffold → (never) final answer while assignment active`.
Ladder resets per problem; teacher policy can cap the max level.

## 2. Draft grading pipeline (batch, human-in-the-loop)

```mermaid
flowchart LR
    A[Teacher: rubric +<br/>N submissions] --> B[Job enqueued<br/>arq worker]
    B --> C[Batch API request<br/>Opus 4.8, 50% cost<br/>1 request per submission]
    C --> D[Per-criterion draft:<br/>score + evidence quotes<br/>+ suggested comment<br/>+ confidence]
    D --> E{Consistency pass}
    E --> F[Outlier check: low-confidence or<br/>cross-batch inconsistent scores flagged]
    F --> G[Teacher review UI:<br/>sort by confidence,<br/>edit scores/comments]
    G --> H[Approve → grades released<br/>edits logged for calibration]
    H --> I[Calibration store:<br/>teacher-vs-AI deltas feed<br/>eval suite + prompt tuning]
```

**Rules:** nothing student-visible before approval; every draft carries evidence quotes from
the submission (no quote → no score, criterion marked "needs human"); confidence < threshold
auto-sorts to top of review queue.

## 3. Lesson planning workflow

```mermaid
flowchart LR
    A[Teacher: objective, grade,<br/>duration, select materials] --> B[RAG over selected materials]
    B --> C[Structured generation - Opus 4.8<br/>JSON schema: objectives, standards,<br/>warm-up, instruction, practice,<br/>differentiation notes, exit ticket]
    C --> D[Editable structured editor<br/>section-level regenerate]
    D --> E[Save to class library]
    E --> F[Optional: derive worksheet /<br/>quiz / slides - v1.1]
```

Structured outputs (JSON schema enforcement) guarantee the plan always parses into the editor.
Section-level "regenerate just this part" avoids full re-runs (cost + teacher control).

## 4. Insight loop (misconception analytics)

```mermaid
flowchart LR
    A[Nightly job: new tutor sessions,<br/>escalations, grading deltas] --> B[Per-session tags<br/>already extracted - Haiku]
    B --> C[Weekly clustering per class:<br/>embed tags → cluster →<br/>label clusters - Sonnet 5]
    C --> D[Digest: top misconceptions,<br/>affected-student counts,<br/>anonymized example exchanges,<br/>suggested re-teach mini-lesson]
    D --> E[Teacher dashboard + weekly email]
    E --> F[One-click: generate re-teach<br/>lesson from cluster → Workflow 3]
```

Privacy rule: digests show pseudonymous counts by default; drill-down to named transcripts is
teacher-of-record only and audit-logged.

## 5. Safety escalation workflow

```mermaid
flowchart TD
    A[Flag raised: moderation hit,<br/>self-harm signal, harassment,<br/>repeated jailbreak attempts] --> B{Severity triage - rules + Haiku}
    B -- critical<br/>self-harm/violence --> C[Immediate: teacher + admin alert<br/>email + in-app, < 5 min SLA<br/>conversation paused,<br/>supportive resources shown]
    B -- moderate --> D[Teacher queue item<br/>with transcript context]
    B -- low/false-positive-likely --> E[Logged only,<br/>weekly review sample]
    C --> F[Resolution recorded:<br/>action, actor, timestamp]
    D --> F
    F --> G[All escalations in audit log<br/>+ monthly safety report]
```

**Design stance:** the system never plays counselor — critical flags route to humans fast,
the student sees age-appropriate supportive language and resources, and the conversation is
paused, not deleted (evidence preservation).

## 6. Cross-cutting: every AI call

```
assemble(prompt_id@ver, cached class prefix, task context)
  → route(task_class → model)            # 06_LLM_SELECTION
  → call with retries/fallback           # circuit breaker
  → trace(model, tokens, cost, latency)  # Langfuse/OTel
  → audit(actor, entity, output hash)    # append-only
```
