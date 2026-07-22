import { INestApplication } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import request from 'supertest';
import { AppModule } from '../src/app.module';
import { configureApp } from '../src/main';
import type { AppConfig } from '../src/config/app-config';

describe('Service template (e2e)', () => {
  let app: INestApplication;

  const config: AppConfig = {
    NODE_ENV: 'test',
    PORT: 0,
    LOG_LEVEL: 'silent',
    SERVICE_NAME: 'service-template',
  };

  beforeAll(async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleRef.createNestApplication();
    configureApp(app, config);
    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  it('GET /api/v1/health/live returns ok', async () => {
    const res = await request(app.getHttpServer()).get('/api/v1/health/live');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('ok');
  });

  it('GET /api/v1/health/ready returns ok', async () => {
    const res = await request(app.getHttpServer()).get('/api/v1/health/ready');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('ok');
  });

  it('GET /metrics exposes Prometheus metrics at the root', async () => {
    const res = await request(app.getHttpServer()).get('/metrics');
    expect(res.status).toBe(200);
    expect(res.text).toContain('http_requests_total');
  });

  it('GET /api/v1/examples returns a page envelope', async () => {
    const res = await request(app.getHttpServer())
      .get('/api/v1/examples')
      .query({ page: 1, pageSize: 2 });
    expect(res.status).toBe(200);
    expect(res.body.total).toBe(3);
    expect(res.body.items).toHaveLength(2);
  });

  it('GET /api/v1/examples/:id returns problem+json when missing', async () => {
    const res = await request(app.getHttpServer()).get('/api/v1/examples/nope');
    expect(res.status).toBe(404);
    expect(res.headers['content-type']).toContain('application/problem+json');
    expect(res.body.type).toBe('urn:asa:error:not_found');
    expect(res.body.instance).toBe('/api/v1/examples/nope');
  });

  it('rejects unknown query params with a 400 problem', async () => {
    const res = await request(app.getHttpServer())
      .get('/api/v1/examples')
      .query({ bogus: 'x' });
    expect(res.status).toBe(400);
    expect(res.body.status).toBe(400);
  });
});
