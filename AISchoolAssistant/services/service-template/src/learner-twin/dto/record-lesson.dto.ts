import { IsString, Length } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

/** Body for recording a completed lesson. */
export class RecordLessonDto {
  @ApiProperty()
  @IsString()
  @Length(1, 100)
  lessonId!: string;

  @ApiProperty()
  @IsString()
  @Length(1, 100)
  topic!: string;
}
