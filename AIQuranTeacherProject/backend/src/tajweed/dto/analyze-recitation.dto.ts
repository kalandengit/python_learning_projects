import { IsInt, IsString, MaxLength, Min, MinLength } from 'class-validator';

export class AnalyzeRecitationDto {
  @IsInt()
  @Min(1)
  surahId!: number;

  @IsInt()
  @Min(1)
  ayahNumber!: number;

  /**
   * The learner's recitation, as a transcript produced by on-device speech
   * recognition. Bounded to keep prompt size (and cost) predictable.
   */
  @IsString()
  @MinLength(1)
  @MaxLength(4000)
  transcript!: string;
}
