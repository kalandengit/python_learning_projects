import {
  IsInt,
  IsNotEmpty,
  IsOptional,
  IsString,
  IsUUID,
} from 'class-validator';

export class DetectMistakesDto {
  /** The recited text (e.g. from speech recognition). */
  @IsString()
  @IsNotEmpty()
  text: string;

  @IsInt()
  ayahId: number;

  /** The expected mushaf text; when omitted, only rule analysis of `text` is returned. */
  @IsOptional()
  @IsString()
  expectedText?: string;

  @IsOptional()
  @IsUUID()
  userId?: string;
}

export class AnalyzeTextDto {
  @IsString()
  @IsNotEmpty()
  text: string;
}
