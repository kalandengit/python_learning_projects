import { Global, Module } from '@nestjs/common';
import { StripeService } from './stripe.service';

/** Global so any feature can inject the shared, stateless {@link StripeService}. */
@Global()
@Module({
  providers: [StripeService],
  exports: [StripeService],
})
export class StripeModule {}
