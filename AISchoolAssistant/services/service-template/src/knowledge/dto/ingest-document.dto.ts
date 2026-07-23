import { IsOptional, IsString, Length } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

/** Body for ingesting a knowledge document. */
export class IngestDocumentDto {
  @ApiProperty()
  @IsString()
  @Length(1, 100)
  id!: string;

  @ApiProperty({ minLength: 1, maxLength: 10000 })
  @IsString()
  @Length(1, 10000)
  text!: string;

  @ApiPropertyOptional()
  @IsString()
  @IsOptional()
  title?: string;
}
