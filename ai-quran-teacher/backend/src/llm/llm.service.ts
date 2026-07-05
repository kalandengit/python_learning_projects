import Anthropic from '@anthropic-ai/sdk';
import { Injectable, Logger, ServiceUnavailableException } from '@nestjs/common';

/** Default model for the platform. See docs/LLM_GUIDE.md for the rationale. */
export const DEFAULT_MODEL = 'claude-opus-4-8';

export interface CompletionRequest {
  system?: string;
  prompt: string;
  /** low | medium | high | max — controls thinking depth and token spend. */
  effort?: 'low' | 'medium' | 'high' | 'max';
  maxTokens?: number;
  /** Turn on adaptive thinking for multi-step reasoning. */
  think?: boolean;
  model?: string;
}

export interface CompletionResult {
  text: string;
  model: string;
  inputTokens: number;
  outputTokens: number;
}

/**
 * Thin wrapper over the Anthropic SDK.
 *
 * Exposes a single-call `complete()` and a fan-out `parallel()` that runs
 * many independent Claude requests concurrently with a bounded worker pool —
 * the primitive behind the tutor's simultaneous multi-aspect analysis.
 */
@Injectable()
export class LlmService {
  private readonly logger = new Logger(LlmService.name);
  private readonly client: Anthropic | null;
  /** Max concurrent in-flight requests across the whole process. */
  private readonly maxConcurrency = Number.parseInt(
    process.env.LLM_MAX_CONCURRENCY ?? '8',
    10,
  );

  constructor() {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    // The SDK also resolves ANTHROPIC_AUTH_TOKEN / an `ant auth login` profile,
    // so construct it whenever any credential path is plausible.
    this.client = apiKey || process.env.ANTHROPIC_AUTH_TOKEN
      ? new Anthropic()
      : null;
    if (!this.client) {
      this.logger.warn(
        'No Anthropic credentials found; LLM features are disabled until ANTHROPIC_API_KEY is set.',
      );
    }
  }

  get enabled(): boolean {
    return this.client !== null;
  }

  /** Single Claude completion. Streams internally so large outputs don't time out. */
  async complete(request: CompletionRequest): Promise<CompletionResult> {
    if (!this.client) {
      throw new ServiceUnavailableException('LLM features are not configured.');
    }
    const model = request.model ?? DEFAULT_MODEL;
    const stream = this.client.messages.stream({
      model,
      max_tokens: request.maxTokens ?? 4096,
      ...(request.think ? { thinking: { type: 'adaptive' as const } } : {}),
      output_config: { effort: request.effort ?? 'medium' },
      ...(request.system ? { system: request.system } : {}),
      messages: [{ role: 'user', content: request.prompt }],
    });

    const message = await stream.finalMessage();
    const text = message.content
      .filter((block): block is Anthropic.TextBlock => block.type === 'text')
      .map((block) => block.text)
      .join('');

    return {
      text,
      model: message.model,
      inputTokens: message.usage.input_tokens,
      outputTokens: message.usage.output_tokens,
    };
  }

  /**
   * Runs many completions concurrently, preserving input order in the result.
   * Concurrency is capped by `maxConcurrency` so a large fan-out can't exhaust
   * the API rate limit or the event loop. Individual failures are captured per
   * item rather than rejecting the whole batch.
   */
  async parallel(
    requests: CompletionRequest[],
  ): Promise<Array<{ result?: CompletionResult; error?: string }>> {
    const results: Array<{ result?: CompletionResult; error?: string }> = new Array(
      requests.length,
    );
    let cursor = 0;

    const worker = async (): Promise<void> => {
      while (cursor < requests.length) {
        const index = cursor++;
        try {
          results[index] = { result: await this.complete(requests[index]) };
        } catch (error) {
          const message = error instanceof Error ? error.message : String(error);
          this.logger.error(`Parallel completion ${index} failed: ${message}`);
          results[index] = { error: message };
        }
      }
    };

    const poolSize = Math.min(this.maxConcurrency, requests.length);
    await Promise.all(Array.from({ length: poolSize }, () => worker()));
    return results;
  }
}
