import {
  BadRequestException,
  Body,
  Controller,
  Get,
  Headers,
  HttpCode,
  HttpStatus,
  Logger,
  Post,
  RawBodyRequest,
  Req,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { ApiBearerAuth, ApiOperation, ApiTags } from '@nestjs/swagger';
import { Throttle } from '@nestjs/throttler';
import { Request } from 'express';
import {
  AuthenticatedUser,
  CurrentUser,
} from '../common/decorators/current-user.decorator';
import { Public } from '../common/decorators/public.decorator';
import { StripeService } from '../common/stripe/stripe.service';
import { StripeConfig } from '../config/configuration';
import { BillingService, Entitlement } from './billing.service';
import { CHECKOUT_PLANS, CreateCheckoutDto } from './dto/create-checkout.dto';

@ApiTags('billing')
@Controller('billing')
export class BillingController {
  private readonly logger = new Logger(BillingController.name);

  constructor(
    private readonly billing: BillingService,
    private readonly stripe: StripeService,
    private readonly configService: ConfigService,
  ) {}

  @ApiBearerAuth()
  @Get('config')
  @ApiOperation({
    summary: 'Publishable key and available plans for the client.',
  })
  config(): { publishableKey: string; plans: readonly string[] } {
    const cfg = this.configService.getOrThrow<StripeConfig>('stripe');
    return { publishableKey: cfg.publishableKey, plans: CHECKOUT_PLANS };
  }

  @ApiBearerAuth()
  @Get('me')
  @ApiOperation({ summary: "The current user's subscription/entitlement." })
  me(@CurrentUser() user: AuthenticatedUser): Promise<Entitlement> {
    return this.billing.getEntitlement(user.userId);
  }

  @ApiBearerAuth()
  @Throttle({ default: { limit: 15, ttl: 60_000 } })
  @Post('checkout')
  @ApiOperation({
    summary: 'Start a subscription checkout; returns a Stripe URL.',
  })
  checkout(
    @CurrentUser() user: AuthenticatedUser,
    @Body() dto: CreateCheckoutDto,
  ): Promise<{ url: string }> {
    return this.billing.createCheckoutSession(user.userId, dto.plan);
  }

  @ApiBearerAuth()
  @Throttle({ default: { limit: 15, ttl: 60_000 } })
  @Post('portal')
  @ApiOperation({ summary: 'Open the Stripe billing portal; returns a URL.' })
  portal(@CurrentUser() user: AuthenticatedUser): Promise<{ url: string }> {
    return this.billing.createPortalSession(user.userId);
  }

  /**
   * Stripe webhook receiver. Public (Stripe is not a logged-in user) but
   * authenticated by verifying the signature against the raw request body.
   * `rawBody` is available because the app is created with `rawBody: true`.
   */
  @Public()
  @Post('webhook')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Stripe webhook endpoint (signature-verified).' })
  async webhook(
    @Req() req: RawBodyRequest<Request>,
    @Headers('stripe-signature') signature: string | undefined,
  ): Promise<{ received: true }> {
    if (!signature || !req.rawBody) {
      throw new BadRequestException('Missing Stripe signature or body.');
    }

    let event;
    try {
      event = this.stripe.constructWebhookEvent(req.rawBody, signature);
    } catch (err) {
      // Invalid signature — reject so Stripe (and attackers) get a clear 400.
      this.logger.warn(`Rejected webhook: ${(err as Error).message}`);
      throw new BadRequestException('Invalid webhook signature.');
    }

    // Acknowledge fast; a thrown error makes Stripe retry, which is safe
    // because event handling is idempotent.
    await this.billing.handleWebhookEvent(event);
    return { received: true };
  }
}
