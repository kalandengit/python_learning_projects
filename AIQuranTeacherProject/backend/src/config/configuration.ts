/**
 * Strongly-typed application configuration, loaded once at bootstrap.
 *
 * Values are read from environment variables (already validated by
 * {@link ./env.validation.ts}) and exposed through the Nest `ConfigService`
 * using the `config.get('namespace.key')` convention.
 */
export interface AppConfig {
  nodeEnv: string;
  port: number;
  corsOrigins: string[];
}

export interface DatabaseConfig {
  type: 'sqlite' | 'postgres';
  url?: string;
  database: string;
  host?: string;
  port?: number;
  username?: string;
  password?: string;
  ssl: boolean;
  synchronize: boolean;
}

export interface JwtConfig {
  secret: string;
  expiresIn: string;
}

export interface MistralConfig {
  apiKey: string;
  apiUrl: string;
  model: string;
  timeoutMs: number;
}

export interface ThrottleConfig {
  ttlMs: number;
  limit: number;
}

export interface StripeConfig {
  secretKey: string;
  webhookSecret: string;
  publishableKey: string;
  /** Allow-listed price IDs, keyed by plan. Clients pick a plan, never a price. */
  prices: Record<string, string>;
  successUrl: string;
  cancelUrl: string;
  portalReturnUrl: string;
}

export interface Configuration {
  app: AppConfig;
  database: DatabaseConfig;
  jwt: JwtConfig;
  mistral: MistralConfig;
  throttle: ThrottleConfig;
  stripe: StripeConfig;
}

const toBool = (value: string | undefined, fallback = false): boolean => {
  if (value === undefined) return fallback;
  return ['1', 'true', 'yes', 'on'].includes(value.toLowerCase());
};

const toInt = (value: string | undefined, fallback: number): number => {
  const parsed = Number.parseInt(value ?? '', 10);
  return Number.isFinite(parsed) ? parsed : fallback;
};

export default (): Configuration => ({
  app: {
    nodeEnv: process.env.NODE_ENV ?? 'development',
    port: toInt(process.env.PORT, 3000),
    corsOrigins: (process.env.CORS_ORIGINS ?? 'http://localhost:3000')
      .split(',')
      .map((o) => o.trim())
      .filter(Boolean),
  },
  database: {
    type: (process.env.DB_TYPE as 'sqlite' | 'postgres') ?? 'sqlite',
    url: process.env.DATABASE_URL,
    database: process.env.DB_DATABASE ?? 'aiquran.sqlite',
    host: process.env.DB_HOST,
    port: toInt(process.env.DB_PORT, 5432),
    username: process.env.DB_USERNAME,
    password: process.env.DB_PASSWORD,
    ssl: toBool(process.env.DB_SSL, false),
    synchronize: toBool(process.env.DB_SYNCHRONIZE, false),
  },
  jwt: {
    secret: process.env.JWT_SECRET ?? '',
    expiresIn: process.env.JWT_EXPIRES_IN ?? '3600s',
  },
  mistral: {
    apiKey: process.env.MISTRAL_API_KEY ?? '',
    apiUrl: process.env.MISTRAL_API_URL ?? 'https://api.mistral.ai/v1',
    model: process.env.MISTRAL_MODEL ?? 'mistral-large-latest',
    timeoutMs: toInt(process.env.MISTRAL_TIMEOUT_MS, 30000),
  },
  throttle: {
    ttlMs: toInt(process.env.THROTTLE_TTL_MS, 60000),
    limit: toInt(process.env.THROTTLE_LIMIT, 120),
  },
  stripe: {
    secretKey: process.env.STRIPE_SECRET_KEY ?? '',
    webhookSecret: process.env.STRIPE_WEBHOOK_SECRET ?? '',
    publishableKey: process.env.STRIPE_PUBLISHABLE_KEY ?? '',
    // Map friendly plan names to Stripe price IDs (server-side allow-list).
    prices: {
      premium_monthly: process.env.STRIPE_PRICE_PREMIUM_MONTHLY ?? '',
      premium_yearly: process.env.STRIPE_PRICE_PREMIUM_YEARLY ?? '',
    },
    successUrl:
      process.env.STRIPE_SUCCESS_URL ??
      'http://localhost:3000/billing/success?session_id={CHECKOUT_SESSION_ID}',
    cancelUrl:
      process.env.STRIPE_CANCEL_URL ?? 'http://localhost:3000/billing/cancel',
    portalReturnUrl:
      process.env.STRIPE_PORTAL_RETURN_URL ?? 'http://localhost:3000/billing',
  },
});
