import { GamificationProfile } from './gamification.entity';

export interface BadgeDefinition {
  id: string;
  name: string;
  description: string;
  /** Returns true when the profile qualifies for this badge. */
  earned: (profile: GamificationProfile) => boolean;
}

/**
 * The badge catalogue. Badges are re-evaluated after every points award; a
 * badge is granted the first time its predicate becomes true and then sticks.
 */
export const BADGES: BadgeDefinition[] = [
  {
    id: 'first_steps',
    name: 'First Steps',
    description: 'Earned your very first points.',
    earned: (p) => p.points >= 1,
  },
  {
    id: 'century',
    name: 'Century',
    description: 'Reached 100 points.',
    earned: (p) => p.points >= 100,
  },
  {
    id: 'scholar',
    name: 'Scholar',
    description: 'Reached 1000 points.',
    earned: (p) => p.points >= 1000,
  },
  {
    id: 'consistent',
    name: 'Consistent',
    description: 'Maintained a 3-day streak.',
    earned: (p) => p.longestStreak >= 3,
  },
  {
    id: 'devoted',
    name: 'Devoted',
    description: 'Maintained a 7-day streak.',
    earned: (p) => p.longestStreak >= 7,
  },
  {
    id: 'steadfast',
    name: 'Steadfast',
    description: 'Maintained a 30-day streak.',
    earned: (p) => p.longestStreak >= 30,
  },
];

export const BADGES_BY_ID = new Map(BADGES.map((b) => [b.id, b]));
