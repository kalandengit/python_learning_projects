import { IsNumber, IsString, Length, Max, Min } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

/** Body for recording an assessment score. */
export class RecordAssessmentDto {
  @ApiProperty()
  @IsString()
  @Length(1, 100)
  assessmentId!: string;

  @ApiProperty()
  @IsString()
  @Length(1, 100)
  topic!: string;

  @ApiProperty({ minimum: 0, maximum: 100 })
  @IsNumber()
  @Min(0)
  @Max(100)
  score!: number;
}
