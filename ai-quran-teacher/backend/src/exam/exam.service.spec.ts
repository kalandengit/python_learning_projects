import { Test } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { IsNull } from 'typeorm';
import { GamificationService } from '../gamification/gamification.service';
import { Certificate, Exam } from './exam.entity';
import { ExamService } from './exam.service';

describe('ExamService', () => {
  let service: ExamService;
  let exams: Map<string, Exam>;
  let certificates: Certificate[];
  let gamification: {
    addXp: jest.Mock;
    updateStreak: jest.Mock;
    awardBadge: jest.Mock;
  };

  beforeEach(async () => {
    exams = new Map();
    certificates = [];
    let nextId = 1;
    gamification = {
      addXp: jest.fn(),
      updateStreak: jest.fn(),
      awardBadge: jest.fn().mockResolvedValue(null),
    };

    const moduleRef = await Test.createTestingModule({
      providers: [
        ExamService,
        {
          provide: getRepositoryToken(Exam),
          useValue: {
            create: (dto: Partial<Exam>) => ({ ...dto }) as Exam,
            save: async (exam: Exam) => {
              if (!exam.id) exam.id = `exam-${nextId++}`;
              if (!exam.startedAt) exam.startedAt = new Date();
              exams.set(exam.id, exam);
              return exam;
            },
            findOne: async ({ where }: any) => {
              const entries = [...exams.values()];
              if (where.id) return exams.get(where.id) ?? null;
              // Simulate the active-exam lookup (completedAt IS NULL).
              if (where.userId && where.completedAt instanceof Object) {
                return (
                  entries.find(
                    (e) => e.userId === where.userId && e.completedAt === null,
                  ) ?? null
                );
              }
              return null;
            },
            find: async () => [...exams.values()],
            count: async () => exams.size,
          },
        },
        {
          provide: getRepositoryToken(Certificate),
          useValue: {
            create: (dto: Partial<Certificate>) => ({ ...dto }) as Certificate,
            save: async (cert: Certificate) => {
              cert.id = `cert-${certificates.length + 1}`;
              cert.issuedAt = new Date();
              certificates.push(cert);
              return cert;
            },
            find: async () => certificates,
            findOne: async ({ where }: any) =>
              certificates.find(
                (c) => c.verificationCode === where.verificationCode,
              ) ?? null,
          },
        },
        { provide: GamificationService, useValue: gamification },
      ],
    }).compile();
    service = moduleRef.get(ExamService);
    // Guard against the IsNull import being unused in some ts configs.
    void IsNull;
  });

  it('starts a foundation exam with the right question count and deadline', async () => {
    const served = await service.startExam('user-1', 'foundation');
    expect(served.level).toBe('foundation');
    expect(served.questions.length).toBeGreaterThan(0);
    expect(served.questions.length).toBeLessThanOrEqual(8);
    expect(served.passPercent).toBe(70);
    expect(served.expiresAt.getTime()).toBeGreaterThan(served.startedAt.getTime());
    for (const q of served.questions) {
      expect(q).not.toHaveProperty('correctIndex');
    }
  });

  it('issues a certificate when the student passes', async () => {
    const served = await service.startExam('user-1', 'foundation');
    const stored = exams.get(served.id)!;
    const answers = stored.questions.map((q) => q.correctIndex);

    const result = await service.submitExam(served.id, answers);
    expect(result.passed).toBe(true);
    expect(result.percent).toBe(100);
    expect(result.certificate).not.toBeNull();
    expect(gamification.awardBadge).toHaveBeenCalledWith(
      'user-1',
      'certified_foundation',
    );
  });

  it('fails a mostly-wrong submission and issues no certificate', async () => {
    const served = await service.startExam('user-1', 'foundation');
    const stored = exams.get(served.id)!;
    // Deliberately wrong answers.
    const answers = stored.questions.map((q) => (q.correctIndex + 1) % 4);

    const result = await service.submitExam(served.id, answers);
    expect(result.passed).toBe(false);
    expect(result.certificate).toBeNull();
  });

  it('verifies an issued certificate by code', async () => {
    const served = await service.startExam('user-1', 'foundation');
    const stored = exams.get(served.id)!;
    const answers = stored.questions.map((q) => q.correctIndex);
    const result = await service.submitExam(served.id, answers);

    const verification = await service.verifyCertificate(
      result.certificate!.verificationCode,
    );
    expect(verification.valid).toBe(true);
  });

  it('rejects an unknown verification code', async () => {
    const verification = await service.verifyCertificate('does-not-exist');
    expect(verification.valid).toBe(false);
  });

  it('records a late submission as expired and non-passing', async () => {
    const served = await service.startExam('user-1', 'advanced');
    const stored = exams.get(served.id)!;
    // Backdate the start beyond the allowed duration.
    stored.startedAt = new Date(Date.now() - 60 * 60_000);
    const answers = stored.questions.map((q) => q.correctIndex);

    const result = await service.submitExam(served.id, answers);
    expect(result.expired).toBe(true);
    expect(result.passed).toBe(false);
  });
});
