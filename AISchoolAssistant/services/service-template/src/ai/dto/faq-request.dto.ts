import { IsString, Length } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

/** HTTP body for the FAQ capability endpoint (validated by the global pipe). */
export class FaqRequestDto {
  @ApiProperty({ minLength: 1, maxLength: 500 })
  @IsString()
  @Length(1, 500)
  question!: string;
}
