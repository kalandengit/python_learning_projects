'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { io: ioClient } = require('socket.io-client');
const { createServer } = require('../src/server');

/** Boot a server on an ephemeral port with anonymous auth for the test. */
function boot() {
  const config = {
    nodeEnv: 'test',
    port: 0,
    jwtSecret: '',
    allowAnonymous: true,
    corsOrigins: ['*'],
    maxRoomSize: 2,
  };
  const { httpServer, io } = createServer(config);
  return new Promise((resolve) => {
    httpServer.listen(0, () => {
      const { port } = httpServer.address();
      resolve({ url: `http://localhost:${port}`, httpServer, io });
    });
  });
}

function connect(url) {
  return new Promise((resolve, reject) => {
    const socket = ioClient(url, { transports: ['websocket'], forceNew: true });
    socket.on('connect', () => resolve(socket));
    socket.on('connect_error', reject);
  });
}

test('two clients can join a room and relay signaling', async (t) => {
  const { url, httpServer, io } = await boot();
  t.after(() => {
    io.close();
    httpServer.close();
  });

  const alice = await connect(url);
  const bob = await connect(url);
  t.after(() => {
    alice.close();
    bob.close();
  });

  // Alice joins first.
  const aliceJoin = await alice.emitWithAck('join', { roomId: 'class-1' });
  assert.strictEqual(aliceJoin.ok, true);
  assert.strictEqual(aliceJoin.participants.length, 1);

  // Bob joining should notify Alice via userJoined.
  const userJoined = new Promise((resolve) => alice.once('userJoined', resolve));
  const bobJoin = await bob.emitWithAck('join', { roomId: 'class-1' });
  assert.strictEqual(bobJoin.ok, true);
  assert.strictEqual(bobJoin.participants.length, 2);
  const joinedEvt = await userJoined;
  assert.ok(joinedEvt.socketId);

  // Alice sends an offer; Bob receives it with the sender stamped by the server.
  const offerReceived = new Promise((resolve) => bob.once('offer', resolve));
  alice.emit('offer', { roomId: 'class-1', data: { type: 'offer', sdp: 'v=0' } });
  const offer = await offerReceived;
  assert.strictEqual(offer.data.sdp, 'v=0');
  assert.ok(offer.from);
});

test('rooms enforce their capacity limit', async (t) => {
  const { url, httpServer, io } = await boot();
  t.after(() => {
    io.close();
    httpServer.close();
  });

  const a = await connect(url);
  const b = await connect(url);
  const c = await connect(url);
  t.after(() => {
    a.close();
    b.close();
    c.close();
  });

  await a.emitWithAck('join', { roomId: 'full-room' });
  await b.emitWithAck('join', { roomId: 'full-room' });
  const third = await c.emitWithAck('join', { roomId: 'full-room' });
  assert.strictEqual(third.ok, false);
  assert.strictEqual(third.error, 'room_full');
});

test('invalid room ids are rejected', async (t) => {
  const { url, httpServer, io } = await boot();
  t.after(() => {
    io.close();
    httpServer.close();
  });
  const s = await connect(url);
  t.after(() => s.close());

  const res = await s.emitWithAck('join', { roomId: 'bad room id!' });
  assert.strictEqual(res.ok, false);
  assert.strictEqual(res.error, 'invalid_room');
});
