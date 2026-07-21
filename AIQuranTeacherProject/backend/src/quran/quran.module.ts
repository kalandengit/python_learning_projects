import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Ayah } from './entities/ayah.entity';
import { Surah } from './entities/surah.entity';
import { QuranController } from './quran.controller';
import { QuranService } from './quran.service';

@Module({
  imports: [TypeOrmModule.forFeature([Surah, Ayah])],
  controllers: [QuranController],
  providers: [QuranService],
  exports: [QuranService],
})
export class QuranModule {}
