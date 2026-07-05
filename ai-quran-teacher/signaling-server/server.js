const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');

const app = express();
app.use(cors());

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', rooms: rooms.size });
});

const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: process.env.ALLOWED_ORIGINS?.split(',') ?? '*',
    methods: ['GET', 'POST'],
  },
});

/** roomId -> Map<socketId, userId> */
const rooms = new Map();

function leaveRoom(socket, roomId) {
  const room = rooms.get(roomId);
  if (!room || !room.has(socket.id)) return;
  const userId = room.get(socket.id);
  room.delete(socket.id);
  if (room.size === 0) rooms.delete(roomId);
  socket.to(roomId).emit('userLeft', { userId, socketId: socket.id });
}

io.on('connection', (socket) => {
  console.log(`User connected: ${socket.id}`);

  socket.on('join', ({ roomId, userId }) => {
    if (!roomId || !userId) return;
    socket.join(roomId);
    if (!rooms.has(roomId)) {
      rooms.set(roomId, new Map());
    }
    const room = rooms.get(roomId);
    room.set(socket.id, userId);

    // Tell the newcomer who is already here so they can create offers.
    const participants = [...room.entries()]
      .filter(([socketId]) => socketId !== socket.id)
      .map(([socketId, existingUserId]) => ({
        socketId,
        userId: existingUserId,
      }));
    socket.emit('roomParticipants', { roomId, participants });
    socket.to(roomId).emit('userJoined', { userId, socketId: socket.id });
  });

  socket.on('leave', ({ roomId }) => {
    leaveRoom(socket, roomId);
    socket.leave(roomId);
  });

  // WebRTC negotiation: relay to a specific peer when `to` is given,
  // otherwise broadcast to the room (small classes).
  for (const event of ['offer', 'answer', 'iceCandidate']) {
    socket.on(event, (payload) => {
      const { roomId, to, ...rest } = payload ?? {};
      const message = { ...rest, socketId: socket.id };
      if (to) {
        io.to(to).emit(event, message);
      } else if (roomId) {
        socket.to(roomId).emit(event, message);
      }
    });
  }

  socket.on('chatMessage', ({ message, roomId, userId }) => {
    if (!roomId) return;
    socket.to(roomId).emit('chatMessage', {
      message,
      userId,
      socketId: socket.id,
      sentAt: new Date().toISOString(),
    });
  });

  socket.on('drawing', ({ drawing, roomId, userId }) => {
    if (!roomId) return;
    socket.to(roomId).emit('drawing', { drawing, userId, socketId: socket.id });
  });

  socket.on('disconnect', () => {
    console.log(`User disconnected: ${socket.id}`);
    for (const roomId of rooms.keys()) {
      leaveRoom(socket, roomId);
    }
  });
});

const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
  console.log(`Signaling server running on port ${PORT}`);
});

module.exports = { server, io, rooms };
