import {
  Column,
  Entity,
  Index,
  JoinColumn,
  ManyToOne,
  PrimaryGeneratedColumn,
} from 'typeorm';
import { Surah } from './surah.entity';

@Entity({ name: 'ayahs' })
@Index(['surahId', 'numberInSurah'], { unique: true })
export class Ayah {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'int' })
  surahId!: number;

  @ManyToOne(() => Surah, (surah) => surah.ayahs, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'surahId' })
  surah!: Surah;

  /** Ayah number within its surah, starting at 1. */
  @Column({ type: 'int' })
  numberInSurah!: number;

  @Column({ type: 'text' })
  textArabic!: string;

  @Column({ type: 'text', nullable: true })
  textTransliteration!: string | null;

  @Column({ type: 'text', nullable: true })
  translation!: string | null;
}
