import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  PrimaryGeneratedColumn,
} from 'typeorm';
import { QuizQuestion } from '../quiz/quiz.entity';

export type ExamLevel = 'foundation' | 'intermediate' | 'advanced';

export const EXAM_RULES: Record<
  ExamLevel,
  { durationMinutes: number; passPercent: number; questionCount: number }
> = {
  foundation: { durationMinutes: 15, passPercent: 70, questionCount: 8 },
  intermediate: { durationMinutes: 20, passPercent: 70, questionCount: 10 },
  advanced: { durationMinutes: 30, passPercent: 80, questionCount: 10 },
};

@Entity('exams')
export class Exam {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Index()
  @Column()
  userId: string;

  @Column()
  level: ExamLevel;

  /** Snapshot of served questions, including answers, for grading. */
  @Column({ type: 'jsonb' })
  questions: QuizQuestion[];

  @Column('int')
  durationMinutes: number;

  @CreateDateColumn()
  startedAt: Date;

  @Column({ type: 'timestamptz', nullable: true })
  completedAt: Date | null;

  @Column('int', { nullable: true })
  score: number | null;

  @Column({ type: 'boolean', nullable: true })
  passed: boolean | null;

  /** Set when the submission arrived after the time limit. */
  @Column({ default: false })
  expired: boolean;

  @Column({ type: 'uuid', nullable: true })
  certificateId: string | null;
}

@Entity('certificates')
export class Certificate {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Index()
  @Column()
  userId: string;

  @Column('uuid')
  examId: string;

  @Column()
  level: ExamLevel;

  /** Public code for third-party verification (GET /exams/verify/:code). */
  @Index({ unique: true })
  @Column()
  verificationCode: string;

  @CreateDateColumn()
  issuedAt: Date;
}
