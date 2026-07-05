import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  PrimaryGeneratedColumn,
  Unique,
  UpdateDateColumn,
} from 'typeorm';

/** A badge awarded to a user. The badge catalog itself lives in code. */
@Entity('user_badges')
@Unique(['userId', 'badgeCode'])
export class UserBadge {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Index()
  @Column()
  userId: string;

  @Column()
  badgeCode: string;

  @CreateDateColumn()
  awardedAt: Date;
}

@Entity('streaks')
export class Streak {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Index({ unique: true })
  @Column()
  userId: string;

  @Column('int', { default: 0 })
  current: number;

  @Column('int', { default: 0 })
  longest: number;

  /** Calendar date (YYYY-MM-DD) of the last counted activity. */
  @Column({ type: 'date', nullable: true })
  lastActivityDate: string | null;
}

@Entity('leaderboard_entries')
export class LeaderboardEntry {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Index({ unique: true })
  @Column()
  userId: string;

  @Column('int', { default: 0 })
  xp: number;

  @Column('int', { default: 1 })
  level: number;

  @UpdateDateColumn()
  updatedAt: Date;
}
