'use strict';

const jwt = require('jsonwebtoken');

const ROOM_ID_RE = /^[A-Za-z0-9_-]{1,100}$/;
const MAX_SIGNAL_BYTES = 64 * 1024; // guard against oversized SDP/candidate blobs
const MAX_CHAT_LEN = 2000;

/** Rough byte size of an arbitrary JSON-serialisable value. */
function byteSize(value) {
  try {
    return Buffer.byteLength(JSON.stringify(value ?? ''), 'utf8');
  } catch {
    return Infinity;
  }
}

function isValidRoomId(roomId) {
  return typeof roomId === 'string' && ROOM_ID_RE.test(roomId);
}

/**
 * Socket.IO authentication middleware. Verifies the JWT presented in the
 * handshake and pins the trusted `userId` onto the socket, so a client can
 * never spoof another user's id in event payloads.
 */
function authMiddleware(config, logger) {
  return (socket, next) => {
    const token =
      socket.handshake.auth?.token ||
      socket.handshake.headers?.authorization?.replace(/^Bearer\s+/i, '');

    if (!token) {
      if (config.allowAnonymous) {
        socket.data.userId = `anon-${socket.id}`;
        return next();
      }
      return next(new Error('unauthorized: missing token'));
    }

    try {
      const payload = jwt.verify(token, config.jwtSecret);
      socket.data.userId = String(payload.sub || payload.userId || socket.id);
      return next();
    } catch (err) {
      logger.warn({ err: err.message }, 'rejected socket: invalid token');
      return next(new Error('unauthorized: invalid token'));
    }
  };
}

/**
 * Register all signaling event handlers on the Socket.IO server.
 *
 * Relaying model: offers/answers/ICE candidates are forwarded to the rest of
 * the room untouched (this server never inspects media). The sender is always
 * the authenticated `socket.data.userId`, never a client-supplied field.
 */
function registerHandlers(io, config, registry, logger) {
  io.use(authMiddleware(config, logger));

  io.on('connection', (socket) => {
    const userId = socket.data.userId;
    logger.info({ socketId: socket.id, userId }, 'client connected');

    socket.on('join', (payload, ack) => {
      const roomId = payload?.roomId;
      if (!isValidRoomId(roomId)) {
        return typeof ack === 'function' && ack({ ok: false, error: 'invalid_room' });
      }
      const result = registry.join(roomId, socket.id, userId);
      if (!result.ok) {
        return typeof ack === 'function' && ack({ ok: false, error: result.reason });
      }
      socket.join(roomId);
      // Tell existing members someone joined; give the newcomer the roster.
      socket.to(roomId).emit('userJoined', { userId, socketId: socket.id });
      logger.info({ roomId, userId, size: registry.size(roomId) }, 'joined room');
      if (typeof ack === 'function') {
        ack({ ok: true, participants: result.participants });
      }
    });

    // Directed relays: forward to a specific target socket in the room.
    for (const type of ['offer', 'answer', 'iceCandidate']) {
      socket.on(type, (payload) => {
        const { roomId, target, data } = payload || {};
        if (!isValidRoomId(roomId) || byteSize(data) > MAX_SIGNAL_BYTES) return;
        const envelope = { from: socket.id, userId, data };
        if (target && typeof target === 'string') {
          io.to(target).emit(type, envelope);
        } else {
          socket.to(roomId).emit(type, envelope);
        }
      });
    }

    socket.on('chat', (payload) => {
      const { roomId, message } = payload || {};
      if (!isValidRoomId(roomId)) return;
      if (typeof message !== 'string' || message.length === 0) return;
      io.to(roomId).emit('chat', {
        userId,
        socketId: socket.id,
        message: message.slice(0, MAX_CHAT_LEN),
        at: new Date().toISOString(),
      });
    });

    socket.on('leave', (payload) => {
      const roomId = payload?.roomId;
      if (!isValidRoomId(roomId)) return;
      registry.leave(roomId, socket.id);
      socket.leave(roomId);
      socket.to(roomId).emit('userLeft', { userId, socketId: socket.id });
    });

    socket.on('disconnect', (reason) => {
      const left = registry.leaveAll(socket.id);
      for (const { roomId } of left) {
        socket.to(roomId).emit('userLeft', { userId, socketId: socket.id });
      }
      logger.info({ socketId: socket.id, userId, reason }, 'client disconnected');
    });
  });
}

module.exports = { registerHandlers, authMiddleware, isValidRoomId };
