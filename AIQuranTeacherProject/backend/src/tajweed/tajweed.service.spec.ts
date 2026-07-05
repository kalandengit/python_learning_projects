import { MistralService } from '../common/mistral/mistral.service';
import { QuranService } from '../quran/quran.service';
import { Ayah } from '../quran/entities/ayah.entity';
import { TajweedAnalysis, MistakeSeverity } from './tajweed.entity';
import { TajweedService } from './tajweed.service';

describe('TajweedService', () => {
  let service: TajweedService;
  let mistral: { chatJson: jest.Mock };
  let quran: { getAyah: jest.Mock };
  let repo: { create: jest.Mock; save: jest.Mock; find: jest.Mock };

  const ayah: Partial<Ayah> = {
    surahId: 1,
    numberInSurah: 1,
    textArabic: 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ',
    textTransliteration: 'Bismi Allāhi ar-raḥmāni ar-raḥīm',
  };

  beforeEach(() => {
    mistral = { chatJson: jest.fn() };
    quran = { getAyah: jest.fn().mockResolvedValue(ayah) };
    repo = {
      create: jest.fn((x) => x),
      save: jest.fn(async (x) => ({ id: 'analysis-1', ...x })),
      find: jest.fn().mockResolvedValue([]),
    };
    service = new TajweedService(
      repo as never,
      mistral as unknown as MistralService,
      quran as unknown as QuranService,
    );
  });

  it('clamps out-of-range scores and normalises mistakes', async () => {
    mistral.chatJson.mockResolvedValue({
      score: 250,
      feedback: 'Great effort!',
      mistakes: [
        {
          word: 'الرَّحِيمِ',
          position: 4,
          rule: 'Madd',
          severity: 'ludicrous', // invalid -> coerced to minor
          explanation: 'Elongation too short.',
          correction: 'Hold the madd for the correct count.',
        },
      ],
    });

    const result = (await service.analyze('user-1', {
      surahId: 1,
      ayahNumber: 1,
      transcript: 'bismillah',
    })) as TajweedAnalysis;

    expect(result.score).toBe(100);
    expect(result.mistakes).toHaveLength(1);
    expect(result.mistakes[0].severity).toBe(MistakeSeverity.Minor);
    expect(result.userId).toBe('user-1');
    expect(result.referenceText).toBe(ayah.textArabic);
    expect(repo.save).toHaveBeenCalledTimes(1);
  });

  it('handles a non-array mistakes payload defensively', async () => {
    mistral.chatJson.mockResolvedValue({
      score: -5,
      feedback: '',
      mistakes: null,
    });

    const result = (await service.analyze('user-1', {
      surahId: 1,
      ayahNumber: 1,
      transcript: 'x',
    })) as TajweedAnalysis;

    expect(result.score).toBe(0);
    expect(result.mistakes).toEqual([]);
  });

  it('propagates NotFound from the Quran service', async () => {
    quran.getAyah.mockRejectedValue(new Error('Surah 999 not found.'));
    await expect(
      service.analyze('user-1', {
        surahId: 999,
        ayahNumber: 1,
        transcript: 'x',
      }),
    ).rejects.toThrow('not found');
    expect(mistral.chatJson).not.toHaveBeenCalled();
  });
});
