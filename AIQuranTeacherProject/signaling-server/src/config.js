'use strict';

/**
 * Centralised, validated configuration for the signaling server.
 * Fails fast at startup if a production-critical value is missing.
 */
function loadConfig() {
  const nodeEnv = process.env.NODE_ENV || 'development';
  const allowAnonymous = process.env.ALLOW_ANONYMOUS === 'true';
  const jwtSecret = process.env.JWT_SECRET || '';

  if (nodeEnv === 'production' && !allowAnonymous && jwtSecret.length < 32) {
    throw new Error(
      'JWT_SECRET (>= 32 chars) is required in production unless ALLOW_ANONYMOUS=true.',
    );
  }

  return {
    nodeEnv,
    port: Number.parseInt(process.env.PORT || '3001', 10),
    jwtSecret,
    allowAnonymous,
    corsOrigins: (process.env.CORS_ORIGINS || 'http://localhost:3000')
      .split(',')
      .map((o) => o.trim())
      .filter(Boolean),
    maxRoomSize: Number.parseInt(process.env.MAX_ROOM_SIZE || '8', 10),
  };
}

module.exports = { loadConfig };
