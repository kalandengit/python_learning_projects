import {
  BadRequestException,
  Injectable,
  Logger,
  NotFoundException,
  ServiceUnavailableException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { InjectRepository } from '@nestjs/typeorm';
import Stripe from 'stripe';
import { Repository } from 'typeorm';
import { StripeService } from '../common/stripe/stripe.service';
import { StripeConfig } from '../config/configuration';
import { UsersService } from '../users/users.service';
import { BillingCustomer } from './billing.entity';
import { PremiumGrant } from './premium-grant.entity';
import { CheckoutPlan } from './dto/create-checkout.dto';

/** Subscription statuses that grant premium access. */
const ACTIVE_STATUSES = new Set(['active', 'trialing']);

/** Where a user's premium access comes from. */
export type EntitlementSource = 'subscription' | 'whitelist' | null;

export interface Entitlement {
  plan: string | null;
  status: string | null;
  isPremium: boolean;
  source: EntitlementSource;
  currentPeriodEnd: number | null;
  cancelAtPeriodEnd: boolean;
  /** Unix seconds when a whitelist grant expires (null = none/indefinite). */
  whitelistExpiresAt: number | null;
}

export interface WhitelistEntry {
  userId: string;
  reason: string | null;
  grantedBy: string | null;
  expiresAt: number | null;
  active: boolean;
}

@Injectable()
export class BillingService {
  private readonly logger = new Logger(BillingService.name);
  private readonly config: StripeConfig;
  /** Reverse map: Stripe price id -> plan key, for decoding webhook events. */
  private readonly priceToPlan: Map<string, string>;

  constructor(
    @InjectRepository(BillingCustomer)
    private readonly customers: Repository<BillingCustomer>,
    @InjectRepository(PremiumGrant)
    private readonly grants: Repository<PremiumGrant>,
    private readonly stripe: StripeService,
    private readonly users: UsersService,
    configService: ConfigService,
  ) {
    this.config = configService.getOrThrow<StripeConfig>('stripe');
    this.priceToPlan = new Map(
      Object.entries(this.config.prices)
        .filter(([, priceId]) => Boolean(priceId))
        .map(([plan, priceId]) => [priceId, plan]),
    );
  }

  /**
   * Create a Stripe Checkout Session for a subscription and return its URL.
   * The client picks a plan; the price is resolved server-side from the
   * allow-list, so the amount can never be tampered with.
   */
  async createCheckoutSession(
    userId: string,
    plan: CheckoutPlan,
  ): Promise<{ url: string }> {
    this.assertConfigured();
    const priceId = this.config.prices[plan];
    if (!priceId) {
      throw new BadRequestException(`Plan "${plan}" is not available.`);
    }

    const customer = await this.ensureCustomer(userId);
    const session = await this.stripe.client.checkout.sessions.create(
      {
        mode: 'subscription',
        customer: customer.stripeCustomerId,
        line_items: [{ price: priceId, quantity: 1 }],
        // Bind the checkout to our user so the webhook can reconcile it.
        client_reference_id: userId,
        metadata: { userId, plan },
        subscription_data: { metadata: { userId, plan } },
        success_url: this.config.successUrl,
        cancel_url: this.config.cancelUrl,
        allow_promotion_codes: true,
      },
      // Idempotency guards against duplicate sessions if the request is retried.
      { idempotencyKey: `checkout:${userId}:${plan}:${Date.now()}` },
    );

    if (!session.url) {
      throw new ServiceUnavailableException('Could not start checkout.');
    }
    return { url: session.url };
  }

  /** Create a Stripe Billing Portal session so a user can manage their plan. */
  async createPortalSession(userId: string): Promise<{ url: string }> {
    this.assertConfigured();
    const customer = await this.customers.findOne({ where: { userId } });
    if (!customer) {
      throw new NotFoundException('No billing account for this user.');
    }
    const session = await this.stripe.client.billingPortal.sessions.create({
      customer: customer.stripeCustomerId,
      return_url: this.config.portalReturnUrl,
    });
    return { url: session.url };
  }

  async getEntitlement(userId: string): Promise<Entitlement> {
    const [customer, grant] = await Promise.all([
      this.customers.findOne({ where: { userId } }),
      this.grants.findOne({ where: { userId } }),
    ]);

    const subscriptionPremium = customer
      ? this.computeSubscriptionPremium(customer)
      : false;
    const grantActive = this.isGrantActive(grant);

    // A whitelist grant takes precedence as the reported source when there is
    // no paid subscription, so free users understand why they have access.
    const source: EntitlementSource = subscriptionPremium
      ? 'subscription'
      : grantActive
        ? 'whitelist'
        : null;

    return {
      plan: customer?.plan ?? null,
      status: customer?.status ?? null,
      isPremium: subscriptionPremium || grantActive,
      source,
      currentPeriodEnd: customer?.currentPeriodEnd
        ? Number(customer.currentPeriodEnd)
        : null,
      cancelAtPeriodEnd: customer?.cancelAtPeriodEnd ?? false,
      whitelistExpiresAt: grant?.expiresAt ? Number(grant.expiresAt) : null,
    };
  }

  async isPremium(userId: string): Promise<boolean> {
    return (await this.getEntitlement(userId)).isPremium;
  }

  // --- whitelist (admin) --------------------------------------------------

  /**
   * Grant a user free premium access, optionally for a defined number of days.
   * Idempotent per user (upserted). `grantedBy` records the acting admin.
   */
  async grantWhitelist(
    targetUserId: string,
    durationDays: number | undefined,
    reason: string | undefined,
    grantedBy: string,
  ): Promise<WhitelistEntry> {
    const user = await this.users.findById(targetUserId);
    if (!user) {
      throw new NotFoundException('Target user not found.');
    }
    const expiresAt =
      durationDays && durationDays > 0
        ? Math.floor(Date.now() / 1000) + durationDays * 24 * 60 * 60
        : null;

    const existing = await this.grants.findOne({
      where: { userId: targetUserId },
    });
    const grant = this.grants.create({
      ...(existing ?? {}),
      userId: targetUserId,
      reason: reason ?? null,
      grantedBy,
      expiresAt,
    });
    const saved = await this.grants.save(grant);
    this.logger.log(
      `Whitelist granted to ${targetUserId} by ${grantedBy}` +
        (expiresAt
          ? ` until ${new Date(expiresAt * 1000).toISOString()}`
          : ' (indefinite)'),
    );
    return this.toWhitelistEntry(saved);
  }

  /** Revoke a user's whitelist grant. Returns true if a grant was removed. */
  async revokeWhitelist(targetUserId: string): Promise<boolean> {
    const result = await this.grants.delete({ userId: targetUserId });
    const removed = (result.affected ?? 0) > 0;
    if (removed) this.logger.log(`Whitelist revoked for ${targetUserId}`);
    return removed;
  }

  async listWhitelist(): Promise<WhitelistEntry[]> {
    const grants = await this.grants.find({ order: { createdAt: 'DESC' } });
    return grants.map((g) => this.toWhitelistEntry(g));
  }

  /**
   * Handle a verified Stripe webhook event. Idempotent: applying the same event
   * twice yields the same state, so Stripe retries are safe.
   */
  async handleWebhookEvent(event: Stripe.Event): Promise<void> {
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session;
        if (session.subscription) {
          const sub = await this.stripe.client.subscriptions.retrieve(
            String(session.subscription),
          );
          await this.applySubscription(sub);
        }
        break;
      }
      case 'customer.subscription.created':
      case 'customer.subscription.updated':
      case 'customer.subscription.deleted': {
        await this.applySubscription(event.data.object as Stripe.Subscription);
        break;
      }
      default:
        // Unhandled event types are acknowledged (200) and ignored.
        this.logger.debug(`Ignoring Stripe event ${event.type}`);
    }
  }

  // --- internals ----------------------------------------------------------

  private async ensureCustomer(userId: string): Promise<BillingCustomer> {
    const existing = await this.customers.findOne({ where: { userId } });
    if (existing) return existing;

    const user = await this.users.findById(userId);
    if (!user) {
      throw new NotFoundException('User not found.');
    }
    const stripeCustomer = await this.stripe.client.customers.create({
      email: user.email,
      name: user.displayName,
      metadata: { userId },
    });
    return this.customers.save(
      this.customers.create({
        userId,
        stripeCustomerId: stripeCustomer.id,
        cancelAtPeriodEnd: false,
      }),
    );
  }

  /** Upsert local subscription state from a Stripe subscription object. */
  private async applySubscription(sub: Stripe.Subscription): Promise<void> {
    const stripeCustomerId = String(sub.customer);
    const customer = await this.customers.findOne({
      where: { stripeCustomerId },
    });
    if (!customer) {
      // We only create customers through our own flow, so this is unexpected.
      this.logger.warn(
        `Webhook for unknown Stripe customer ${stripeCustomerId}; ignoring.`,
      );
      return;
    }

    const item = sub.items?.data?.[0];
    const priceId = item?.price?.id;
    customer.subscriptionId = sub.id;
    customer.status = sub.status;
    customer.plan = priceId
      ? (this.priceToPlan.get(priceId) ?? null)
      : customer.plan;
    customer.currentPeriodEnd = this.readPeriodEnd(sub, item);
    customer.cancelAtPeriodEnd = Boolean(sub.cancel_at_period_end);
    await this.customers.save(customer);
    this.logger.log(
      `Updated subscription for user ${customer.userId}: ${sub.status}`,
    );
  }

  /**
   * `current_period_end` lives on the subscription in older API versions and on
   * the subscription item in newer ones. Read whichever is present.
   */
  private readPeriodEnd(
    sub: Stripe.Subscription,
    item: Stripe.SubscriptionItem | undefined,
  ): number | null {
    const onSub = (sub as unknown as { current_period_end?: number })
      .current_period_end;
    const onItem = (
      item as unknown as { current_period_end?: number } | undefined
    )?.current_period_end;
    return onSub ?? onItem ?? null;
  }

  private computeSubscriptionPremium(customer: BillingCustomer): boolean {
    if (!customer.status || !ACTIVE_STATUSES.has(customer.status)) return false;
    // If we know the period end, treat a lapsed period as not premium.
    if (customer.currentPeriodEnd) {
      return Number(customer.currentPeriodEnd) * 1000 > Date.now();
    }
    return true;
  }

  private isGrantActive(grant: PremiumGrant | null): boolean {
    if (!grant) return false;
    if (grant.expiresAt === null || grant.expiresAt === undefined) return true;
    return Number(grant.expiresAt) * 1000 > Date.now();
  }

  private toWhitelistEntry(grant: PremiumGrant): WhitelistEntry {
    return {
      userId: grant.userId,
      reason: grant.reason,
      grantedBy: grant.grantedBy,
      expiresAt: grant.expiresAt ? Number(grant.expiresAt) : null,
      active: this.isGrantActive(grant),
    };
  }

  private assertConfigured(): void {
    if (!this.stripe.isConfigured()) {
      throw new ServiceUnavailableException(
        'Billing is not configured (STRIPE_SECRET_KEY missing).',
      );
    }
  }
}
