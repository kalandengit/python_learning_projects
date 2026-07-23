import type { LanguageModelProvider } from '../provider';
import type {
  ChatChunk,
  ChatRequest,
  ChatResult,
  FinishReason,
  ToolCall,
} from '../types';

/** A single scripted turn: text and/or tool calls the provider should emit. */
export interface ScriptedResponse {
  text?: string;
  toolCalls?: ToolCall[];
  finishReason?: FinishReason;
}

/**
 * A deterministic provider that returns a predefined sequence of responses,
 * one per `generate` call. Purpose-built for testing multi-step flows (e.g. an
 * agent's tool-calling loop) without a real model: script a turn that requests
 * a tool call, then a turn that returns the final answer. Throws once the
 * script is exhausted, so an unexpected extra call is a visible test failure.
 */
export class ScriptedProvider implements LanguageModelProvider {
  readonly id: string;
  private cursor = 0;

  constructor(
    private readonly responses: ScriptedResponse[],
    options: { id?: string } = {},
  ) {
    this.id = options.id ?? 'scripted';
  }

  /** Number of times `generate` has been called. */
  get calls(): number {
    return this.cursor;
  }

  async generate(request: ChatRequest): Promise<ChatResult> {
    if (this.cursor >= this.responses.length) {
      throw new Error(
        `ScriptedProvider exhausted after ${this.responses.length} response(s).`,
      );
    }
    const response = this.responses[this.cursor];
    this.cursor += 1;

    const hasToolCalls = (response.toolCalls?.length ?? 0) > 0;
    return {
      text: response.text ?? '',
      toolCalls: response.toolCalls,
      finishReason:
        response.finishReason ?? (hasToolCalls ? 'tool_calls' : 'stop'),
      usage: { promptTokens: 0, completionTokens: 0, totalTokens: 0 },
      model: request.model,
    };
  }

  async *stream(request: ChatRequest): AsyncIterable<ChatChunk> {
    const result = await this.generate(request);
    yield { delta: result.text, finishReason: result.finishReason };
  }
}
