import { Test } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { GamificationService } from '../gamification/gamification.service';
import { Quiz } from './quiz.entity';
import { QuizService } from './quiz.service';

describe('QuizService', () => {
  let service: QuizService;
  let store: Map<string, Quiz>;
  let gamification: {
    addXp: jest.Mock;
    updateStreak: jest.Mock;
    awardBadge: jest.Mock;
  };

  beforeEach(async () => {
    store = new Map();
    let nextId = 1;
    gamification = {
      addXp: jest.fn(),
      updateStreak: jest.fn(),
      awardBadge: jest.fn().mockResolvedValue(null),
    };

    const moduleRef = await Test.createTestingModule({
      providers: [
        QuizService,
        {
          provide: getRepositoryToken(Quiz),
          useValue: {
            create: (dto: Partial<Quiz>) => ({ ...dto }) as Quiz,
            save: async (quiz: Quiz) => {
              if (!quiz.id) quiz.id = `quiz-${nextId++}`;
              store.set(quiz.id, quiz);
              return quiz;
            },
            findOne: async ({ where: { id } }: any) => store.get(id) ?? null,
            find: async () => [...store.values()],
            count: async () => store.size,
          },
        },
        { provide: GamificationService, useValue: gamification },
      ],
    }).compile();
    service = moduleRef.get(QuizService);
  });

  it('serves questions without exposing the correct answers', async () => {
    const quiz = await service.generateQuiz('user-1', 'medium', 3);
    expect(quiz.questions).toHaveLength(3);
    for (const question of quiz.questions) {
      expect(question).not.toHaveProperty('correctIndex');
      expect(question).not.toHaveProperty('explanation');
      expect(question.options.length).toBeGreaterThanOrEqual(2);
    }
  });

  it('grades a submission and awards XP', async () => {
    const served = await service.generateQuiz('user-1', 'easy', 2);
    const stored = store.get(served.id)!;
    const answers = stored.questions.map((q) => q.correctIndex);

    const result = await service.submitQuiz(served.id, answers);
    expect(result.score).toBe(2);
    expect(result.total).toBe(2);
    expect(result.xpEarned).toBe(20);
    expect(gamification.addXp).toHaveBeenCalledWith('user-1', 20);
    expect(gamification.updateStreak).toHaveBeenCalledWith('user-1');
    expect(result.review.every((r) => r.correct)).toBe(true);
  });

  it('rejects double submission', async () => {
    const served = await service.generateQuiz('user-1', 'easy', 1);
    const stored = store.get(served.id)!;
    const answers = stored.questions.map((q) => q.correctIndex);
    await service.submitQuiz(served.id, answers);
    await expect(service.submitQuiz(served.id, answers)).rejects.toThrow(
      'already been submitted',
    );
  });

  it('awards the tajweed_master badge for a perfect hard quiz', async () => {
    gamification.awardBadge.mockResolvedValueOnce({ code: 'tajweed_master' });
    const served = await service.generateQuiz('user-1', 'hard', 2);
    const stored = store.get(served.id)!;
    const answers = stored.questions.map((q) => q.correctIndex);

    const result = await service.submitQuiz(served.id, answers);
    expect(gamification.awardBadge).toHaveBeenCalledWith(
      'user-1',
      'tajweed_master',
    );
    expect(result.newBadges).toContain('tajweed_master');
  });
});
