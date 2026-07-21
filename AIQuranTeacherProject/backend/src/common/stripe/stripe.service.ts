import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import Stripe from 'stripe';
import { StripeConfig } from '../../config/configuration';

/**
 * Thin wrapper around the Stripe SDK.
 *
 * Centralises the secret key and client construction, exposes a typed client,
 * and isolates webhook signature verification. Keeping Stripe behind a service
 * makes the billing logic unit-testable with a mock (no network, no real keys).
 */
@Injectable()
export class StripeService {
  private readonly logger = new Logger(StripeService.name);
  private readonly config: StripeConfig;
  private readonly stripe: Stripe | null;

  constructor(private readonly configService: ConfigService) {
    this.config = this.configService.getOrThrow<StripeConfig>('stripe');
    this.stripe = this.config.secretKey
      ? new Stripe(this.config.secretKey, {
          // Fail fast on transient network errors instead of hanging a request.
          maxNetworkRetries: 2,
          timeout: 20_000,
          // API version is pinned by the installed SDK; omit to use its default
          // so the TypeScript types always match the requests we send.
          appInfo: { name: 'AI Quran Teacher', version: '1.0.0' },
        })
      : null;
  }

  isConfigured(): boolean {
    return this.stripe !== null;
  }

  /** The underlying client. Throws if Stripe is not configured. */
  get client(): Stripe {
    if (!this.stripe) {
      throw new Error('Stripe is not configured (STRIPE_SECRET_KEY missing).');
    }
    return this.stripe;
  }

  /**
   * Verify and parse a webhook payload. MUST be given the raw request body
   * (a Buffer/string exactly as received) — a parsed JSON body will fail
   * signature verification. Throws if the signature is invalid.
   */
  constructWebhookEvent(
    rawBody: Buffer | string,
    signature: string,
  ): Stripe.Event {
    return this.client.webhooks.constructEvent(
      rawBody,
      signature,
      this.config.webhookSecret,
    );
  }
}
