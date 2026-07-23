# @asa/agent-runtime

The **Agent Registry** and **multi-agent runtime** — a governed, bounded
tool-calling loop built on `@asa/ai-sdk` (ADR-0005). Features run agents by
id/version; the runtime owns reasoning, tool dispatch, and safety.

## Concepts

- **Tool** (`AgentTool`) — `name`, `description`, a JSON-Schema `parameters`
  object advertised to the model, a zod `inputSchema` that validates
  model-produced arguments, and `execute(args, ctx)`. Registered in a
  `ToolRegistry`.
- **Agent** (`AgentDefinition`) — `instructions`, a routed `model`, an allowed
  `tools` list, a hard `maxSteps` bound, and governance metadata. Registered in
  an `AgentRegistry`.
- **`AgentExecutor`** — runs the loop: prompt the model with the available
  tools → execute any tool calls → feed results back → repeat until the model
  answers or `maxSteps` is hit.

## Guarantees (enforced)

- **Bounded** — every run stops at `maxSteps` (returns a `max_steps` outcome
  instead of looping).
- **Validated tool arguments** — model-produced arguments are parsed and
  zod-validated before a tool runs; malformed/invalid arguments fail the run.
- **Tool allow-list** — an agent calling a tool outside its declared set is
  rejected (`Forbidden`).
- **Model allow-list** — the routed model must be on the agent's governance
  allow-list.
- **Observed** — each run emits an `AgentRunEvent` (model, steps, tools used,
  usage, latency, tenant, actor, correlation id, outcome).

## NestJS usage

```ts
AgentModule.forRoot({
  providers: [new EchoProvider()], // default; add real adapters here
  tools: [addTool],
  agents: [assistantAgent],
});
```

Features inject `AgentExecutor` and call `run(id, version, { goal }, context)`.

## Testing

Use `ScriptedProvider` from `@asa/ai-sdk` to drive deterministic tool-calling:
script a turn that requests a tool call, then a turn that returns the final
answer. Assert emitted events with `InMemoryAgentSink`. No live model required.
