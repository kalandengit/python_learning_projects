import { IsArray, IsIn, IsOptional, IsString, MaxLength, MinLength } from 'class-validator';
import { TutorAspect } from './tutor.prompts';

const ALL_ASPECTS: TutorAspect[] = ['answer', 'tafsir', 'tajweed', 'followUp'];

export class AskTutorDto {
  @IsString()
  @MinLength(3)
  @MaxLength(2000)
  question: string;

  /** Optional ayah/surah context the student is looking at. */
  @IsOptional()
  @IsString()
  @MaxLength(4000)
  context?: string;

  /**
   * Which aspects to generate. Each aspect is a separate Claude call and they
   * run concurrently. Defaults to all four.
   */
  @IsOptional()
  @IsArray()
  @IsIn(ALL_ASPECTS, { each: true })
  aspects?: TutorAspect[];
}
