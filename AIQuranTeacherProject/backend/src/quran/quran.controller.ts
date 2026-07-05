import { Controller, Get, Param, ParseIntPipe } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { Public } from '../common/decorators/public.decorator';
import { Ayah } from './entities/ayah.entity';
import { Surah } from './entities/surah.entity';
import { QuranService } from './quran.service';

// Quran content is public reference material — readable without authentication.
@ApiTags('quran')
@Public()
@Controller('quran')
export class QuranController {
  constructor(private readonly quranService: QuranService) {}

  @Get('surahs')
  @ApiOperation({ summary: 'List all available surahs.' })
  listSurahs(): Promise<Surah[]> {
    return this.quranService.listSurahs();
  }

  @Get('surahs/:id')
  @ApiOperation({ summary: 'Get a surah with all of its ayahs.' })
  getSurah(@Param('id', ParseIntPipe) id: number): Promise<Surah> {
    return this.quranService.getSurah(id);
  }

  @Get('surahs/:surahId/ayahs/:ayah')
  @ApiOperation({ summary: 'Get a single ayah by surah and ayah number.' })
  getAyah(
    @Param('surahId', ParseIntPipe) surahId: number,
    @Param('ayah', ParseIntPipe) ayah: number,
  ): Promise<Ayah> {
    return this.quranService.getAyah(surahId, ayah);
  }
}
