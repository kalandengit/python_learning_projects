import { Controller, Get, Param, Query } from '@nestjs/common';
import { ApiBearerAuth, ApiOkResponse, ApiTags } from '@nestjs/swagger';
import { Roles } from '@asa/auth';
import type { Page } from '@asa/contracts';
import { ExampleService } from './example.service';
import type { Example } from './example.model';
import { ListExamplesDto } from './dto/list-examples.dto';

/**
 * Authenticated by default (the global auth guard). Demonstrates a
 * role-protected endpoint via `@Roles`, alongside ordinary authenticated reads.
 */
@ApiTags('examples')
@ApiBearerAuth()
@Controller('examples')
export class ExampleController {
  constructor(private readonly examples: ExampleService) {}

  @Get()
  @ApiOkResponse({ description: 'A page of examples.' })
  list(@Query() query: ListExamplesDto): Page<Example> {
    return this.examples.list(query);
  }

  @Get('admin/summary')
  @Roles('examples:admin')
  @ApiOkResponse({ description: 'Aggregate counts (requires examples:admin).' })
  summary(): { total: number } {
    return { total: this.examples.count() };
  }

  @Get(':id')
  @ApiOkResponse({ description: 'A single example.' })
  getById(@Param('id') id: string): Example {
    return this.examples.getById(id);
  }
}
