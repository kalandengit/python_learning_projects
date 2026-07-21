import { BadRequestException, NotFoundException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import Stripe from 'stripe';
import { StripeService } from '../common/stripe/stripe.service';
import { UsersService } from '../users/users.service';
import { BillingCustomer } from './billing.entity';
import { BillingService } from './billing.service';
import { PremiumGrant } from './premium-grant.entity';

const stripeConfig = {
  secretKey: 'sk_test',
  webhookSecret: 'whsec_test',
  publishableKey: 'pk_test',
  prices: { premium_monthly: 'price_month', premium_yearly: 'price_year' },
  successUrl: 'https://app/success',
  cancelUrl: 'https://app/cancel',
  portalReturnUrl: 'https://app/billing',
};

const nowSec = () => Math.floor(Date.now() / 1000);

describe('BillingService', () => {
  let service: BillingService;
  let customers: Record<string, jest.Mock>;
  let grants: Record<string, jest.Mock>;
  let stripe: {
    isConfigured: jest.Mock;
    client: {
      checkout: { sessions: { create: jest.Mock } };
      customers: { create: jest.Mock };
      billingPortal: { sessions: { create: jest.Mock } };
      subscriptions: { retrieve: jest.Mock };
    };
    constructWebhookEvent: jest.Mock;
  };
  let users: { findById: jest.Mock };

  beforeEach(() => {
    customers = {
      findOne: jest.fn(),
      create: jest.fn((x) => x),
      save: jest.fn(async (x) => x),
    };
    grants = {
      findOne: jest.fn(),
      create: jest.fn((x) => x),
      save: jest.fn(async (x) => x),
      delete: jest.fn(async () => ({ affected: 1 })),
      find: jest.fn(async () => []),
    };
    stripe = {
      isConfigured: jest.fn().mockReturnValue(true),
      client: {
        checkout: { sessions: { create: jest.fn() } },
        customers: { create: jest.fn() },
        billingPortal: { sessions: { create: jest.fn() } },
        subscriptions: { retrieve: jest.fn() },
      },
      constructWebhookEvent: jest.fn(),
    };
    users = { findById: jest.fn() };

    const configService = {
      getOrThrow: () => stripeConfig,
    } as unknown as ConfigService;

    service = new BillingService(
      customers as never,
      grants as never,
      stripe as unknown as StripeService,
      users as unknown as UsersService,
      configService,
    );
  });

  describe('createCheckoutSession', () => {
    it('resolves the price server-side and returns the session URL', async () => {
      customers.findOne.mockResolvedValue({
        userId: 'u1',
        stripeCustomerId: 'cus_1',
      });
      stripe.client.checkout.sessions.create.mockResolvedValue({
        url: 'https://checkout.stripe.com/x',
      });

      const res = await service.createCheckoutSession('u1', 'premium_monthly');
      expect(res.url).toBe('https://checkout.stripe.com/x');
      const args = stripe.client.checkout.sessions.create.mock.calls[0][0];
      expect(args.line_items[0].price).toBe('price_month'); // from allow-list
      expect(args.customer).toBe('cus_1');
      expect(args.client_reference_id).toBe('u1');
    });

    it('creates a Stripe customer on first checkout', async () => {
      customers.findOne.mockResolvedValue(null);
      users.findById.mockResolvedValue({
        id: 'u1',
        email: 'a@b.com',
        displayName: 'A',
      });
      stripe.client.customers.create.mockResolvedValue({ id: 'cus_new' });
      stripe.client.checkout.sessions.create.mockResolvedValue({
        url: 'https://checkout/x',
      });

      await service.createCheckoutSession('u1', 'premium_yearly');
      expect(stripe.client.customers.create).toHaveBeenCalledWith(
        expect.objectContaining({
          email: 'a@b.com',
          metadata: { userId: 'u1' },
        }),
      );
    });

    it('rejects an unconfigured plan price', async () => {
      const cfg2 = {
        ...stripeConfig,
        prices: { premium_monthly: '', premium_yearly: '' },
      };
      const svc = new BillingService(
        customers as never,
        grants as never,
        stripe as unknown as StripeService,
        users as unknown as UsersService,
        { getOrThrow: () => cfg2 } as unknown as ConfigService,
      );
      await expect(
        svc.createCheckoutSession('u1', 'premium_monthly'),
      ).rejects.toBeInstanceOf(BadRequestException);
    });
  });

  describe('getEntitlement', () => {
    it('is not premium with no subscription and no grant', async () => {
      customers.findOne.mockResolvedValue(null);
      grants.findOne.mockResolvedValue(null);
      const e = await service.getEntitlement('u1');
      expect(e.isPremium).toBe(false);
      expect(e.source).toBeNull();
    });

    it('is premium via an active subscription', async () => {
      customers.findOne.mockResolvedValue({
        userId: 'u1',
        status: 'active',
        plan: 'premium_monthly',
        currentPeriodEnd: nowSec() + 3600,
        cancelAtPeriodEnd: false,
      } as BillingCustomer);
      grants.findOne.mockResolvedValue(null);
      const e = await service.getEntitlement('u1');
      expect(e.isPremium).toBe(true);
      expect(e.source).toBe('subscription');
    });

    it('is premium via a non-expired whitelist grant', async () => {
      customers.findOne.mockResolvedValue(null);
      grants.findOne.mockResolvedValue({
        userId: 'u1',
        expiresAt: nowSec() + 86400,
      } as PremiumGrant);
      const e = await service.getEntitlement('u1');
      expect(e.isPremium).toBe(true);
      expect(e.source).toBe('whitelist');
    });

    it('is not premium when the whitelist grant has expired', async () => {
      customers.findOne.mockResolvedValue(null);
      grants.findOne.mockResolvedValue({
        userId: 'u1',
        expiresAt: nowSec() - 10,
      } as PremiumGrant);
      const e = await service.getEntitlement('u1');
      expect(e.isPremium).toBe(false);
    });

    it('treats an indefinite grant (null expiry) as active', async () => {
      customers.findOne.mockResolvedValue(null);
      grants.findOne.mockResolvedValue({
        userId: 'u1',
        expiresAt: null,
      } as PremiumGrant);
      expect(await service.isPremium('u1')).toBe(true);
    });
  });

  describe('whitelist management', () => {
    it('grants access for a defined period', async () => {
      users.findById.mockResolvedValue({ id: 'u2' });
      grants.findOne.mockResolvedValue(null);
      const entry = await service.grantWhitelist(
        'u2',
        30,
        'scholarship',
        'admin1',
      );
      expect(entry.userId).toBe('u2');
      expect(entry.active).toBe(true);
      expect(entry.expiresAt).toBeGreaterThan(nowSec());
      expect(entry.grantedBy).toBe('admin1');
    });

    it('rejects granting to a non-existent user', async () => {
      users.findById.mockResolvedValue(null);
      await expect(
        service.grantWhitelist('ghost', 30, undefined, 'admin1'),
      ).rejects.toBeInstanceOf(NotFoundException);
    });

    it('revokes a grant', async () => {
      expect(await service.revokeWhitelist('u2')).toBe(true);
      expect(grants.delete).toHaveBeenCalledWith({ userId: 'u2' });
    });
  });

  describe('handleWebhookEvent', () => {
    it('applies a subscription update to the matching customer', async () => {
      customers.findOne.mockResolvedValue({
        userId: 'u1',
        stripeCustomerId: 'cus_1',
      } as BillingCustomer);

      const event = {
        type: 'customer.subscription.updated',
        data: {
          object: {
            id: 'sub_1',
            customer: 'cus_1',
            status: 'active',
            cancel_at_period_end: false,
            current_period_end: nowSec() + 3600,
            items: { data: [{ price: { id: 'price_month' } }] },
          },
        },
      } as unknown as Stripe.Event;

      await service.handleWebhookEvent(event);
      const saved = customers.save.mock.calls[0][0];
      expect(saved.status).toBe('active');
      expect(saved.plan).toBe('premium_monthly'); // reverse-mapped from price id
      expect(saved.subscriptionId).toBe('sub_1');
    });

    it('ignores webhooks for unknown customers', async () => {
      customers.findOne.mockResolvedValue(null);
      const event = {
        type: 'customer.subscription.deleted',
        data: {
          object: {
            id: 'sub_x',
            customer: 'cus_unknown',
            status: 'canceled',
            items: { data: [] },
          },
        },
      } as unknown as Stripe.Event;
      await service.handleWebhookEvent(event);
      expect(customers.save).not.toHaveBeenCalled();
    });
  });
});
