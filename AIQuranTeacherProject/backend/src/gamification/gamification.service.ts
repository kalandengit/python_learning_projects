import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from '../users/user.entity';
import { BADGES, BADGES_BY_ID } from './badges';
import { GamificationProfile } from './gamification.entity';

const POINTS_PER_CORRECT = 10;
const PERFECT_QUIZ_BONUS = 20;

export interface EarnedBadge {
  id: string;
  name: string;
  description: string;
}

export interface ProfileSummary {
  userId: string;
  points: number;
  currentStreak: number;
  longestStreak: number;
  lastActivityDate: string | null;
  badges: EarnedBadge[];
}

export interface LeaderboardEntry {
  rank: number;
  userId: string;
  displayName: string;
  points: number;
  currentStreak: number;
}

/** Current date as a UTC `YYYY-MM-DD` string. */
const utcDate = (d = new Date()): string => d.toISOString().slice(0, 10);

@Injectable()
export class GamificationService {
  constructor(
    @InjectRepository(GamificationProfile)
    private readonly profiles: Repository<GamificationProfile>,
  ) {}

  async getOrCreateProfile(userId: string): Promise<GamificationProfile> {
    const existing = await this.profiles.findOne({ where: { userId } });
    if (existing) return existing;
    return this.profiles.save(
      this.profiles.create({
        userId,
        points: 0,
        currentStreak: 0,
        longestStreak: 0,
        lastActivityDate: null,
        badges: [],
      }),
    );
  }

  async getSummary(userId: string): Promise<ProfileSummary> {
    const profile = await this.getOrCreateProfile(userId);
    return this.toSummary(profile);
  }

  /**
   * Award points for a graded quiz, update the daily streak, and grant any
   * newly-earned badges. Returns the number of points awarded.
   */
  async awardQuizPoints(
    userId: string,
    correctCount: number,
    totalCount: number,
  ): Promise<number> {
    const profile = await this.getOrCreateProfile(userId);
    const perfect = totalCount > 0 && correctCount === totalCount;
    const points =
      correctCount * POINTS_PER_CORRECT + (perfect ? PERFECT_QUIZ_BONUS : 0);

    profile.points += points;
    this.applyStreak(profile);
    this.applyBadges(profile);
    await this.profiles.save(profile);
    return points;
  }

  async getLeaderboard(limit = 10): Promise<LeaderboardEntry[]> {
    const capped = Math.min(Math.max(limit, 1), 100);
    const rows = await this.profiles
      .createQueryBuilder('p')
      .leftJoin(User, 'u', 'u.id = p.userId')
      .select('p.userId', 'userId')
      .addSelect('p.points', 'points')
      .addSelect('p.currentStreak', 'currentStreak')
      .addSelect('u.displayName', 'displayName')
      .orderBy('p.points', 'DESC')
      .addOrderBy('p.updatedAt', 'ASC')
      .limit(capped)
      .getRawMany<{
        userId: string;
        points: number;
        currentStreak: number;
        displayName: string | null;
      }>();

    return rows.map((r, i) => ({
      rank: i + 1,
      userId: r.userId,
      displayName: r.displayName ?? 'Anonymous',
      points: Number(r.points),
      currentStreak: Number(r.currentStreak),
    }));
  }

  /** Update the day-streak based on the UTC date of the last activity. */
  private applyStreak(profile: GamificationProfile): void {
    const today = utcDate();
    if (profile.lastActivityDate === today) {
      return; // already counted today
    }
    const yesterday = utcDate(new Date(Date.now() - 24 * 60 * 60 * 1000));
    profile.currentStreak =
      profile.lastActivityDate === yesterday ? profile.currentStreak + 1 : 1;
    profile.lastActivityDate = today;
    profile.longestStreak = Math.max(
      profile.longestStreak,
      profile.currentStreak,
    );
  }

  private applyBadges(profile: GamificationProfile): void {
    const owned = new Set(profile.badges);
    for (const badge of BADGES) {
      if (!owned.has(badge.id) && badge.earned(profile)) {
        owned.add(badge.id);
      }
    }
    profile.badges = [...owned];
  }

  private toSummary(profile: GamificationProfile): ProfileSummary {
    return {
      userId: profile.userId,
      points: profile.points,
      currentStreak: profile.currentStreak,
      longestStreak: profile.longestStreak,
      lastActivityDate: profile.lastActivityDate,
      badges: profile.badges
        .map((id) => BADGES_BY_ID.get(id))
        .filter((b): b is NonNullable<typeof b> => Boolean(b))
        .map((b) => ({ id: b.id, name: b.name, description: b.description })),
    };
  }
}
