import { Body, Controller, Param, Post } from '@nestjs/common';
import { ApiBearerAuth, ApiOkResponse, ApiTags } from '@nestjs/swagger';
import { AgentExecutor } from '@asa/agent-runtime';
import { RequestContextService } from '@asa/auth';
import { RunAgentDto } from './dto/run-agent.dto';

/** Response envelope for an agent run. */
export interface AgentRunResponse {
  output: string;
  steps: number;
  toolsUsed: string[];
  finishReason: 'completed' | 'max_steps';
  model: string;
}

/**
 * Runs a registered agent. Authentication is enforced by the global guard; the
 * tenant/actor/correlation id flow from the request context into the run for
 * governance and audit. The controller never touches a provider or tool
 * directly — the runtime owns the reasoning loop.
 */
@ApiTags('agents')
@ApiBearerAuth()
@Controller('agents')
export class AgentsController {
  constructor(
    private readonly executor: AgentExecutor,
    private readonly context: RequestContextService,
  ) {}

  @Post(':id/invoke')
  @ApiOkResponse({ description: 'The agent run result.' })
  async invoke(
    @Param('id') id: string,
    @Body() body: RunAgentDto,
  ): Promise<AgentRunResponse> {
    const result = await this.executor.run(
      id,
      body.version ?? '1.0.0',
      { goal: body.goal },
      {
        tenantId: this.context.tenantId,
        actor: this.context.principal?.subject,
        correlationId: this.context.correlationId,
      },
    );
    return {
      output: result.output,
      steps: result.steps,
      toolsUsed: result.toolsUsed,
      finishReason: result.finishReason,
      model: result.model,
    };
  }
}
