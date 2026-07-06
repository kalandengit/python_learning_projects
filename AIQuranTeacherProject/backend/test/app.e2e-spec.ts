import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import request from 'supertest';
import { AppModule } from '../src/app.module';
import { MistralService } from '../src/common/mistral/mistral.service';

/**
 * End-to-end smoke test running the whole Nest app against an in-memory SQLite
 * database. The Mistral client is replaced with a deterministic stub so the AI
 * endpoints are exercised without any network calls.
 */
describe('AI Quran Teacher API (e2e)', () => {
  let app: INestApplication;
  let token: string;

  const mistralStub: Partial<MistralService> = {
    isConfigured: () => true,
    chatJson: (async () => ({
      questions: [
        {
          prompt: 'What does Ikhfa mean?',
          options: ['Hiding', 'Merging', 'Clarifying', 'Converting'],
          correctIndex: 0,
          explanation: 'Ikhfa means to conceal the noon sound.',
        },
      ],
    })) as MistralService['chatJson'],
  };

  beforeAll(async () => {
    process.env.NODE_ENV = 'test';
    process.env.DB_TYPE = 'sqlite';
    process.env.DB_DATABASE = ':memory:';
    process.env.DB_SYNCHRONIZE = 'true';
    process.env.JWT_SECRET = 'test-secret-that-is-at-least-32-chars-long!!';
    process.env.MISTRAL_API_KEY = 'test-key';

    const moduleRef = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(MistralService)
      .useValue(mistralStub)
      .compile();

    app = moduleRef.createNestApplication();
    app.setGlobalPrefix('api');
    app.useGlobalPipes(
      new ValidationPipe({
        whitelist: true,
        forbidNonWhitelisted: true,
        transform: true,
      }),
    );
    await app.init();
  });

  afterAll(async () => {
    await app?.close();
  });

  it('GET /api/health returns ok', async () => {
    const res = await request(app.getHttpServer())
      .get('/api/health')
      .expect(200);
    expect(res.body.status).toBe('ok');
  });

  it('GET /api/quran/surahs returns the seeded surahs', async () => {
    const res = await request(app.getHttpServer())
      .get('/api/quran/surahs')
      .expect(200);
    expect(res.body.length).toBeGreaterThanOrEqual(2);
    expect(res.body[0]).toHaveProperty('nameTransliteration', 'Al-Fatihah');
  });

  it('rejects an unauthenticated protected route', async () => {
    await request(app.getHttpServer()).get('/api/gamification/me').expect(401);
  });

  it('rejects a forged "none"-algorithm JWT (alg-confusion mitigation)', async () => {
    // Craft an unsigned token with alg=none — must be refused because the
    // strategy pins algorithms to HS256.
    const b64 = (o: object) =>
      Buffer.from(JSON.stringify(o)).toString('base64url');
    const forged =
      `${b64({ alg: 'none', typ: 'JWT' })}.` +
      `${b64({ sub: 'attacker', email: 'attacker@example.com' })}.`;
    await request(app.getHttpServer())
      .get('/api/gamification/me')
      .set('Authorization', `Bearer ${forged}`)
      .expect(401);
  });

  it('registers a user and returns a token', async () => {
    const res = await request(app.getHttpServer())
      .post('/api/auth/register')
      .send({
        email: 'learner@example.com',
        displayName: 'Learner',
        password: 'StrongPass123',
      })
      .expect(201);
    expect(res.body.accessToken).toBeDefined();
    token = res.body.accessToken;
  });

  it('rejects a weak password at registration', async () => {
    await request(app.getHttpServer())
      .post('/api/auth/register')
      .send({
        email: 'weak@example.com',
        displayName: 'Weak',
        password: 'short',
      })
      .expect(400);
  });

  it('returns the current user from /api/auth/me', async () => {
    const res = await request(app.getHttpServer())
      .get('/api/auth/me')
      .set('Authorization', `Bearer ${token}`)
      .expect(200);
    expect(res.body.email).toBe('learner@example.com');
    expect(res.body).not.toHaveProperty('passwordHash');
  });

  it('generates a quiz, hides answers, and grades a submission', async () => {
    const gen = await request(app.getHttpServer())
      .post('/api/quiz/generate')
      .set('Authorization', `Bearer ${token}`)
      .send({ difficulty: 'beginner', numQuestions: 1 })
      .expect(201);

    expect(gen.body.questions[0]).not.toHaveProperty('correctIndex');
    const quizId = gen.body.id;

    const submit = await request(app.getHttpServer())
      .post(`/api/quiz/${quizId}/submit`)
      .set('Authorization', `Bearer ${token}`)
      .send({ answers: [0] })
      .expect(201);

    expect(submit.body.correctCount).toBe(1);
    expect(submit.body.pointsAwarded).toBeGreaterThan(0);
  });

  it('reflects earned points on the gamification profile', async () => {
    const res = await request(app.getHttpServer())
      .get('/api/gamification/me')
      .set('Authorization', `Bearer ${token}`)
      .expect(200);
    expect(res.body.points).toBeGreaterThan(0);
    expect(res.body.currentStreak).toBe(1);
  });
});
