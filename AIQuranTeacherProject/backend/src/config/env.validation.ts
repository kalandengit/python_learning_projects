import { plainToInstance } from 'class-transformer';
import {
  IsEnum,
  IsInt,
  IsOptional,
  IsString,
  validateSync,
} from 'class-validator';

enum NodeEnv {
  Development = 'development',
  Production = 'production',
  Test = 'test',
}

/**
 * Fail-fast validation of the process environment.
 *
 * Nest calls {@link validate} during module initialisation; if a required
 * variable is missing or malformed the process exits immediately instead of
 * failing later with a confusing runtime error. In production a weak or unset
 * `JWT_SECRET` is treated as fatal.
 */
class EnvironmentVariables {
  @IsEnum(NodeEnv)
  @IsOptional()
  NODE_ENV?: NodeEnv;

  @IsInt()
  @IsOptional()
  PORT?: number;

  @IsString()
  @IsOptional()
  DB_TYPE?: string;

  @IsString()
  @IsOptional()
  JWT_SECRET?: string;

  @IsString()
  @IsOptional()
  MISTRAL_API_KEY?: string;
}

export function validate(
  config: Record<string, unknown>,
): Record<string, unknown> {
  const validatedConfig = plainToInstance(EnvironmentVariables, config, {
    enableImplicitConversion: true,
  });

  const errors = validateSync(validatedConfig, {
    skipMissingProperties: true,
  });

  if (errors.length > 0) {
    throw new Error(
      `Invalid environment configuration:\n${errors
        .map((e) => `  - ${Object.values(e.constraints ?? {}).join(', ')}`)
        .join('\n')}`,
    );
  }

  const isProd = (config.NODE_ENV ?? 'development') === 'production';
  const secret = (config.JWT_SECRET as string) ?? '';
  if (isProd && secret.length < 32) {
    throw new Error(
      'JWT_SECRET must be set to a strong value (>= 32 chars) in production.',
    );
  }

  return config;
}
