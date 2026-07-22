import { z } from 'zod';
import { loadConfig } from '@asa/config';
import type { AuthOptions } from '@asa/auth';

/** Injection token for the validated application config. */
export const APP_CONFIG = 'APP_CONFIG';

/** Parse a boolean from an env string ("true"/"1" → true) without JS coercion. */
const booleanFromString = z.preprocess((value) => {
  if (typeof value === 'string') {
    return ['true', '1', 'yes'].includes(value.trim().toLowerCase());
  }
  return value;
}, z.boolean());

const schema = z
  .object({
    NODE_ENV: z
      .enum(['development', 'production', 'test'])
      .default('development'),
    PORT: z.coerce.number().int().positive().default(3000),
    LOG_LEVEL: z.string().default('info'),
    SERVICE_NAME: z.string().default('service-template'),

    // Identity / OAuth 2.1 / OIDC. Secure by default: auth is ON unless the
    // operator explicitly disables it (local development only).
    AUTH_ENABLED: booleanFromString.default(true),
    OIDC_ISSUER: z.string().default(''),
    OIDC_AUDIENCE: z.string().default(''),
    OIDC_JWKS_URI: z.string().default(''),
    OIDC_TENANT_CLAIM: z.string().default('tenant_id'),
    OIDC_CLIENT_ID: z.string().optional(),
  })
  .superRefine((value, ctx) => {
    if (!value.AUTH_ENABLED) {
      return;
    }
    for (const key of [
      'OIDC_ISSUER',
      'OIDC_AUDIENCE',
      'OIDC_JWKS_URI',
    ] as const) {
      if (!value[key]) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: [key],
          message: `${key} is required when AUTH_ENABLED is true.`,
        });
      }
    }
  });

export type AppConfig = z.infer<typeof schema>;

/** Load + validate config from the environment (fail-fast). */
export function loadAppConfig(env: NodeJS.ProcessEnv = process.env): AppConfig {
  return loadConfig(schema, env);
}

/** Project the app config onto the auth layer's options. */
export function toAuthOptions(config: AppConfig): AuthOptions {
  return {
    enabled: config.AUTH_ENABLED,
    issuer: config.OIDC_ISSUER,
    audience: config.OIDC_AUDIENCE,
    jwksUri: config.OIDC_JWKS_URI,
    tenantClaim: config.OIDC_TENANT_CLAIM,
    clientId: config.OIDC_CLIENT_ID,
  };
}
