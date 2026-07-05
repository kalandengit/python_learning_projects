import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  PrimaryGeneratedColumn,
} from 'typeorm';

export enum MistakeSeverity {
  Minor = 'minor',
  Moderate = 'moderate',
  Major = 'major',
}

/** A single tajweed observation returned by the AI, stored as JSON. */
export interface TajweedMistake {
  /** The word (or fragment) the mistake relates to. */
  word: string;
  /** 1-based index of the word within the ayah, when identifiable. */
  position: number | null;
  /** The tajweed rule involved, e.g. "Ikhfa", "Madd", "Qalqalah". */
  rule: string;
  severity: MistakeSeverity;
  /** Plain-language explanation for the learner. */
  explanation: string;
  /** How to correct it. */
  correction: string;
}

@Entity({ name: 'tajweed_analyses' })
export class TajweedAnalysis {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Index()
  @Column({ type: 'uuid' })
  userId!: string;

  @Column({ type: 'int' })
  surahId!: number;

  @Column({ type: 'int' })
  ayahNumber!: number;

  @Column({ type: 'text' })
  referenceText!: string;

  @Column({ type: 'text' })
  transcript!: string;

  /** Overall accuracy score, 0–100. */
  @Column({ type: 'int' })
  score!: number;

  @Column({ type: 'simple-json' })
  mistakes!: TajweedMistake[];

  /** Short encouraging summary from the AI teacher. */
  @Column({ type: 'text' })
  feedback!: string;

  @CreateDateColumn()
  createdAt!: Date;
}
