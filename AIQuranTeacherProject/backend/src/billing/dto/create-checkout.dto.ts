import { IsIn, IsString } from 'class-validator';

/**
 * The client selects a *plan*, never a price or amount. The server maps the
 * plan to an allow-listed Stripe price ID, so a client can never influence
 * what it is charged.
 */
export const CHECKOUT_PLANS = ['premium_monthly', 'premium_yearly'] as const;
export type CheckoutPlan = (typeof CHECKOUT_PLANS)[number];

export class CreateCheckoutDto {
  @IsString()
  @IsIn(CHECKOUT_PLANS)
  plan!: CheckoutPlan;
}
