import { GamificationProfile } from './gamification.entity';
import { GamificationService } from './gamification.service';

/**
 * A tiny in-memory stand-in for the TypeORM repository so we exercise the real
 * streak and badge logic without a database.
 */
class InMemoryProfileRepo {
  private store = new Map<string, GamificationProfile>();

  create(data: Partial<GamificationProfile>): GamificationProfile {
    return { ...data } as GamificationProfile;
  }

  async findOne(opts: { where: { userId: string } }) {
    return this.store.get(opts.where.userId) ?? null;
  }

  async save(profile: GamificationProfile) {
    this.store.set(profile.userId, { ...profile });
    return this.store.get(profile.userId)!;
  }
}

describe('GamificationService', () => {
  let service: GamificationService;
  let repo: InMemoryProfileRepo;

  beforeEach(() => {
    repo = new InMemoryProfileRepo();
    service = new GamificationService(repo as never);
  });

  it('creates a profile lazily on first access', async () => {
    const summary = await service.getSummary('user-1');
    expect(summary.points).toBe(0);
    expect(summary.currentStreak).toBe(0);
    expect(summary.badges).toEqual([]);
  });

  it('awards 10 points per correct answer plus a perfect bonus', async () => {
    const points = await service.awardQuizPoints('user-1', 3, 3);
    expect(points).toBe(3 * 10 + 20);
    const summary = await service.getSummary('user-1');
    expect(summary.points).toBe(50);
  });

  it('does not add the perfect bonus for an imperfect quiz', async () => {
    const points = await service.awardQuizPoints('user-1', 2, 3);
    expect(points).toBe(20);
  });

  it('starts a streak at 1 and grants the first_steps badge', async () => {
    await service.awardQuizPoints('user-1', 1, 5);
    const summary = await service.getSummary('user-1');
    expect(summary.currentStreak).toBe(1);
    expect(summary.badges.map((b) => b.id)).toContain('first_steps');
  });

  it('does not double-count the streak on the same UTC day', async () => {
    await service.awardQuizPoints('user-1', 1, 5);
    await service.awardQuizPoints('user-1', 1, 5);
    const summary = await service.getSummary('user-1');
    expect(summary.currentStreak).toBe(1);
    expect(summary.points).toBe(20);
  });

  it('continues a streak from the previous day and grants streak badges', async () => {
    // Seed a profile whose last activity was yesterday.
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000)
      .toISOString()
      .slice(0, 10);
    await repo.save({
      userId: 'user-1',
      points: 90,
      currentStreak: 2,
      longestStreak: 2,
      lastActivityDate: yesterday,
      badges: ['first_steps'],
    } as unknown as GamificationProfile);

    await service.awardQuizPoints('user-1', 1, 5);
    const summary = await service.getSummary('user-1');
    expect(summary.currentStreak).toBe(3);
    expect(summary.longestStreak).toBe(3);
    // 90 + 10 = 100 -> century; streak 3 -> consistent
    expect(summary.badges.map((b) => b.id)).toEqual(
      expect.arrayContaining(['century', 'consistent']),
    );
  });

  it('resets the streak after a gap of more than one day', async () => {
    const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000)
      .toISOString()
      .slice(0, 10);
    await repo.save({
      userId: 'user-1',
      points: 0,
      currentStreak: 5,
      longestStreak: 5,
      lastActivityDate: threeDaysAgo,
      badges: [],
    } as unknown as GamificationProfile);

    await service.awardQuizPoints('user-1', 1, 5);
    const summary = await service.getSummary('user-1');
    expect(summary.currentStreak).toBe(1);
    expect(summary.longestStreak).toBe(5);
  });
});
