import type {
  ChatChunk,
  ChatRequest,
  ChatResult,
  EmbeddingRequest,
  EmbeddingResult,
} from './types';

/**
 * The single port every model provider implements. Business logic depends only
 * on this interface — never on a vendor SDK — so providers (OpenAI, Anthropic,
 * Gemini, Mistral, Ollama, vLLM, …) are swappable behind the router.
 *
 * `generate` is required; `stream` and `embed` are optional capabilities a
 * provider may advertise by implementing them.
 */
export interface LanguageModelProvider {
  /** Stable provider id used in `provider:model` references. */
  readonly id: string;

  generate(request: ChatRequest, signal?: AbortSignal): Promise<ChatResult>;

  stream?(request: ChatRequest, signal?: AbortSignal): AsyncIterable<ChatChunk>;

  embed?(request: EmbeddingRequest): Promise<EmbeddingResult>;
}

/** Narrowing helper: does the provider support streaming? */
export function supportsStreaming(
  provider: LanguageModelProvider,
): provider is LanguageModelProvider &
  Required<Pick<LanguageModelProvider, 'stream'>> {
  return typeof provider.stream === 'function';
}

/** Narrowing helper: does the provider support embeddings? */
export function supportsEmbeddings(
  provider: LanguageModelProvider,
): provider is LanguageModelProvider &
  Required<Pick<LanguageModelProvider, 'embed'>> {
  return typeof provider.embed === 'function';
}
