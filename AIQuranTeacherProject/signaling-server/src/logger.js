'use strict';

const pino = require('pino');

// Structured JSON logs by default — no extra transport dependency required.
// Pipe through `pino-pretty` in a dev shell if you want colourised output:
//   npm start | npx pino-pretty
const logger = pino({ level: process.env.LOG_LEVEL || 'info' });

module.exports = { logger };
