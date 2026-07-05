import {
  Injectable,
  Logger,
  NotFoundException,
  OnModuleInit,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Ayah } from './entities/ayah.entity';
import { Surah } from './entities/surah.entity';
import { QURAN_SEED } from './quran.seed';

@Injectable()
export class QuranService implements OnModuleInit {
  private readonly logger = new Logger(QuranService.name);

  constructor(
    @InjectRepository(Surah) private readonly surahs: Repository<Surah>,
    @InjectRepository(Ayah) private readonly ayahs: Repository<Ayah>,
  ) {}

  /** Idempotently load the bundled seed on first boot. */
  async onModuleInit(): Promise<void> {
    const count = await this.surahs.count();
    if (count > 0) return;
    await this.seed();
  }

  async seed(): Promise<void> {
    for (const s of QURAN_SEED) {
      const surah = await this.surahs.save(
        this.surahs.create({
          id: s.id,
          nameArabic: s.nameArabic,
          nameTransliteration: s.nameTransliteration,
          nameTranslation: s.nameTranslation,
          revelationPlace: s.revelationPlace,
          ayahCount: s.ayahCount,
        }),
      );
      await this.ayahs.save(
        s.ayahs.map((a) =>
          this.ayahs.create({
            surahId: surah.id,
            numberInSurah: a.numberInSurah,
            textArabic: a.textArabic,
            textTransliteration: a.textTransliteration,
            translation: a.translation,
          }),
        ),
      );
    }
    this.logger.log(`Seeded ${QURAN_SEED.length} surahs.`);
  }

  listSurahs(): Promise<Surah[]> {
    return this.surahs.find({ order: { id: 'ASC' } });
  }

  async getSurah(id: number): Promise<Surah> {
    const surah = await this.surahs.findOne({
      where: { id },
      relations: { ayahs: true },
      order: { ayahs: { numberInSurah: 'ASC' } },
    });
    if (!surah) {
      throw new NotFoundException(`Surah ${id} not found.`);
    }
    return surah;
  }

  async getAyah(surahId: number, numberInSurah: number): Promise<Ayah> {
    const ayah = await this.ayahs.findOne({
      where: { surahId, numberInSurah },
    });
    if (!ayah) {
      throw new NotFoundException(
        `Ayah ${surahId}:${numberInSurah} not found.`,
      );
    }
    return ayah;
  }
}
