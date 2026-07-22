import { z } from 'zod';
import { loadConfig } from '@asa/config';

/** Injection token for the validated application config. */
export const APP_CONFIG = 'APP_CONFIG';

const schema = z.object({
  NODE_ENV: z
    .enum(['development', 'production', 'test'])
    .default('development'),
  PORT: z.coerce.number().int().positive().default(3000),
  LOG_LEVEL: z.string().default('info'),
  SERVICE_NAME: z.string().default('service-template'),
});

export type AppConfig = z.infer<typeof schema>;

/** Load + validate config from the environment (fail-fast). */
export function loadAppConfig(env: NodeJS.ProcessEnv = process.env): AppConfig {
  return loadConfig(schema, env);
}
