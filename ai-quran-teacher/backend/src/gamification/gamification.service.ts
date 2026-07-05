import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import {
  BADGE_CATALOG,
  BadgeDefinition,
  levelForXp,
} from './badges.catalog';
import {
  LeaderboardEntry,
  Streak,
  UserBadge,
} from './gamification.entity';

@Injectable()
export class GamificationService {
  constructor(
    @InjectRepository(UserBadge)
    private readonly badgesRepository: Repository<UserBadge>,
    @InjectRepository(Streak)
    private readonly streaksRepository: Repository<Streak>,
    @InjectRepository(LeaderboardEntry)
    private readonly leaderboardRepository: Repository<LeaderboardEntry>,
  ) {}

  getBadgeCatalog(): BadgeDefinition[] {
    return BADGE_CATALOG;
  }

  /** Awards a badge once; re-awarding is a no-op. Returns the badge if newly awarded. */
  async awardBadge(
    userId: string,
    badgeCode: string,
  ): Promise<BadgeDefinition | null> {
    const definition = BADGE_CATALOG.find((b) => b.code === badgeCode);
    if (!definition) {
      throw new NotFoundException(`Unknown badge code: ${badgeCode}`);
    }
    const existing = await this.badgesRepository.findOne({
      where: { userId, badgeCode },
    });
    if (existing) {
      return null;
    }
    await this.badgesRepository.save(
      this.badgesRepository.create({ userId, badgeCode }),
    );
    await this.addXp(userId, definition.xpReward);
    return definition;
  }

  /**
   * Records a practice day. Consecutive calendar days extend the streak;
   * a gap resets it to 1. Same-day calls are idempotent.
   */
  async updateStreak(userId: string, today = new Date()): Promise<Streak> {
    const todayStr = toDateString(today);
    let streak = await this.streaksRepository.findOne({ where: { userId } });
    if (!streak) {
      streak = this.streaksRepository.create({
        userId,
        current: 0,
        longest: 0,
        lastActivityDate: null,
      });
    }

    if (streak.lastActivityDate === todayStr) {
      return streak;
    }

    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    streak.current =
      streak.lastActivityDate === toDateString(yesterday)
        ? streak.current + 1
        : 1;
    streak.longest = Math.max(streak.longest, streak.current);
    streak.lastActivityDate = todayStr;
    streak = await this.streaksRepository.save(streak);

    if (streak.current === 7) {
      await this.awardBadge(userId, 'week_streak');
    } else if (streak.current === 30) {
      await this.awardBadge(userId, 'month_streak');
    }
    return streak;
  }

  /** Adds XP and recomputes the user's level and leaderboard entry. */
  async addXp(userId: string, amount: number): Promise<LeaderboardEntry> {
    let entry = await this.leaderboardRepository.findOne({
      where: { userId },
    });
    if (!entry) {
      entry = this.leaderboardRepository.create({ userId, xp: 0, level: 1 });
    }
    entry.xp += amount;
    entry.level = levelForXp(entry.xp);
    return this.leaderboardRepository.save(entry);
  }

  getLeaderboard(limit = 20): Promise<LeaderboardEntry[]> {
    return this.leaderboardRepository.find({
      order: { xp: 'DESC' },
      take: limit,
    });
  }

  /** Full gamification profile for one user. */
  async getProfile(userId: string) {
    const [badges, streak, entry] = await Promise.all([
      this.badgesRepository.find({ where: { userId } }),
      this.streaksRepository.findOne({ where: { userId } }),
      this.leaderboardRepository.findOne({ where: { userId } }),
    ]);
    const codes = new Set(badges.map((b) => b.badgeCode));
    return {
      userId,
      xp: entry?.xp ?? 0,
      level: entry?.level ?? 1,
      streak: {
        current: streak?.current ?? 0,
        longest: streak?.longest ?? 0,
        lastActivityDate: streak?.lastActivityDate ?? null,
      },
      badges: BADGE_CATALOG.filter((b) => codes.has(b.code)),
    };
  }
}

function toDateString(date: Date): string {
  return date.toISOString().slice(0, 10);
}
