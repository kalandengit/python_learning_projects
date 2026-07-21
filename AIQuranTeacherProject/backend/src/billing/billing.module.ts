import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { RolesGuard } from '../common/guards/roles.guard';
import { UsersModule } from '../users/users.module';
import { BillingController } from './billing.controller';
import { BillingCustomer } from './billing.entity';
import { BillingService } from './billing.service';
import { PremiumGrant } from './premium-grant.entity';
import { WhitelistController } from './whitelist.controller';

@Module({
  imports: [
    TypeOrmModule.forFeature([BillingCustomer, PremiumGrant]),
    UsersModule,
  ],
  controllers: [BillingController, WhitelistController],
  providers: [BillingService, RolesGuard],
  exports: [BillingService],
})
export class BillingModule {}
