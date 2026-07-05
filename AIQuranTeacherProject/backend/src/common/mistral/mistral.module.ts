import { Global, Module } from '@nestjs/common';
import { MistralService } from './mistral.service';

/**
 * Global module so any feature can inject {@link MistralService} without
 * re-importing it. The service is stateless and safe to share.
 */
@Global()
@Module({
  providers: [MistralService],
  exports: [MistralService],
})
export class MistralModule {}
