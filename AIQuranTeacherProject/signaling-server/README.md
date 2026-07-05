# AI Quran Teacher — Signaling Server

A hardened WebRTC signaling server (Socket.IO) that brokers SDP offers/answers
and ICE candidates for live classes. Media flows peer-to-peer; this server only
coordinates the handshake.

## Features

- **JWT-authenticated** WebSocket handshake (shares the backend's `JWT_SECRET`);
  the trusted `userId` is pinned server-side so it can't be spoofed.
- **Room management** with capacity limits and roster tracking.
- **Validated payloads** — room-id regex, SDP/ICE size caps, chat length caps.
- **Directed and broadcast relays** for `offer` / `answer` / `iceCandidate`.
- **Structured logging** (pino), `/health` endpoint, graceful shutdown.

## Quick start

```bash
cp .env.example .env    # set JWT_SECRET to match the backend
npm install
npm start               # ws://localhost:3001
npm test                # node:test integration tests
```

For local development without tokens, set `ALLOW_ANONYMOUS=true` (never in prod).

## Client events

| Event | Direction | Payload | Notes |
| --- | --- | --- | --- |
| `join` | client → server | `{ roomId }` (ack: `{ ok, participants }`) | Join a room |
| `userJoined` / `userLeft` | server → clients | `{ userId, socketId }` | Roster changes |
| `offer` / `answer` / `iceCandidate` | client ↔ clients | `{ roomId, target?, data }` | Relayed; `from` is stamped by server |
| `chat` | client ↔ clients | `{ roomId, message }` | Broadcast to room |
| `leave` | client → server | `{ roomId }` | Leave a room |

Authenticate by passing the JWT in the handshake:

```js
import { io } from 'socket.io-client';
const socket = io('wss://signaling.example.com', { auth: { token: jwt } });
const { participants } = await socket.emitWithAck('join', { roomId: 'class-42' });
```

## Scaling

Room state is in-process. To run multiple instances, add
`@socket.io/redis-adapter` so events fan out across pods and move the
`RoomRegistry` into Redis. Deploy STUN/TURN (e.g. coturn) for NAT traversal.
