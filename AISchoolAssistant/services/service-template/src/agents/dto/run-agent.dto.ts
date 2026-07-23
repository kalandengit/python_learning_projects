import { IsOptional, IsString, Length } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

/** HTTP body for running an agent (validated by the global pipe). */
export class RunAgentDto {
  @ApiProperty({ minLength: 1, maxLength: 1000 })
  @IsString()
  @Length(1, 1000)
  goal!: string;

  @ApiPropertyOptional({ default: '1.0.0' })
  @IsString()
  @IsOptional()
  version?: string;
}
