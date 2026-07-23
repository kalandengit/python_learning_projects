# @asa/ai-sdk

Provider-agnostic AI SDK for the AI School Assistant platform. Defines the
single port every model provider implements plus the registry and router used to
resolve them. **Business logic never imports a vendor SDK** — it depends only on
these interfaces (ADR-0002).

## What you get

- **Types** — `ChatMessage`, `ChatRequest`, `ChatResult`, `TokenUsage`,
  `ToolDefinition`/`ToolCall`, streaming `ChatChunk`, and embedding types.
- **`LanguageModelProvider`** — the port: `generate` (required), optional
  `stream` and `embed`, with `supportsStreaming` / `supportsEmbeddings` guards.
- **`AiProviderRegistry`** — register/resolve providers by id.
- **`ModelRouter`** — resolves a logical reference (`provider:model`, a named
  alias, or the default) to a concrete provider + model, so operators re-route
  models (cost/latency/availability) without touching feature code.
- **`EchoProvider`** — a deterministic, offline provider that echoes the last
  user message. For local development and as a reproducible fixture for
  evaluating capabilities and testing the full pipeline. **Not a real model.**

## Adding a real provider

Implement `LanguageModelProvider` in a separate adapter package (e.g.
`@asa/ai-provider-anthropic`) that wraps the vendor SDK, then register it:

```ts
const providers = new AiProviderRegistry([
  new AnthropicProvider({ apiKey: process.env.ANTHROPIC_API_KEY }),
  new EchoProvider(),
]);
const router = new ModelRouter(
  { 'chat-default': 'anthropic:claude-sonnet-5' },
  'anthropic:claude-sonnet-5',
);
```

Only the adapter imports the vendor SDK; everything else stays provider-agnostic.
