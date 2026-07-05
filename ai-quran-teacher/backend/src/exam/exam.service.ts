import {
  BadRequestException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { randomBytes } from 'crypto';
import { InjectRepository } from '@nestjs/typeorm';
import { IsNull, Repository } from 'typeorm';
import { GamificationService } from '../gamification/gamification.service';
import { QUESTION_BANK } from '../quiz/question-bank';
import { QuizDifficulty } from '../quiz/quiz.entity';
import { Certificate, EXAM_RULES, Exam, ExamLevel } from './exam.entity';

const XP_PER_CORRECT_ANSWER = 15;
const PASS_XP_BONUS = 100;

const LEVEL_POOLS: Record<ExamLevel, QuizDifficulty[]> = {
  foundation: ['easy'],
  intermediate: ['easy', 'medium'],
  advanced: ['medium', 'hard'],
};

export interface ServedExam {
  id: string;
  level: ExamLevel;
  durationMinutes: number;
  startedAt: Date;
  expiresAt: Date;
  passPercent: number;
  questions: Array<{ id: string; question: string; options: string[] }>;
}

export interface ExamResult {
  examId: string;
  level: ExamLevel;
  score: number;
  total: number;
  percent: number;
  passed: boolean;
  expired: boolean;
  xpEarned: number;
  certificate: Certificate | null;
  review: Array<{
    questionId: string;
    correct: boolean;
    correctIndex: number;
    explanation: string;
  }>;
}

@Injectable()
export class ExamService {
  constructor(
    @InjectRepository(Exam)
    private readonly examRepository: Repository<Exam>,
    @InjectRepository(Certificate)
    private readonly certificateRepository: Repository<Certificate>,
    private readonly gamificationService: GamificationService,
  ) {}

  /**
   * Starts a timed exam. Only one exam may be in progress per user;
   * an in-progress exam whose deadline passed is auto-expired first.
   */
  async startExam(userId: string, level: ExamLevel): Promise<ServedExam> {
    const active = await this.examRepository.findOne({
      where: { userId, completedAt: IsNull() },
    });
    if (active) {
      if (this.deadline(active) > new Date()) {
        throw new BadRequestException(
          `An exam is already in progress (id ${active.id}); submit it first.`,
        );
      }
      active.completedAt = new Date();
      active.expired = true;
      active.passed = false;
      active.score = 0;
      await this.examRepository.save(active);
    }

    const rules = EXAM_RULES[level];
    const pool = QUESTION_BANK.filter((q) =>
      LEVEL_POOLS[level].includes(q.difficulty),
    );
    const questions = shuffle(pool)
      .slice(0, Math.min(rules.questionCount, pool.length))
      .map(({ difficulty: _d, ...question }) => question);

    const exam = await this.examRepository.save(
      this.examRepository.create({
        userId,
        level,
        questions,
        durationMinutes: rules.durationMinutes,
        completedAt: null,
        score: null,
        passed: null,
        expired: false,
        certificateId: null,
      }),
    );

    return {
      id: exam.id,
      level,
      durationMinutes: rules.durationMinutes,
      startedAt: exam.startedAt,
      expiresAt: this.deadline(exam),
      passPercent: rules.passPercent,
      questions: exam.questions.map(({ id, question, options }) => ({
        id,
        question,
        options,
      })),
    };
  }

  /** Grades a submission; late submissions are recorded but cannot pass. */
  async submitExam(examId: string, answers: number[]): Promise<ExamResult> {
    const exam = await this.examRepository.findOne({ where: { id: examId } });
    if (!exam) {
      throw new NotFoundException(`Exam ${examId} not found`);
    }
    if (exam.completedAt) {
      throw new BadRequestException('Exam has already been submitted');
    }
    if (answers.length !== exam.questions.length) {
      throw new BadRequestException(
        `Expected ${exam.questions.length} answers, got ${answers.length}`,
      );
    }

    const now = new Date();
    const expired = now > this.deadline(exam);

    const review = exam.questions.map((q, i) => ({
      questionId: q.id,
      correct: answers[i] === q.correctIndex,
      correctIndex: q.correctIndex,
      explanation: q.explanation,
    }));
    const score = review.filter((r) => r.correct).length;
    const percent = Math.round((score / exam.questions.length) * 100);
    const rules = EXAM_RULES[exam.level];
    const passed = !expired && percent >= rules.passPercent;

    exam.completedAt = now;
    exam.score = score;
    exam.passed = passed;
    exam.expired = expired;

    let certificate: Certificate | null = null;
    if (passed) {
      certificate = await this.certificateRepository.save(
        this.certificateRepository.create({
          userId: exam.userId,
          examId: exam.id,
          level: exam.level,
          verificationCode: randomBytes(8).toString('hex'),
        }),
      );
      exam.certificateId = certificate.id;
      await this.gamificationService.awardBadge(
        exam.userId,
        `certified_${exam.level}`,
      );
    }
    await this.examRepository.save(exam);

    const xpEarned = score * XP_PER_CORRECT_ANSWER + (passed ? PASS_XP_BONUS : 0);
    await this.gamificationService.addXp(exam.userId, xpEarned);
    await this.gamificationService.updateStreak(exam.userId);

    return {
      examId,
      level: exam.level,
      score,
      total: exam.questions.length,
      percent,
      passed,
      expired,
      xpEarned,
      certificate,
      review,
    };
  }

  getCertificates(userId: string): Promise<Certificate[]> {
    return this.certificateRepository.find({
      where: { userId },
      order: { issuedAt: 'DESC' },
    });
  }

  /** Public verification for employers/institutes. */
  async verifyCertificate(code: string) {
    const certificate = await this.certificateRepository.findOne({
      where: { verificationCode: code },
    });
    if (!certificate) {
      return { valid: false as const };
    }
    return {
      valid: true as const,
      level: certificate.level,
      issuedAt: certificate.issuedAt,
      certificateId: certificate.id,
    };
  }

  getHistory(userId: string): Promise<Exam[]> {
    return this.examRepository.find({
      where: { userId },
      order: { startedAt: 'DESC' },
      take: 50,
    });
  }

  private deadline(exam: Exam): Date {
    return new Date(exam.startedAt.getTime() + exam.durationMinutes * 60_000);
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
