import { Module } from '@nestjs/common';
import { LearnerTwinController } from './learner-twin.controller';
import { LearnerTwinService } from './learner-twin.service';

/**
 * Learner Digital Twin feature: the projection service (subscribes to the bus)
 * and the HTTP surface for recording activity and reading the twin.
 */
@Module({
  controllers: [LearnerTwinController],
  providers: [LearnerTwinService],
  exports: [LearnerTwinService],
})
export class LearnerTwinModule {}
