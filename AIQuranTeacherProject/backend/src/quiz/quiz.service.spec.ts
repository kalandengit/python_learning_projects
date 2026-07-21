import { BadRequestException, NotFoundException } from '@nestjs/common';
import { MistralService } from '../common/mistral/mistral.service';
import { GamificationService } from '../gamification/gamification.service';
import { QuizDifficulty } from './quiz.entity';
import { QuizService } from './quiz.service';

describe('QuizService', () => {
  let service: QuizService;
  let mistral: { chatJson: jest.Mock };
  let gamification: { awardQuizPoints: jest.Mock };
  let quizzes: { create: jest.Mock; save: jest.Mock; findOne: jest.Mock };
  let attempts: { create: jest.Mock; save: jest.Mock };

  const goodQuestion = (correctIndex: number) => ({
    prompt: 'What is Ikhfa?',
    options: ['A', 'B', 'C', 'D'],
    correctIndex,
    explanation: 'Because...',
  });

  beforeEach(() => {
    mistral = { chatJson: jest.fn() };
    gamification = { awardQuizPoints: jest.fn().mockResolvedValue(40) };
    quizzes = {
      create: jest.fn((x) => x),
      save: jest.fn(async (x) => ({
        id: 'quiz-1',
        createdAt: new Date(),
        ...x,
      })),
      findOne: jest.fn(),
    };
    attempts = {
      create: jest.fn((x) => x),
      save: jest.fn(async (x) => ({ id: 'attempt-1', ...x })),
    };
    service = new QuizService(
      quizzes as never,
      attempts as never,
      mistral as unknown as MistralService,
      gamification as unknown as GamificationService,
    );
  });

  it('generates a quiz and never exposes correct answers', async () => {
    mistral.chatJson.mockResolvedValue({
      questions: [
        goodQuestion(1),
        { prompt: 'bad', options: ['only', 'three', 'opts'], correctIndex: 0 },
      ],
    });

    const quiz = await service.generate('user-1', {
      difficulty: QuizDifficulty.Beginner,
      numQuestions: 5,
    });

    // The malformed 2nd question is dropped.
    expect(quiz.questions).toHaveLength(1);
    expect(quiz.questions[0]).not.toHaveProperty('correctIndex');
    expect(quiz.questions[0].options).toHaveLength(4);
  });

  it('rejects when no valid questions could be produced', async () => {
    mistral.chatJson.mockResolvedValue({ questions: [{ prompt: '' }] });
    await expect(
      service.generate('user-1', {
        difficulty: QuizDifficulty.Beginner,
        numQuestions: 3,
      }),
    ).rejects.toBeInstanceOf(BadRequestException);
  });

  it('grades a submission and awards points', async () => {
    quizzes.findOne.mockResolvedValue({
      id: 'quiz-1',
      userId: 'user-1',
      questions: [goodQuestion(2), goodQuestion(0)],
    });

    const result = await service.submit('user-1', 'quiz-1', {
      answers: [2, 3],
    });

    expect(result.correctCount).toBe(1);
    expect(result.totalCount).toBe(2);
    expect(result.results[0].correct).toBe(true);
    expect(result.results[1].correct).toBe(false);
    expect(gamification.awardQuizPoints).toHaveBeenCalledWith('user-1', 1, 2);
    expect(result.pointsAwarded).toBe(40);
  });

  it('rejects a submission with the wrong number of answers', async () => {
    quizzes.findOne.mockResolvedValue({
      id: 'quiz-1',
      userId: 'user-1',
      questions: [goodQuestion(0), goodQuestion(1)],
    });
    await expect(
      service.submit('user-1', 'quiz-1', { answers: [0] }),
    ).rejects.toBeInstanceOf(BadRequestException);
  });

  it("treats another user's quiz as not found", async () => {
    quizzes.findOne.mockResolvedValue({
      id: 'quiz-1',
      userId: 'someone-else',
      questions: [goodQuestion(0)],
    });
    await expect(
      service.submit('user-1', 'quiz-1', { answers: [0] }),
    ).rejects.toBeInstanceOf(NotFoundException);
  });
});
