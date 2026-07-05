'use strict';

const http = require('http');
const express = require('express');
const cors = require('cors');
const { Server } = require('socket.io');
const { loadConfig } = require('./config');
const { logger } = require('./logger');
const { RoomRegistry } = require('./rooms');
const { registerHandlers } = require('./gateway');

/**
 * Build (but do not start) the HTTP + Socket.IO server. Exported so tests can
 * spin it up on an ephemeral port.
 */
function createServer(config = loadConfig()) {
  const app = express();
  app.disable('x-powered-by');
  app.use(cors({ origin: config.corsOrigins }));

  const registry = new RoomRegistry(config.maxRoomSize);

  app.get('/health', (_req, res) => {
    res.json({ status: 'ok', rooms: registry.rooms.size, timestamp: new Date().toISOString() });
  });

  const httpServer = http.createServer(app);
  const io = new Server(httpServer, {
    cors: { origin: config.corsOrigins, methods: ['GET', 'POST'] },
    // Reasonable ceiling so a client can't push huge frames through the socket.
    maxHttpBufferSize: 1e6,
  });

  registerHandlers(io, config, registry, logger);
  return { app, httpServer, io, registry, config };
}

/** Start listening and wire graceful shutdown. Only runs when executed directly. */
function start() {
  const { httpServer, io, config } = createServer();
  httpServer.listen(config.port, () => {
    logger.info(
      { port: config.port, env: config.nodeEnv, anonymous: config.allowAnonymous },
      'signaling server listening',
    );
  });

  const shutdown = (signal) => {
    logger.info({ signal }, 'shutting down');
    io.close();
    httpServer.close(() => process.exit(0));
    // Force-exit if connections linger.
    setTimeout(() => process.exit(1), 10_000).unref();
  };
  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
}

if (require.main === module) {
  start();
}

module.exports = { createServer, start };
