import { Global, Module } from '@nestjs/common';
import { RedisService } from './redis.service';

/** Global so RedisService can be injected anywhere without re-importing. */
@Global()
@Module({
  providers: [RedisService],
  exports: [RedisService],
})
export class CommonModule {}
