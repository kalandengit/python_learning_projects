import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  PrimaryGeneratedColumn,
} from 'typeorm';

export enum QuizDifficulty {
  Beginner = 'beginner',
  Intermediate = 'intermediate',
  Advanced = 'advanced',
}

/** A single multiple-choice question. `correctIndex` is never sent to clients. */
export interface QuizQuestion {
  prompt: string;
  options: string[];
  correctIndex: number;
  explanation: string;
}

@Entity({ name: 'quizzes' })
export class Quiz {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Index()
  @Column({ type: 'uuid' })
  userId!: string;

  @Column({ type: 'varchar', length: 120 })
  topic!: string;

  @Column({ type: 'varchar', default: QuizDifficulty.Beginner })
  difficulty!: QuizDifficulty;

  @Column({ type: 'simple-json' })
  questions!: QuizQuestion[];

  @CreateDateColumn()
  createdAt!: Date;
}

@Entity({ name: 'quiz_attempts' })
export class QuizAttempt {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Index()
  @Column({ type: 'uuid' })
  quizId!: string;

  @Index()
  @Column({ type: 'uuid' })
  userId!: string;

  @Column({ type: 'simple-json' })
  answers!: number[];

  /** Number of correct answers. */
  @Column({ type: 'int' })
  correctCount!: number;

  @Column({ type: 'int' })
  totalCount!: number;

  @CreateDateColumn()
  createdAt!: Date;
}
