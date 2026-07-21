import {
  IsEmail,
  IsString,
  Matches,
  MaxLength,
  MinLength,
} from 'class-validator';

export class RegisterDto {
  @IsEmail({}, { message: 'A valid email address is required.' })
  @MaxLength(320)
  email!: string;

  @IsString()
  @MinLength(2)
  @MaxLength(80)
  displayName!: string;

  @IsString()
  @MinLength(10, { message: 'Password must be at least 10 characters.' })
  @MaxLength(128)
  @Matches(/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, {
    message: 'Password must contain upper- and lower-case letters and a digit.',
  })
  password!: string;
}
