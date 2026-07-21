import {
  IsInt,
  IsOptional,
  IsString,
  IsUUID,
  Max,
  MaxLength,
  Min,
} from 'class-validator';

export class GrantWhitelistDto {
  /** The user who should receive free premium access. */
  @IsUUID()
  userId!: string;

  /**
   * How many days the free access lasts. Omit for an indefinite grant
   * (until an admin revokes it). Max ~10 years.
   */
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(3650)
  durationDays?: number;

  @IsOptional()
  @IsString()
  @MaxLength(200)
  reason?: string;
}
