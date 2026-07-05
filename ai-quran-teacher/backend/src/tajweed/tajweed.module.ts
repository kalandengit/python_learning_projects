import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { TajweedController } from './tajweed.controller';
import { TajweedMistake } from './tajweed.entity';
import { TajweedService } from './tajweed.service';

@Module({
  imports: [TypeOrmModule.forFeature([TajweedMistake])],
  controllers: [TajweedController],
  providers: [TajweedService],
  exports: [TajweedService],
})
export class TajweedModule {}
