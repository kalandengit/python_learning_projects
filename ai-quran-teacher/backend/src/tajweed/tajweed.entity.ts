import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  PrimaryGeneratedColumn,
} from 'typeorm';

export type MistakeSeverity = 'minor' | 'moderate' | 'major';

@Entity('tajweed_mistakes')
export class TajweedMistake {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Index()
  @Column({ nullable: true })
  userId: string | null;

  @Index()
  @Column('int')
  ayahId: number;

  @Column()
  type: string;

  @Column({ default: 'moderate' })
  severity: MistakeSeverity;

  @Column('int')
  wordIndex: number;

  @Column({ default: '' })
  expectedWord: string;

  @Column({ default: '' })
  actualWord: string;

  @Column({ default: '' })
  suggestion: string;

  @CreateDateColumn()
  createdAt: Date;
}
