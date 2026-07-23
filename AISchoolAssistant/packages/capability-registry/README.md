# @asa/capability-registry

The **Capability Registry** and governed executor — the enterprise catalog of AI
capabilities every feature invokes instead of calling a model directly
(ADR-0002). Built on `@asa/ai-sdk`.

## Concepts

A **capability** is a named, versioned unit that fully specifies:

- **I/O contract** — zod `inputSchema` / `outputSchema`.
- **Prompt/policy** — `buildPrompt(input, ctx)`.
- **Model routing** — a logical `model` reference resolved by the `ModelRouter`.
- **Output parsing** — `parseOutput(result, input)`.
- **Governance** — owner, data classification, PII policy, and a **model
  allow-list**.
- **Evaluation** — a suite of cases + a minimum pass rate.

## Guarantees (enforced)

- **Every capability requires evaluation.** A capability is registered as
  `draft` and can only be promoted to `published` when its evaluation passes
  threshold (`CapabilityRegistry.publish`). No eval, no publish.
- **Only published capabilities run.** `CapabilityExecutor.invoke` refuses
  `draft` capabilities.
- **Never bypass the registry / always via the AI SDK.** `executeCapability` is
  the single path from input to output: validate input → route model → enforce
  the governance allow-list → build prompt → call the provider → parse →
  validate output. There is no other way to reach a provider.
- **Everything is observed.** Each invocation (success or failure) emits a
  `CapabilityInvocationEvent` to the `AiObservabilitySink` with model, usage,
  latency, tenant, actor, and correlation id.

## NestJS usage

```ts
AiModule.forRoot({
  providers: [new EchoProvider()], // default; add real adapters here
  capabilities: [faqCapability], // registered + evaluated + published at boot
});
```

`AiModule` publishes each configured capability at application boot and **aborts
startup if an evaluation regresses** (fail-fast). Features inject
`CapabilityExecutor` and call `invoke(id, version, input, context)`.

## Testing

`executeCapability` runs the same governed path in tests as in production; with
the `EchoProvider` the output and evaluation are deterministic. Use the
`InMemoryObservabilitySink` to assert emitted events.
