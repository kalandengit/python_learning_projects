import {
  Column,
  CreateDateColumn,
  Entity,
  PrimaryColumn,
  UpdateDateColumn,
} from 'typeorm';

/**
 * One gamification profile per user. The row is created lazily the first time
 * a user earns points, so there is no coupling to the registration flow.
 */
@Entity({ name: 'gamification_profiles' })
export class GamificationProfile {
  @PrimaryColumn({ type: 'uuid' })
  userId!: string;

  @Column({ type: 'int', default: 0 })
  points!: number;

  @Column({ type: 'int', default: 0 })
  currentStreak!: number;

  @Column({ type: 'int', default: 0 })
  longestStreak!: number;

  /** UTC calendar date (YYYY-MM-DD) of the last recorded activity. */
  @Column({ type: 'varchar', length: 10, nullable: true })
  lastActivityDate!: string | null;

  /** Ids of earned badges (see {@link BADGES}). Initialised in the service. */
  @Column({ type: 'simple-json' })
  badges!: string[];

  @CreateDateColumn()
  createdAt!: Date;

  @UpdateDateColumn()
  updatedAt!: Date;
}
