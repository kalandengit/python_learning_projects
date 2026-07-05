import { Test } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { levelForXp } from './badges.catalog';
import {
  LeaderboardEntry,
  Streak,
  UserBadge,
} from './gamification.entity';
import { GamificationService } from './gamification.service';

function inMemoryRepo<T extends { userId: string }>() {
  const rows: T[] = [];
  return {
    rows,
    create: (dto: Partial<T>) => ({ ...dto }) as T,
    save: async (row: T) => {
      const index = rows.findIndex((r) => r.userId === row.userId);
      if (index >= 0) rows[index] = row;
      else rows.push(row);
      return row;
    },
    findOne: async ({ where }: any) =>
      rows.find((r) =>
        Object.entries(where).every(([k, v]) => (r as any)[k] === v),
      ) ?? null,
    find: async ({ where }: any = {}) =>
      where
        ? rows.filter((r) =>
            Object.entries(where).every(([k, v]) => (r as any)[k] === v),
          )
        : [...rows],
  };
}

describe('GamificationService', () => {
  let service: GamificationService;
  let badges: ReturnType<typeof inMemoryRepo<UserBadge>>;
  let streaks: ReturnType<typeof inMemoryRepo<Streak>>;
  let leaderboard: ReturnType<typeof inMemoryRepo<LeaderboardEntry>>;

  beforeEach(async () => {
    badges = inMemoryRepo<UserBadge>();
    streaks = inMemoryRepo<Streak>();
    leaderboard = inMemoryRepo<LeaderboardEntry>();

    const moduleRef = await Test.createTestingModule({
      providers: [
        GamificationService,
        { provide: getRepositoryToken(UserBadge), useValue: badges },
        { provide: getRepositoryToken(Streak), useValue: streaks },
        { provide: getRepositoryToken(LeaderboardEntry), useValue: leaderboard },
      ],
    }).compile();
    service = moduleRef.get(GamificationService);
  });

  it('awards a badge once and grants its XP', async () => {
    const first = await service.awardBadge('user-1', 'first_recitation');
    expect(first?.code).toBe('first_recitation');
    const again = await service.awardBadge('user-1', 'first_recitation');
    expect(again).toBeNull();
    expect(leaderboard.rows[0].xp).toBe(25);
  });

  it('extends the streak on consecutive days and resets after a gap', async () => {
    const day1 = new Date('2026-07-01T10:00:00Z');
    const day2 = new Date('2026-07-02T10:00:00Z');
    const day5 = new Date('2026-07-05T10:00:00Z');

    expect((await service.updateStreak('user-1', day1)).current).toBe(1);
    expect((await service.updateStreak('user-1', day2)).current).toBe(2);
    // Same-day repeat is idempotent.
    expect((await service.updateStreak('user-1', day2)).current).toBe(2);
    const afterGap = await service.updateStreak('user-1', day5);
    expect(afterGap.current).toBe(1);
    expect(afterGap.longest).toBe(2);
  });

  it('awards the week_streak badge on day 7', async () => {
    for (let day = 1; day <= 7; day++) {
      await service.updateStreak(
        'user-1',
        new Date(`2026-07-0${day}T10:00:00Z`),
      );
    }
    const profile = await service.getProfile('user-1');
    expect(profile.badges.map((b) => b.code)).toContain('week_streak');
    expect(profile.streak.current).toBe(7);
  });

  it('computes levels from XP', () => {
    expect(levelForXp(0)).toBe(1);
    expect(levelForXp(99)).toBe(1);
    expect(levelForXp(100)).toBe(2);
    expect(levelForXp(300)).toBe(3);
  });
});
