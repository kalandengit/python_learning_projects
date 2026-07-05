import { Test } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { TajweedMistake } from './tajweed.entity';
import { TajweedService } from './tajweed.service';
import { analyzeText, normalizeArabic } from './tajweed.rules';

const BASMALA = 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ';

describe('tajweed rules', () => {
  it('detects iqlab for noon sakinah before ba', () => {
    const occurrences = analyzeText('مِنْ بَعْدِ');
    expect(occurrences.some((o) => o.rule === 'iqlab')).toBe(true);
  });

  it('detects ikhfa for tanween before ta', () => {
    const occurrences = analyzeText('جَنَّاتٍ تَجْرِي');
    expect(occurrences.some((o) => o.rule === 'ikhfa')).toBe(true);
  });

  it('detects qalqalah on saakin qaf', () => {
    const occurrences = analyzeText('يَقْطَعُونَ');
    expect(occurrences.some((o) => o.rule === 'qalqalah')).toBe(true);
  });

  it('detects ghunnah on noon mushaddadah', () => {
    const occurrences = analyzeText('إِنَّ');
    expect(occurrences.some((o) => o.rule === 'ghunnah')).toBe(true);
  });

  it('normalizes away diacritics and alef variants', () => {
    expect(normalizeArabic('إِنَّ')).toBe('ان');
  });
});

describe('TajweedService.detectMistakes', () => {
  let service: TajweedService;
  const saved: TajweedMistake[] = [];

  beforeEach(async () => {
    saved.length = 0;
    const moduleRef = await Test.createTestingModule({
      providers: [
        TajweedService,
        {
          provide: getRepositoryToken(TajweedMistake),
          useValue: {
            create: (dto: Partial<TajweedMistake>) => dto,
            save: async (items: TajweedMistake[]) => {
              saved.push(...items);
              return items;
            },
            find: async () => saved,
          },
        },
      ],
    }).compile();
    service = moduleRef.get(TajweedService);
  });

  it('returns full accuracy for a perfect recitation', async () => {
    const result = await service.detectMistakes(BASMALA, 1, BASMALA);
    expect(result.accuracy).toBe(1);
    expect(result.mistakes).toHaveLength(0);
    expect(result.rulesToObserve.length).toBeGreaterThan(0);
  });

  it('flags a substituted word without cascading errors', async () => {
    const recited = 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الْكَرِيمِ';
    const result = await service.detectMistakes(recited, 1, BASMALA);
    expect(result.mistakes).toHaveLength(1);
    expect(result.mistakes[0].type).toBe('word_mismatch');
    expect(result.mistakes[0].wordIndex).toBe(3);
    expect(result.accuracy).toBeCloseTo(3 / 4);
  });

  it('flags a skipped word as missing', async () => {
    const recited = 'بِسْمِ اللَّهِ الرَّحِيمِ';
    const result = await service.detectMistakes(recited, 1, BASMALA);
    expect(result.mistakes).toHaveLength(1);
    expect(result.mistakes[0].type).toBe('missing_word');
  });

  it('persists mistakes when a userId is provided', async () => {
    const recited = 'بِسْمِ اللَّهِ الرَّحِيمِ';
    await service.detectMistakes(recited, 1, BASMALA, 'user-1');
    expect(saved).toHaveLength(1);
  });
});
