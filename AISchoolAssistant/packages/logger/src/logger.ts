import pino, { type Logger, type LoggerOptions } from 'pino';

export type { Logger } from 'pino';

export interface CreateLoggerOptions {
  /** Service name, attached to every log line as `service`. */
  service: string;
  /** Log level; defaults to `LOG_LEVEL` env or `info`. */
  level?: string;
}

/** Paths redacted from every log to avoid leaking secrets/PII. */
const REDACT_PATHS = [
  'req.headers.authorization',
  'req.headers.cookie',
  'password',
  'token',
  'secret',
  'accessToken',
  'refreshToken',
  '*.password',
  '*.token',
  '*.secret',
];

/**
 * Create a structured JSON logger with a stable base context and secret
 * redaction. OpenTelemetry trace/span ids can be added by the caller via a
 * child logger once tracing is wired in.
 */
export function createLogger(options: CreateLoggerOptions): Logger {
  const config: LoggerOptions = {
    level: options.level ?? process.env.LOG_LEVEL ?? 'info',
    base: { service: options.service },
    timestamp: pino.stdTimeFunctions.isoTime,
    redact: { paths: REDACT_PATHS, censor: '[REDACTED]' },
    formatters: {
      level: (label) => ({ level: label }),
    },
  };
  return pino(config);
}
