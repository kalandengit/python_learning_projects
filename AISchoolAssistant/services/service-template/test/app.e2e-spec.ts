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
