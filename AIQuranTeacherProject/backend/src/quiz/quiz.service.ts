import {
  BadRequestException,
  Injectable,
  Logger,
  NotFoundException,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { ChatMessage, MistralService } from '../common/mistral/mistral.service';
import { GamificationService } from '../gamification/gamification.service';
import { GenerateQuizDto } from './dto/generate-quiz.dto';
import { SubmitQuizDto } from './dto/submit-quiz.dto';
import { Quiz, QuizAttempt, QuizQuestion } from './quiz.entity';

/** Quiz as exposed to clients — correct answers stripped out. */
export interface PublicQuiz {
  id: string;
  topic: string;
  difficulty: string;
  createdAt: Date;
  questions: Array<{ prompt: string; options: string[] }>;
}

export interface QuizResult {
  attemptId: string;
  correctCount: number;
  totalCount: number;
  pointsAwarded: number;
  results: Array<{
    prompt: string;
    chosenIndex: number;
    correctIndex: number;
    correct: boolean;
    explanation: string;
  }>;
}

interface AiQuiz {
  questions: QuizQuestion[];
}

const SYSTEM_PROMPT = `You are a Quran and tajweed teacher creating a multiple-choice quiz.
Respond ONLY with a JSON object of this exact shape:
{
  "questions": Array<{
    "prompt": string,          // the question
    "options": string[],       // exactly 4 options
    "correctIndex": number,    // 0-based index of the correct option
    "explanation": string      // why the correct answer is correct
  }>
}
Questions must be factually accurate about tajweed rules, Quranic Arabic, and recitation.
Return no text outside the JSON object.`;

@Injectable()
export class QuizService {
  private readonly logger = new Logger(QuizService.name);

  constructor(
    @InjectRepository(Quiz) private readonly quizzes: Repository<Quiz>,
    @InjectRepository(QuizAttempt)
    private readonly attempts: Repository<QuizAttempt>,
    private readonly mistral: MistralService,
    private readonly gamification: GamificationService,
  ) {}

  async generate(userId: string, dto: GenerateQuizDto): Promise<PublicQuiz> {
    const topic = (dto.topic ?? 'general tajweed rules').trim();
    const messages: ChatMessage[] = [
      { role: 'system', content: SYSTEM_PROMPT },
      {
        role: 'user',
        content: `Create ${dto.numQuestions} ${dto.difficulty}-level questions about: ${topic}.`,
      },
    ];

    const ai = await this.mistral.chatJson<AiQuiz>(messages, {
      temperature: 0.4,
      maxTokens: 2048,
    });
    const questions = this.sanitizeQuestions(ai.questions, dto.numQuestions);
    if (questions.length === 0) {
      throw new BadRequestException(
        'Could not generate a valid quiz. Please try again.',
      );
    }

    const quiz = await this.quizzes.save(
      this.quizzes.create({
        userId,
        topic: topic.slice(0, 120),
        difficulty: dto.difficulty,
        questions,
      }),
    );
    return this.toPublic(quiz);
  }

  async getForUser(userId: string, quizId: string): Promise<PublicQuiz> {
    const quiz = await this.requireOwnedQuiz(userId, quizId);
    return this.toPublic(quiz);
  }

  async submit(
    userId: string,
    quizId: string,
    dto: SubmitQuizDto,
  ): Promise<QuizResult> {
    const quiz = await this.requireOwnedQuiz(userId, quizId);
    if (dto.answers.length !== quiz.questions.length) {
      throw new BadRequestException(
        `Expected ${quiz.questions.length} answers, received ${dto.answers.length}.`,
      );
    }

    const results = quiz.questions.map((q, i) => {
      const chosenIndex = dto.answers[i];
      const correct = chosenIndex === q.correctIndex;
      return {
        prompt: q.prompt,
        chosenIndex,
        correctIndex: q.correctIndex,
        correct,
        explanation: q.explanation,
      };
    });
    const correctCount = results.filter((r) => r.correct).length;

    const attempt = await this.attempts.save(
      this.attempts.create({
        quizId: quiz.id,
        userId,
        answers: dto.answers,
        correctCount,
        totalCount: quiz.questions.length,
      }),
    );

    const pointsAwarded = await this.gamification.awardQuizPoints(
      userId,
      correctCount,
      quiz.questions.length,
    );

    return {
      attemptId: attempt.id,
      correctCount,
      totalCount: quiz.questions.length,
      pointsAwarded,
      results,
    };
  }

  private async requireOwnedQuiz(
    userId: string,
    quizId: string,
  ): Promise<Quiz> {
    const quiz = await this.quizzes.findOne({ where: { id: quizId } });
    // Treat "not yours" as "not found" so quiz IDs can't be probed.
    if (!quiz || quiz.userId !== userId) {
      throw new NotFoundException('Quiz not found.');
    }
    return quiz;
  }

  private toPublic(quiz: Quiz): PublicQuiz {
    return {
      id: quiz.id,
      topic: quiz.topic,
      difficulty: quiz.difficulty,
      createdAt: quiz.createdAt,
      questions: quiz.questions.map((q) => ({
        prompt: q.prompt,
        options: q.options,
      })),
    };
  }

  private sanitizeQuestions(questions: unknown, max: number): QuizQuestion[] {
    if (!Array.isArray(questions)) return [];
    const out: QuizQuestion[] = [];
    for (const q of questions.slice(0, max)) {
      const raw = (q ?? {}) as Record<string, unknown>;
      const options = Array.isArray(raw.options)
        ? raw.options.map((o) => String(o)).slice(0, 4)
        : [];
      const correctIndex = Number(raw.correctIndex);
      const prompt = String(raw.prompt ?? '').trim();
      // A well-formed question needs a prompt, 4 options, and a valid answer.
      if (
        prompt.length === 0 ||
        options.length !== 4 ||
        !Number.isInteger(correctIndex) ||
        correctIndex < 0 ||
        correctIndex > 3
      ) {
        continue;
      }
      out.push({
        prompt: prompt.slice(0, 500),
        options: options.map((o) => o.slice(0, 300)),
        correctIndex,
        explanation: String(raw.explanation ?? '').slice(0, 1000),
      });
    }
    return out;
  }
}
