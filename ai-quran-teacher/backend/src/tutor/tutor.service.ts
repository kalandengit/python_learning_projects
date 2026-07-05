import { Injectable } from '@nestjs/common';
import { CompletionRequest, LlmService } from '../llm/llm.service';
import { ASPECT_PROMPTS, TutorAspect } from './tutor.prompts';

export interface TutorAspectResult {
  aspect: TutorAspect;
  text?: string;
  error?: string;
}

export interface TutorResponse {
  question: string;
  aspects: TutorAspectResult[];
  usage: { inputTokens: number; outputTokens: number };
  /** Wall-clock time for the whole fan-out, in milliseconds. */
  latencyMs: number;
}

const DEFAULT_ASPECTS: TutorAspect[] = ['answer', 'tafsir', 'tajweed', 'followUp'];

@Injectable()
export class TutorService {
  constructor(private readonly llm: LlmService) {}

  get available(): boolean {
    return this.llm.enabled;
  }

  /**
   * Answers a student's question by fanning out one Claude request per aspect
   * and running them **simultaneously**. Because the aspects are independent,
   * total latency is roughly that of the slowest single call rather than the
   * sum — the point of the parallel LLM design.
   */
  async ask(
    question: string,
    context: string | undefined,
    aspects: TutorAspect[] = DEFAULT_ASPECTS,
  ): Promise<TutorResponse> {
    const started = Date.now();
    const contextBlock = context
      ? `\n\nThe student is currently looking at this text/context:\n"""${context}"""`
      : '';

    const requests: CompletionRequest[] = aspects.map((aspect) => ({
      system: ASPECT_PROMPTS[aspect],
      prompt: `Student's question: ${question}${contextBlock}`,
      // The main answer benefits from deeper reasoning; the rest stay light
      // to keep the fan-out fast and cheap.
      effort: aspect === 'answer' ? 'high' : 'low',
      think: aspect === 'answer',
      maxTokens: aspect === 'followUp' ? 512 : 2048,
    }));

    const outcomes = await this.llm.parallel(requests);

    let inputTokens = 0;
    let outputTokens = 0;
    const results: TutorAspectResult[] = outcomes.map((outcome, i) => {
      if (outcome.result) {
        inputTokens += outcome.result.inputTokens;
        outputTokens += outcome.result.outputTokens;
        return { aspect: aspects[i], text: outcome.result.text };
      }
      return { aspect: aspects[i], error: outcome.error };
    });

    return {
      question,
      aspects: results,
      usage: { inputTokens, outputTokens },
      latencyMs: Date.now() - started,
    };
  }
}
