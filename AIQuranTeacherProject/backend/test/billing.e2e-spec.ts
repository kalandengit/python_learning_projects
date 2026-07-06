import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import request from 'supertest';
import { DataSource } from 'typeorm';
import Stripe from 'stripe';
import { AppModule } from '../src/app.module';
import { MistralService } from '../src/common/mistral/mistral.service';
import { StripeService } from '../src/common/stripe/stripe.service';
import { User, UserRole } from '../src/users/user.entity';

/**
 * End-to-end tests for billing + the premium whitelist. Stripe is replaced with
 * a deterministic stub so no real keys or network are involved. The Mistral
 * client is stubbed too (unused here, but AppModule wires it).
 */
describe('Billing & whitelist (e2e)', () => {
  let app: INestApplication;
  let adminToken: string;
  let userToken: string;
  let userId: string;
  let adminId: string;

  // A stub webhook event for an unknown customer (handled + ignored -> 200).
  const stubEvent = {
    type: 'customer.subscription.updated',
    data: {
      object: {
        id: 'sub_1',
        customer: 'cus_unknown',
        status: 'active',
        items: { data: [] },
      },
    },
  } as unknown as Stripe.Event;

  const stripeStub: Partial<StripeService> = {
    isConfigured: () => true,
    constructWebhookEvent: (body, sig) => {
      if (sig !== 'valid-sig') throw new Error('bad signature');
      return stubEvent;
    },
  };

  beforeAll(async () => {
    process.env.NODE_ENV = 'test';
    process.env.DB_TYPE = 'sqlite';
    process.env.DB_DATABASE = ':memory:';
    process.env.DB_SYNCHRONIZE = 'true';
    process.env.JWT_SECRET = 'test-secret-that-is-at-least-32-chars-long!!';

    const moduleRef = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(StripeService)
      .useValue(stripeStub)
      .overrideProvider(MistralService)
      .useValue({ isConfigured: () => false })
      .compile();

    app = moduleRef.createNestApplication({ rawBody: true });
    app.setGlobalPrefix('api');
    app.useGlobalPipes(
      new ValidationPipe({
        whitelist: true,
        forbidNonWhitelisted: true,
        transform: true,
      }),
    );
    await app.init();

    // Register an admin-to-be and a normal user.
    const admin = await request(app.getHttpServer())
      .post('/api/auth/register')
      .send({
        email: 'admin@example.com',
        displayName: 'Admin',
        password: 'StrongPass123',
      });
    adminToken = admin.body.accessToken;
    adminId = admin.body.user.id;

    const user = await request(app.getHttpServer())
      .post('/api/auth/register')
      .send({
        email: 'learner@example.com',
        displayName: 'Learner',
        password: 'StrongPass123',
      });
    userToken = user.body.accessToken;
    userId = user.body.user.id;

    // Promote the admin user directly in the DB (role is read live by the guard).
    await app
      .get(DataSource)
      .getRepository(User)
      .update(adminId, { role: UserRole.Admin });
  });

  afterAll(async () => {
    await app?.close();
  });

  it('reports a fresh user as not premium', async () => {
    const res = await request(app.getHttpServer())
      .get('/api/billing/me')
      .set('Authorization', `Bearer ${userToken}`)
      .expect(200);
    expect(res.body.isPremium).toBe(false);
    expect(res.body.source).toBeNull();
  });

  it('forbids a non-admin from managing the whitelist', async () => {
    await request(app.getHttpServer())
      .post('/api/billing/whitelist')
      .set('Authorization', `Bearer ${userToken}`)
      .send({ userId, durationDays: 30 })
      .expect(403);
  });

  it('lets an admin grant free premium access for a defined period', async () => {
    const res = await request(app.getHttpServer())
      .post('/api/billing/whitelist')
      .set('Authorization', `Bearer ${adminToken}`)
      .send({ userId, durationDays: 7, reason: 'beta tester' })
      .expect(201);
    expect(res.body.active).toBe(true);
    expect(res.body.expiresAt).toBeGreaterThan(Math.floor(Date.now() / 1000));
  });

  it('now reports the whitelisted user as premium (source=whitelist)', async () => {
    const res = await request(app.getHttpServer())
      .get('/api/billing/me')
      .set('Authorization', `Bearer ${userToken}`)
      .expect(200);
    expect(res.body.isPremium).toBe(true);
    expect(res.body.source).toBe('whitelist');
  });

  it('lets an admin revoke the grant', async () => {
    await request(app.getHttpServer())
      .delete(`/api/billing/whitelist/${userId}`)
      .set('Authorization', `Bearer ${adminToken}`)
      .expect(200)
      .expect((r) => expect(r.body.revoked).toBe(true));

    const res = await request(app.getHttpServer())
      .get('/api/billing/me')
      .set('Authorization', `Bearer ${userToken}`)
      .expect(200);
    expect(res.body.isPremium).toBe(false);
  });

  it('rejects a webhook with no signature (400)', async () => {
    await request(app.getHttpServer())
      .post('/api/billing/webhook')
      .set('content-type', 'application/json')
      .send('{"id":"evt_test"}')
      .expect(400);
  });

  it('rejects a webhook with an invalid signature (400)', async () => {
    await request(app.getHttpServer())
      .post('/api/billing/webhook')
      .set('content-type', 'application/json')
      .set('stripe-signature', 'wrong')
      .send('{"id":"evt_test"}')
      .expect(400);
  });

  it('accepts a webhook with a valid signature (200)', async () => {
    await request(app.getHttpServer())
      .post('/api/billing/webhook')
      .set('content-type', 'application/json')
      .set('stripe-signature', 'valid-sig')
      .send('{"id":"evt_test"}')
      .expect(200)
      .expect((r) => expect(r.body.received).toBe(true));
  });
});
