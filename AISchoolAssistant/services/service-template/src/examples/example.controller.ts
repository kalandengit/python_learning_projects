import { Controller, Get, Param, Query } from '@nestjs/common';
import { ApiOkResponse, ApiTags } from '@nestjs/swagger';
import type { Page } from '@asa/contracts';
import { ExampleService } from './example.service';
import type { Example } from './example.model';
import { ListExamplesDto } from './dto/list-examples.dto';

@ApiTags('examples')
@Controller('examples')
export class ExampleController {
  constructor(private readonly examples: ExampleService) {}

  @Get()
  @ApiOkResponse({ description: 'A page of examples.' })
  list(@Query() query: ListExamplesDto): Page<Example> {
    return this.examples.list(query);
  }

  @Get(':id')
  @ApiOkResponse({ description: 'A single example.' })
  getById(@Param('id') id: string): Example {
    return this.examples.getById(id);
  }
}
