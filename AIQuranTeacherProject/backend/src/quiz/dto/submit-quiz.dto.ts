import {
  ArrayMaxSize,
  ArrayMinSize,
  IsArray,
  IsInt,
  Min,
} from 'class-validator';

export class SubmitQuizDto {
  /**
   * The selected option index for each question, in order.
   * Length must match the number of questions in the quiz.
   */
  @IsArray()
  @ArrayMinSize(1)
  @ArrayMaxSize(10)
  @IsInt({ each: true })
  @Min(0, { each: true })
  answers!: number[];
}
