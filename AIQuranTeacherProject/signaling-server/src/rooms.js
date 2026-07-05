'use strict';

/**
 * In-memory room registry for live classes.
 *
 * NOTE: this holds state in a single process. To scale horizontally across
 * multiple signaling instances, back Socket.IO with the Redis adapter
 * (@socket.io/redis-adapter) and move this membership map into Redis so any
 * instance can resolve room state. The interface below is intentionally small
 * to make that swap straightforward.
 */
class RoomRegistry {
  constructor(maxRoomSize) {
    this.maxRoomSize = maxRoomSize;
    /** @type {Map<string, Map<string, { userId: string }>>} roomId -> (socketId -> member) */
    this.rooms = new Map();
  }

  /** @returns {{ ok: true, participants: Array } | { ok: false, reason: string }} */
  join(roomId, socketId, userId) {
    let room = this.rooms.get(roomId);
    if (!room) {
      room = new Map();
      this.rooms.set(roomId, room);
    }
    if (!room.has(socketId) && room.size >= this.maxRoomSize) {
      return { ok: false, reason: 'room_full' };
    }
    room.set(socketId, { userId });
    return { ok: true, participants: this.participants(roomId) };
  }

  leave(roomId, socketId) {
    const room = this.rooms.get(roomId);
    if (!room) return null;
    const member = room.get(socketId);
    room.delete(socketId);
    if (room.size === 0) {
      this.rooms.delete(roomId);
    }
    return member ? member.userId : null;
  }

  /** Remove a socket from every room it belonged to (used on disconnect). */
  leaveAll(socketId) {
    const left = [];
    for (const [roomId, room] of this.rooms) {
      if (room.has(socketId)) {
        const userId = room.get(socketId).userId;
        room.delete(socketId);
        if (room.size === 0) this.rooms.delete(roomId);
        left.push({ roomId, userId });
      }
    }
    return left;
  }

  participants(roomId) {
    const room = this.rooms.get(roomId);
    if (!room) return [];
    return [...room.entries()].map(([socketId, m]) => ({
      socketId,
      userId: m.userId,
    }));
  }

  size(roomId) {
    return this.rooms.get(roomId)?.size ?? 0;
  }
}

module.exports = { RoomRegistry };
