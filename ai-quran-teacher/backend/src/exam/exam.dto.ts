import { ArrayNotEmpty, IsIn, IsInt, IsUUID } from 'class-validator';
import { ExamLevel } from './exam.entity';

export class StartExamDto {
  @IsUUID()
  userId: string;

  @IsIn(['foundation', 'intermediate', 'advanced'])
  level: ExamLevel;
}

export class SubmitExamDto {
  @IsUUID()
  examId: string;

  @ArrayNotEmpty()
  @IsInt({ each: true })
  answers: number[];
}
