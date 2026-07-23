import { Body, Controller, Post } from '@nestjs/common';
import { ApiBearerAuth, ApiOkResponse, ApiTags } from '@nestjs/swagger';
import { CapabilityExecutor } from '@asa/capability-registry';
import { RequestContextService } from '@asa/auth';
import { FaqRequestDto } from './dto/faq-request.dto';
import type { FaqOutput } from './faq.capability';

/** Response envelope for a capability invocation. */
export interface FaqResponse {
  answer: string;
  model: string;
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

/**
 * Demonstrates invoking a registered capability from a feature. Authentication
 * is enforced by the global guard; the tenant/actor/correlation id are read
 * from the ambient request context and passed to the executor for governance
 * and audit. The controller never touches a provider directly (ADR-0002).
 */
@ApiTags('ai')
@ApiBearerAuth()
@Controller('ai')
export class AiController {
  constructor(
    private readonly executor: CapabilityExecutor,
    private readonly context: RequestContextService,
  ) {}

  @Post('faq')
  @ApiOkResponse({ description: 'The capability answer with usage metadata.' })
  async faq(@Body() body: FaqRequestDto): Promise<FaqResponse> {
    const outcome = await this.executor.invoke<FaqOutput>(
      'faq-answer',
      '1.0.0',
      { question: body.question },
      {
        tenantId: this.context.tenantId,
        actor: this.context.principal?.subject,
        correlationId: this.context.correlationId,
      },
    );
    return {
      answer: outcome.output.answer,
      model: outcome.model,
      usage: outcome.usage,
    };
  }
}
