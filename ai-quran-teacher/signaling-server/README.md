# AI Quran Teacher — Signaling Server

Node.js + Socket.IO signaling for WebRTC live classes.

## Events

| Event | Direction | Payload |
|---|---|---|
| `join` | client → server | `{ roomId, userId }` |
| `roomParticipants` | server → newcomer | `{ roomId, participants: [{socketId, userId}] }` |
| `userJoined` / `userLeft` | server → room | `{ userId, socketId }` |
| `offer` / `answer` | relayed | `{ sdp, roomId, userId, to? }` — with `to`, sent to that peer only |
| `iceCandidate` | relayed | `{ candidate, roomId, userId, to? }` |
| `chatMessage` | relayed | `{ message, roomId, userId }` (+ `sentAt` added) |
| `drawing` | relayed | `{ drawing: { points, color }, roomId, userId }` |
| `leave` | client → server | `{ roomId }` |

`GET /health` returns `{ status, rooms }` for load balancers.

## Running

```bash
npm install
PORT=3001 npm start
```

Set `ALLOWED_ORIGINS` (comma-separated) in production instead of the default
`*` CORS policy.
