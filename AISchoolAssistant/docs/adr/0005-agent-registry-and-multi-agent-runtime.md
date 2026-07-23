# ADR-0005: Agent Registry + Multi-Agent Runtime

- **Status:** Accepted
- **Date:** 2026-07-23
- **Context:** Master Spec #3, #5 (agents, multi-agent runtime); Codex AI rules;
  builds on ADR-0002 (AI SDK + Capability Registry); WP-3.

## Decision

Agents are a first-class, governed layer (`@asa/agent-runtime`) on top of the
AI SDK — not ad-hoc loops inside features.

1. **Agent** — a named, versioned unit declaring instructions, a routed model,
   an allowed **tool set**, a hard `maxSteps` bound, and governance metadata.
   Registered in an **Agent Registry**.
2. **Tools** — every tool declares a JSON-Schema (`parameters`) advertised to
   the model and a **zod `inputSchema`** that validates the model-produced
   arguments before execution. Tools live in a **Tool Registry**; an agent may
   only call tools on its declared allow-list.
3. **Runtime** — the `AgentExecutor` runs a bounded reasoning loop: prompt the
   model with the available tools, execute requested tool calls (validating
   arguments, enforcing the tool allow-list), feed results back, and repeat
   until the model answers or `maxSteps` is reached.
4. **Governance + observability** — the routed model must be on the agent's
   allow-list (same posture as capabilities); every run emits an `AgentRunEvent`
   (model, steps, tools used, usage, latency, tenant, actor, correlation id,
   outcome).

## Motivation

- Bounds and audits autonomy: no unbounded loops, no unvetted models, no
  unchecked tool arguments, and a full audit trail per run.
- Reuses the provider-agnostic AI SDK, so agents are model-portable and testable
  offline (the `ScriptedProvider` drives deterministic tool-calling in tests).
- Keeps feature code thin — controllers call `AgentExecutor.run(id, version,
  goal)`; the runtime owns the loop, tool dispatch, and safety.

## Rules (enforced)

- Model-produced tool arguments are **always** validated (zod) before a tool
  runs; malformed or invalid arguments fail the run.
- An agent calling a tool outside its declared set is rejected (`Forbidden`).
- Runs are bounded by `maxSteps`; hitting the bound returns a `max_steps`
  outcome rather than looping.
- The routed model must be on the agent's governance allow-list.

## Alternatives considered

- **Per-feature bespoke agent loops** — rejected: duplicated, unsafe (no bound,
  no arg validation, no audit), and untestable without live models.
- **A monolithic "AI" package** — rejected: the SDK (ADR-0002), capability
  registry (ADR-0002), and agent runtime have distinct responsibilities and
  dependency directions; separate packages keep the layering explicit.

## Consequences

- `@asa/agent-runtime` ships the tool + agent registries, executor, observability
  sink, and a NestJS `AgentModule`. The service template registers a reference
  `assistant` agent + `add` tool and exposes `POST /api/v1/agents/:id/invoke`.
- **MCP tools** are a natural `AgentTool` adapter (a tool whose `execute` calls
  an MCP endpoint) and are deferred to a later WP alongside vendor providers.
- Agents that invoke **capabilities** (ADR-0002) as tools unify the two layers;
  this composition lands as capability-backed tools in a later WP.
