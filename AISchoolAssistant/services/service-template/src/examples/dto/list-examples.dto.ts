import { Type } from 'class-transformer';
import { IsInt, IsOptional, IsString, Max, Min } from 'class-validator';
import { ApiPropertyOptional } from '@nestjs/swagger';
import { DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE } from '@asa/contracts';

/**
 * Query parameters for listing examples. Validated and coerced by the global
 * `ValidationPipe`; the service still re-normalizes via `normalizePageQuery`
 * as defense-in-depth.
 */
export class ListExamplesDto {
  @ApiPropertyOptional({ minimum: 1, default: DEFAULT_PAGE })
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @IsOptional()
  page: number = DEFAULT_PAGE;

  @ApiPropertyOptional({
    minimum: 1,
    maximum: MAX_PAGE_SIZE,
    default: DEFAULT_PAGE_SIZE,
  })
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(MAX_PAGE_SIZE)
  @IsOptional()
  pageSize: number = DEFAULT_PAGE_SIZE;

  @ApiPropertyOptional({
    description: 'Sort expression, e.g. "name" or "-createdAt".',
  })
  @IsString()
  @IsOptional()
  sort?: string;
}
