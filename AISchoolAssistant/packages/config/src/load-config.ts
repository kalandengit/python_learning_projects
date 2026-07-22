import type { TypeOf, ZodTypeAny } from 'zod';
import { ValidationError } from '@asa/errors';

export type EnvSource = Record<string, string | undefined>;

/**
 * Validate and parse configuration against a zod schema, failing fast with a
 * readable {@link ValidationError} (problem+json-ready) if anything is invalid
 * or missing. Twelve-factor: config comes from the environment.
 *
 * @example
 *   const schema = z.object({ PORT: z.coerce.number().default(3000) });
 *   const config = loadConfig(schema);
 */
export function loadConfig<S extends ZodTypeAny>(
  schema: S,
  env: EnvSource = process.env,
): TypeOf<S> {
  const result = schema.safeParse(env);
  if (!result.success) {
    const errors = result.error.issues.map((issue) => ({
      field: issue.path.join('.') || '(root)',
      message: issue.message,
    }));
    throw new ValidationError('Invalid environment configuration.', errors);
  }
  return result.data;
}
