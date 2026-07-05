import {
  BadRequestException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { GamificationService } from '../gamification/gamification.service';
import { QUESTION_BANK } from './question-bank';
import { Quiz, QuizDifficulty } from './quiz.entity';

const XP_PER_CORRECT_ANSWER = 10;

export interface ServedQuiz {
  id: string;
  difficulty: QuizDifficulty;
  questions: Array<{ id: string; question: string; options: string[] }>;
}

export interface QuizResult {
  quizId: string;
  score: number;
  total: number;
  xpEarned: number;
  newBadges: string[];
  review: Array<{
    questionId: string;
    correct: boolean;
    correctIndex: number;
    explanation: string;
  }>;
}

@Injectable()
export class QuizService {
  constructor(
    @InjectRepository(Quiz)
    private readonly quizRepository: Repository<Quiz>,
    private readonly gamificationService: GamificationService,
  ) {}

  /** Creates a quiz from the question bank; answers are stored server-side only. */
  async generateQuiz(
    userId: string,
    difficulty: QuizDifficulty = 'easy',
    count = 4,
  ): Promise<ServedQuiz> {
    const pool = QUESTION_BANK.filter((q) => q.difficulty === difficulty);
    if (pool.length === 0) {
      throw new BadRequestException(`No questions for difficulty ${difficulty}`);
    }
    const questions = shuffle(pool)
      .slice(0, Math.min(count, pool.length))
      .map(({ difficulty: _d, ...question }) => question);

    const quiz = await this.quizRepository.save(
      this.quizRepository.create({
        userId,
        difficulty,
        questions,
        score: null,
        completedAt: null,
      }),
    );

    return {
      id: quiz.id,
      difficulty: quiz.difficulty,
      questions: quiz.questions.map(({ id, question, options }) => ({
        id,
        question,
        options,
      })),
    };
  }

  /** Grades a quiz, records the score, and awards XP and badges. */
  async submitQuiz(quizId: string, answers: number[]): Promise<QuizResult> {
    const quiz = await this.quizRepository.findOne({ where: { id: quizId } });
    if (!quiz) {
      throw new NotFoundException(`Quiz ${quizId} not found`);
    }
    if (quiz.completedAt) {
      throw new BadRequestException('Quiz has already been submitted');
    }
    if (answers.length !== quiz.questions.length) {
      throw new BadRequestException(
        `Expected ${quiz.questions.length} answers, got ${answers.length}`,
      );
    }

    const review = quiz.questions.map((q, i) => ({
      questionId: q.id,
      correct: answers[i] === q.correctIndex,
      correctIndex: q.correctIndex,
      explanation: q.explanation,
    }));
    const score = review.filter((r) => r.correct).length;

    quiz.score = score;
    quiz.completedAt = new Date();
    await this.quizRepository.save(quiz);

    const xpEarned = score * XP_PER_CORRECT_ANSWER;
    await this.gamificationService.addXp(quiz.userId, xpEarned);
    await this.gamificationService.updateStreak(quiz.userId);

    const newBadges: string[] = [];
    if (quiz.difficulty === 'hard' && score === quiz.questions.length) {
      const badge = await this.gamificationService.awardBadge(
        quiz.userId,
        'tajweed_master',
      );
      if (badge) newBadges.push(badge.code);
    }
    const completedCount = await this.quizRepository.count({
      where: { userId: quiz.userId },
    });
    if (completedCount >= 10) {
      const badge = await this.gamificationService.awardBadge(
        quiz.userId,
        'quiz_champion',
      );
      if (badge) newBadges.push(badge.code);
    }

    return {
      quizId,
      score,
      total: quiz.questions.length,
      xpEarned,
      newBadges,
      review,
    };
  }

  getHistory(userId: string): Promise<Quiz[]> {
    return this.quizRepository.find({
      where: { userId },
      order: { createdAt: 'DESC' },
      take: 50,
    });
  }
}

function shuffle<T>(items: T[]): T[] {
  const result = [...items];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}
