import { Type } from 'class-transformer';
import {
  ArrayNotEmpty,
  IsIn,
  IsInt,
  IsOptional,
  IsUUID,
  Max,
  Min,
} from 'class-validator';
import { QuizDifficulty } from './quiz.entity';

export class GenerateQuizDto {
  @IsUUID()
  userId: string;

  @IsOptional()
  @IsIn(['easy', 'medium', 'hard'])
  difficulty?: QuizDifficulty;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(10)
  count?: number;
}

export class SubmitQuizDto {
  @IsUUID()
  quizId: string;

  /** Selected option index per question, in served order. */
  @ArrayNotEmpty()
  @IsInt({ each: true })
  answers: number[];
}
