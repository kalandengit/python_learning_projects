import {
  IsEnum,
  IsInt,
  IsOptional,
  IsString,
  Max,
  MaxLength,
  Min,
} from 'class-validator';
import { QuizDifficulty } from '../quiz.entity';

export class GenerateQuizDto {
  @IsOptional()
  @IsString()
  @MaxLength(120)
  topic?: string;

  @IsEnum(QuizDifficulty)
  difficulty!: QuizDifficulty;

  @IsInt()
  @Min(1)
  @Max(10)
  numQuestions!: number;
}
