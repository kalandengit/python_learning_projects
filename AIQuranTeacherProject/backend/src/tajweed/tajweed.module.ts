import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { QuranModule } from '../quran/quran.module';
import { TajweedAnalysis } from './tajweed.entity';
import { TajweedController } from './tajweed.controller';
import { TajweedService } from './tajweed.service';

@Module({
  imports: [TypeOrmModule.forFeature([TajweedAnalysis]), QuranModule],
  controllers: [TajweedController],
  providers: [TajweedService],
  exports: [TajweedService],
})
export class TajweedModule {}
