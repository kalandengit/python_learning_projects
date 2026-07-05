import {
  Injectable,
  Logger,
  ServiceUnavailableException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { MistralConfig } from '../../config/configuration';

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatCompletionOptions {
  /** Sampling temperature. Lower is more deterministic. */
  temperature?: number;
  /** Force the model to return a syntactically valid JSON object. */
  json?: boolean;
  /** Upper bound on generated tokens. */
  maxTokens?: number;
}

interface MistralChatResponse {
  choices: Array<{ message: { role: string; content: string } }>;
}

/**
 * Thin, dependency-free client for the Mistral AI chat-completions API.
 *
 * Wrapping the HTTP call in a service keeps the API key in one place, gives
 * every caller consistent timeout/error handling, and — crucially — makes the
 * AI features unit-testable: tests inject a mock of this service instead of
 * hitting the network.
 */
@Injectable()
export class MistralService {
  private readonly logger = new Logger(MistralService.name);
  private readonly config: MistralConfig;

  constructor(private readonly configService: ConfigService) {
    this.config = this.configService.getOrThrow<MistralConfig>('mistral');
  }

  /** True when an API key is configured; features can degrade gracefully otherwise. */
  isConfigured(): boolean {
    return this.config.apiKey.length > 0;
  }

  /**
   * Send a chat completion request and return the assistant's text content.
   *
   * @throws ServiceUnavailableException on missing key, timeout, or upstream error.
   */
  async chat(
    messages: ChatMessage[],
    options: ChatCompletionOptions = {},
  ): Promise<string> {
    if (!this.isConfigured()) {
      throw new ServiceUnavailableException(
        'Mistral AI is not configured (MISTRAL_API_KEY missing).',
      );
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.config.timeoutMs);

    try {
      const response = await fetch(`${this.config.apiUrl}/chat/completions`, {
        method: 'POST',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.config.apiKey}`,
        },
        body: JSON.stringify({
          model: this.config.model,
          messages,
          temperature: options.temperature ?? 0.2,
          max_tokens: options.maxTokens ?? 1024,
          ...(options.json ? { response_format: { type: 'json_object' } } : {}),
        }),
      });

      if (!response.ok) {
        // Never surface the raw upstream body to clients — log it, return a
        // generic error. Redact nothing sensitive is sent, but be conservative.
        const body = await response.text().catch(() => '');
        this.logger.error(
          `Mistral API error ${response.status}: ${body.slice(0, 500)}`,
        );
        throw new ServiceUnavailableException(
          'The AI service is temporarily unavailable. Please try again.',
        );
      }

      const data = (await response.json()) as MistralChatResponse;
      const content = data.choices?.[0]?.message?.content;
      if (!content) {
        throw new ServiceUnavailableException(
          'The AI service returned an empty response.',
        );
      }
      return content;
    } catch (err) {
      if (err instanceof ServiceUnavailableException) throw err;
      if (err instanceof Error && err.name === 'AbortError') {
        this.logger.error(
          `Mistral request timed out after ${this.config.timeoutMs}ms`,
        );
        throw new ServiceUnavailableException('The AI service timed out.');
      }
      this.logger.error(`Mistral request failed: ${(err as Error).message}`);
      throw new ServiceUnavailableException('The AI service is unavailable.');
    } finally {
      clearTimeout(timeout);
    }
  }

  /**
   * Convenience wrapper that requests a JSON object and parses it.
   *
   * The model is asked (via `response_format`) to emit strict JSON, but we
   * still guard the parse and strip any accidental markdown fences.
   */
  async chatJson<T>(
    messages: ChatMessage[],
    options: Omit<ChatCompletionOptions, 'json'> = {},
  ): Promise<T> {
    const raw = await this.chat(messages, { ...options, json: true });
    const cleaned = raw
      .trim()
      .replace(/^```(?:json)?/i, '')
      .replace(/```$/, '')
      .trim();
    try {
      return JSON.parse(cleaned) as T;
    } catch {
      this.logger.error(
        `Failed to parse AI JSON response: ${cleaned.slice(0, 300)}`,
      );
      throw new ServiceUnavailableException(
        'The AI service returned malformed data.',
      );
    }
  }
}
