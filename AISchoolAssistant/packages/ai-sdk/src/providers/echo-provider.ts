import type { LanguageModelProvider } from '../provider';
import type {
  ChatChunk,
  ChatRequest,
  ChatResult,
  EmbeddingRequest,
  EmbeddingResult,
  TokenUsage,
} from '../types';

/** Rough token estimate (~words) so usage is populated deterministically. */
function estimateTokens(text: string): number {
  const trimmed = text.trim();
  return trimmed ? trimmed.split(/\s+/).length : 0;
}

function lastUserMessage(request: ChatRequest): string {
  for (let i = request.messages.length - 1; i >= 0; i -= 1) {
    if (request.messages[i].role === 'user') {
      return request.messages[i].content;
    }
  }
  return '';
}

/** Deterministic pseudo-embedding derived from character codes. */
function embed(text: string, dimensions: number): number[] {
  const vector = new Array<number>(dimensions).fill(0);
  for (let i = 0; i < text.length; i += 1) {
    vector[i % dimensions] += text.charCodeAt(i) / 255;
  }
  const norm = Math.sqrt(vector.reduce((sum, v) => sum + v * v, 0)) || 1;
  return vector.map((v) => Number((v / norm).toFixed(6)));
}

/**
 * A fully deterministic, offline provider that echoes the last user message.
 * Its purpose is twofold: a zero-dependency provider for local development, and
 * a reproducible fixture for evaluating capabilities and testing the full AI
 * pipeline without network access or API keys. It is NOT a real model.
 */
export class EchoProvider implements LanguageModelProvider {
  readonly id: string;
  private readonly embeddingDimensions: number;

  constructor(options: { id?: string; embeddingDimensions?: number } = {}) {
    this.id = options.id ?? 'echo';
    this.embeddingDimensions = options.embeddingDimensions ?? 8;
  }

  private render(request: ChatRequest): string {
    const content = lastUserMessage(request);
    if (request.responseFormat === 'json') {
      return JSON.stringify({ echo: content });
    }
    return `[echo] ${content}`;
  }

  private usageFor(request: ChatRequest, output: string): TokenUsage {
    const promptTokens = request.messages.reduce(
      (sum, m) => sum + estimateTokens(m.content),
      0,
    );
    const completionTokens = estimateTokens(output);
    return {
      promptTokens,
      completionTokens,
      totalTokens: promptTokens + completionTokens,
    };
  }

  async generate(request: ChatRequest): Promise<ChatResult> {
    const text = this.render(request);
    return {
      text,
      finishReason: 'stop',
      usage: this.usageFor(request, text),
      model: request.model,
    };
  }

  async *stream(request: ChatRequest): AsyncIterable<ChatChunk> {
    const result = await this.generate(request);
    const words = result.text.split(' ');
    for (let i = 0; i < words.length; i += 1) {
      const isLast = i === words.length - 1;
      yield {
        delta: isLast ? words[i] : `${words[i]} `,
        finishReason: isLast ? 'stop' : undefined,
      };
    }
  }

  async embed(request: EmbeddingRequest): Promise<EmbeddingResult> {
    const embeddings = request.input.map((text) =>
      embed(text, this.embeddingDimensions),
    );
    const promptTokens = request.input.reduce(
      (sum, t) => sum + estimateTokens(t),
      0,
    );
    return {
      model: request.model,
      embeddings,
      usage: { promptTokens, completionTokens: 0, totalTokens: promptTokens },
    };
  }
}
