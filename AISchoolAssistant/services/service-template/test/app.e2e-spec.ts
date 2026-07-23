import { INestApplication } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import request from 'supertest';
import { TOKEN_VERIFIER } from '@asa/auth';
import { AppModule } from '../src/app.module';
import { configureApp } from '../src/main';
import type { AppConfig } from '../src/config/app-config';
import {
  createAuthTestKit,
  TEST_AUDIENCE,
  TEST_CLIENT_ID,
  TEST_ISSUER,
  type TestKit,
} from './auth-testkit';

describe('Service template (e2e)', () => {
  let app: INestApplication;
  let kit: TestKit;

  const config: AppConfig = {
    NODE_ENV: 'test',
    PORT: 0,
    LOG_LEVEL: 'silent',
    SERVICE_NAME: 'service-template',
    AUTH_ENABLED: true,
    OIDC_ISSUER: TEST_ISSUER,
    OIDC_AUDIENCE: TEST_AUDIENCE,
    OIDC_JWKS_URI: 'https://issuer.test/jwks',
    OIDC_TENANT_CLAIM: 'tenant_id',
    OIDC_CLIENT_ID: TEST_CLIENT_ID,
  };

  beforeAll(async () => {
    // Configure the app to require auth; the real JWKS is replaced by a local
    // key set so tokens can be minted in-process.
    process.env.AUTH_ENABLED = 'true';
    process.env.OIDC_ISSUER = config.OIDC_ISSUER;
    process.env.OIDC_AUDIENCE = config.OIDC_AUDIENCE;
    process.env.OIDC_JWKS_URI = config.OIDC_JWKS_URI;
    process.env.OIDC_CLIENT_ID = config.OIDC_CLIENT_ID;
    process.env.OIDC_TENANT_CLAIM = config.OIDC_TENANT_CLAIM;

    kit = await createAuthTestKit();

    const moduleRef = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(TOKEN_VERIFIER)
      .useValue(kit.verifier)
      .compile();

    app = moduleRef.createNestApplication();
    configureApp(app, config);
    await app.init();
  });

  afterAll(async () => {
    await app.close();
    for (const key of [
      'AUTH_ENABLED',
      'OIDC_ISSUER',
      'OIDC_AUDIENCE',
      'OIDC_JWKS_URI',
      'OIDC_CLIENT_ID',
      'OIDC_TENANT_CLAIM',
    ]) {
      delete process.env[key];
    }
  });

  describe('public endpoints', () => {
    it('GET /api/v1/health/live returns ok without a token', async () => {
      const res = await request(app.getHttpServer()).get('/api/v1/health/live');
      expect(res.status).toBe(200);
      expect(res.body.status).toBe('ok');
    });

    it('GET /api/v1/health/ready returns ok without a token', async () => {
      const res = await request(app.getHttpServer()).get(
        '/api/v1/health/ready',
      );
      expect(res.status).toBe(200);
    });

    it('GET /metrics is public and exposes Prometheus metrics', async () => {
      const res = await request(app.getHttpServer()).get('/metrics');
      expect(res.status).toBe(200);
      expect(res.text).toContain('http_requests_total');
    });
  });

  describe('authentication', () => {
    it('rejects a protected route without a token (401 problem+json)', async () => {
      const res = await request(app.getHttpServer()).get('/api/v1/examples');
      expect(res.status).toBe(401);
      expect(res.headers['content-type']).toContain('application/problem+json');
      expect(res.body.type).toBe('urn:asa:error:unauthorized');
    });

    it('rejects a garbage bearer token', async () => {
      const res = await request(app.getHttpServer())
        .get('/api/v1/examples')
        .set('Authorization', 'Bearer not-a-real-token');
      expect(res.status).toBe(401);
    });

    it('accepts a valid token and returns data', async () => {
      const token = await kit.sign({ scope: 'openid examples:read' });
      const res = await request(app.getHttpServer())
        .get('/api/v1/examples')
        .set('Authorization', `Bearer ${token}`)
        .query({ page: 1, pageSize: 2 });
      expect(res.status).toBe(200);
      expect(res.body.total).toBe(3);
      expect(res.body.items).toHaveLength(2);
    });

    it('echoes a correlation id and returns the principal at /api/v1/me', async () => {
      const token = await kit.sign({
        sub: 'user-42',
        tenant_id: 'tenant-7',
        realm_access: { roles: ['teacher'] },
        scope: 'openid profile',
      });
      const res = await request(app.getHttpServer())
        .get('/api/v1/me')
        .set('Authorization', `Bearer ${token}`);
      expect(res.status).toBe(200);
      expect(res.body).toMatchObject({
        subject: 'user-42',
        tenantId: 'tenant-7',
        roles: ['teacher'],
      });
      expect(res.headers['x-correlation-id']).toBeDefined();
      expect(res.body.correlationId).toBe(res.headers['x-correlation-id']);
      // The ambient request context resolved the same tenant as the decorator,
      // proving AsyncLocalStorage propagation guard -> handler.
      expect(res.body.contextTenantId).toBe('tenant-7');
    });
  });

  describe('authorization (RBAC)', () => {
    it('forbids the admin route for a caller without the role (403)', async () => {
      const token = await kit.sign({ realm_access: { roles: ['teacher'] } });
      const res = await request(app.getHttpServer())
        .get('/api/v1/examples/admin/summary')
        .set('Authorization', `Bearer ${token}`);
      expect(res.status).toBe(403);
      expect(res.body.type).toBe('urn:asa:error:forbidden');
    });

    it('allows the admin route when the client role is present', async () => {
      const token = await kit.sign({
        resource_access: { [TEST_CLIENT_ID]: { roles: ['examples:admin'] } },
      });
      const res = await request(app.getHttpServer())
        .get('/api/v1/examples/admin/summary')
        .set('Authorization', `Bearer ${token}`);
      expect(res.status).toBe(200);
      expect(res.body).toEqual({ total: 3 });
    });
  });

  describe('ai capabilities', () => {
    it('rejects the capability endpoint without a token', async () => {
      const res = await request(app.getHttpServer())
        .post('/api/v1/ai/faq')
        .send({ question: 'hi' });
      expect(res.status).toBe(401);
    });

    it('invokes the faq capability and returns a typed answer', async () => {
      const token = await kit.sign();
      const res = await request(app.getHttpServer())
        .post('/api/v1/ai/faq')
        .set('Authorization', `Bearer ${token}`)
        .send({ question: 'When does term start?' });
      expect(res.status).toBe(201);
      expect(res.body.answer).toBe('[echo] When does term start?');
      expect(res.body.model).toBe('echo:default');
      expect(res.body.usage.totalTokens).toBeGreaterThan(0);
    });

    it('rejects an invalid capability request body (400)', async () => {
      const token = await kit.sign();
      const res = await request(app.getHttpServer())
        .post('/api/v1/ai/faq')
        .set('Authorization', `Bearer ${token}`)
        .send({ question: '' });
      expect(res.status).toBe(400);
    });
  });

  describe('agents', () => {
    it('rejects the agent endpoint without a token', async () => {
      const res = await request(app.getHttpServer())
        .post('/api/v1/agents/assistant/invoke')
        .send({ goal: 'hi' });
      expect(res.status).toBe(401);
    });

    it('runs the assistant agent and returns a result', async () => {
      const token = await kit.sign();
      const res = await request(app.getHttpServer())
        .post('/api/v1/agents/assistant/invoke')
        .set('Authorization', `Bearer ${token}`)
        .send({ goal: 'say hello' });
      expect(res.status).toBe(201);
      expect(res.body.output).toBe('[echo] say hello');
      expect(res.body.finishReason).toBe('completed');
      expect(res.body.model).toBe('echo:default');
    });

    it('returns 404 problem+json for an unknown agent', async () => {
      const token = await kit.sign();
      const res = await request(app.getHttpServer())
        .post('/api/v1/agents/nope/invoke')
        .set('Authorization', `Bearer ${token}`)
        .send({ goal: 'x' });
      expect(res.status).toBe(404);
      expect(res.body.type).toBe('urn:asa:error:not_found');
    });
  });

  describe('learner digital twin (event-driven)', () => {
    it('rejects recording activity without a token', async () => {
      const res = await request(app.getHttpServer())
        .post('/api/v1/learners/L1/lessons')
        .send({ lessonId: 'les-1', topic: 'algebra' });
      expect(res.status).toBe(401);
    });

    it('projects lessons and assessments into the twin via the bus', async () => {
      const token = await kit.sign();
      const auth = { Authorization: `Bearer ${token}` };

      await request(app.getHttpServer())
        .post('/api/v1/learners/L1/lessons')
        .set(auth)
        .send({ lessonId: 'les-1', topic: 'algebra' })
        .expect(201);

      const scored = await request(app.getHttpServer())
        .post('/api/v1/learners/L1/assessments')
        .set(auth)
        .send({ assessmentId: 'as-1', topic: 'algebra', score: 80 });
      expect(scored.status).toBe(201);
      expect(scored.body).toMatchObject({
        learnerId: 'L1',
        lessonsCompleted: 1,
        assessmentsTaken: 1,
        averageScore: 80,
      });
      expect(scored.body.masteryByTopic.algebra).toBe(80);

      const twin = await request(app.getHttpServer())
        .get('/api/v1/learners/L1/twin')
        .set(auth);
      expect(twin.status).toBe(200);
      expect(twin.body.lessonsCompleted).toBe(1);
    });

    it('returns 404 for a learner with no activity', async () => {
      const token = await kit.sign();
      const res = await request(app.getHttpServer())
        .get('/api/v1/learners/ghost/twin')
        .set('Authorization', `Bearer ${token}`);
      expect(res.status).toBe(404);
      expect(res.body.type).toBe('urn:asa:error:not_found');
    });

    it('rejects an out-of-range assessment score (400)', async () => {
      const token = await kit.sign();
      const res = await request(app.getHttpServer())
        .post('/api/v1/learners/L1/assessments')
        .set('Authorization', `Bearer ${token}`)
        .send({ assessmentId: 'as-2', topic: 'algebra', score: 150 });
      expect(res.status).toBe(400);
    });
  });

  describe('knowledge platform', () => {
    it('rejects search without a token', async () => {
      const res = await request(app.getHttpServer()).get(
        '/api/v1/knowledge/search?q=algebra',
      );
      expect(res.status).toBe(401);
    });

    it('ingests a document and retrieves it via semantic search', async () => {
      const token = await kit.sign();
      const auth = { Authorization: `Bearer ${token}` };

      const ingest = await request(app.getHttpServer())
        .post('/api/v1/knowledge/documents')
        .set(auth)
        .send({
          id: 'doc-1',
          text: 'Photosynthesis converts light into energy.',
        });
      expect(ingest.status).toBe(201);
      expect(ingest.body).toEqual({ ingested: 1 });

      const search = await request(app.getHttpServer())
        .get('/api/v1/knowledge/search')
        .set(auth)
        .query({ q: 'Photosynthesis converts light into energy.' });
      expect(search.status).toBe(200);
      expect(search.body.hits[0].id).toBe('doc-1');
      expect(search.body.hits[0].text).toContain('Photosynthesis');
    });

    it('requires a query parameter (400)', async () => {
      const token = await kit.sign();
      const res = await request(app.getHttpServer())
        .get('/api/v1/knowledge/search')
        .set('Authorization', `Bearer ${token}`);
      expect(res.status).toBe(400);
    });
  });

  describe('validation', () => {
    it('returns 404 problem+json for a missing example', async () => {
      const token = await kit.sign();
      const res = await request(app.getHttpServer())
        .get('/api/v1/examples/nope')
        .set('Authorization', `Bearer ${token}`);
      expect(res.status).toBe(404);
      expect(res.body.type).toBe('urn:asa:error:not_found');
    });

    it('rejects unknown query params with a 400 problem', async () => {
      const token = await kit.sign();
      const res = await request(app.getHttpServer())
        .get('/api/v1/examples')
        .set('Authorization', `Bearer ${token}`)
        .query({ bogus: 'x' });
      expect(res.status).toBe(400);
    });
  });
});
