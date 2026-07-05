export interface BadgeDefinition {
  code: string;
  name: string;
  description: string;
  icon: string;
  xpReward: number;
}

export const BADGE_CATALOG: BadgeDefinition[] = [
  {
    code: 'first_recitation',
    name: 'First Recitation',
    description: 'Complete your first recitation session.',
    icon: '🎙️',
    xpReward: 25,
  },
  {
    code: 'tajweed_master',
    name: 'Tajweed Master',
    description: 'Score 100% on a hard Tajweed quiz.',
    icon: '🏅',
    xpReward: 200,
  },
  {
    code: 'quiz_champion',
    name: 'Quiz Champion',
    description: 'Complete 10 quizzes.',
    icon: '🧠',
    xpReward: 100,
  },
  {
    code: 'week_streak',
    name: 'Consistent Reciter',
    description: 'Practice 7 days in a row.',
    icon: '🔥',
    xpReward: 75,
  },
  {
    code: 'month_streak',
    name: 'Devoted Student',
    description: 'Practice 30 days in a row.',
    icon: '🌙',
    xpReward: 300,
  },
  {
    code: 'certified_foundation',
    name: 'Certified: Foundation',
    description: 'Pass the Foundation Tajweed exam.',
    icon: '📜',
    xpReward: 150,
  },
  {
    code: 'certified_intermediate',
    name: 'Certified: Intermediate',
    description: 'Pass the Intermediate Tajweed exam.',
    icon: '🎓',
    xpReward: 250,
  },
  {
    code: 'certified_advanced',
    name: 'Certified: Advanced',
    description: 'Pass the Advanced Tajweed exam.',
    icon: '🏆',
    xpReward: 400,
  },
  {
    code: 'surah_complete',
    name: 'Surah Complete',
    description: 'Recite an entire surah without major mistakes.',
    icon: '📖',
    xpReward: 150,
  },
];

/** XP required to go from `level` to `level + 1`. */
export function xpForLevel(level: number): number {
  return 100 * level;
}

/** Computes a level from total XP (level 1 at 0 XP). */
export function levelForXp(xp: number): number {
  let level = 1;
  let remaining = xp;
  while (remaining >= xpForLevel(level)) {
    remaining -= xpForLevel(level);
    level++;
  }
  return level;
}
