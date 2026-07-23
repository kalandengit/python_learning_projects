import { Body, Controller, Get, Post, Query } from '@nestjs/common';
import {
  ApiBearerAuth,
  ApiOkResponse,
  ApiQuery,
  ApiTags,
} from '@nestjs/swagger';
import { KnowledgeService, type KnowledgeHit } from '@asa/knowledge';
import { RequestContextService } from '@asa/auth';
import { ValidationError } from '@asa/errors';
import { IngestDocumentDto } from './dto/ingest-document.dto';

/**
 * Ingests documents into the Knowledge Platform and runs semantic search.
 * Documents are embedded via the AI SDK and stored in the vector store; all
 * operations are scoped to the caller's tenant for isolation.
 */
@ApiTags('knowledge')
@ApiBearerAuth()
@Controller('knowledge')
export class KnowledgeController {
  constructor(
    private readonly knowledge: KnowledgeService,
    private readonly context: RequestContextService,
  ) {}

  @Post('documents')
  @ApiOkResponse({ description: 'Number of documents ingested.' })
  async ingest(@Body() body: IngestDocumentDto): Promise<{ ingested: number }> {
    const ingested = await this.knowledge.ingest([
      {
        id: body.id,
        text: body.text,
        metadata: body.title ? { title: body.title } : {},
        tenantId: this.context.tenantId,
      },
    ]);
    return { ingested };
  }

  @Get('search')
  @ApiQuery({ name: 'q', required: true })
  @ApiOkResponse({ description: 'Ranked search hits.' })
  async search(@Query('q') q: string): Promise<{ hits: KnowledgeHit[] }> {
    if (!q || q.trim().length === 0) {
      throw new ValidationError('Query parameter "q" is required.');
    }
    const hits = await this.knowledge.search(q, {
      topK: 5,
      tenantId: this.context.tenantId,
    });
    return { hits };
  }
}
