import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  PrimaryColumn,
  UpdateDateColumn,
} from 'typeorm';

/**
 * Local mirror of a user's Stripe billing state. Stripe is the source of truth;
 * this row is kept in sync via webhooks so entitlement checks don't need a
 * round-trip to Stripe on every request. Created lazily at first checkout.
 */
@Entity({ name: 'billing_customers' })
export class BillingCustomer {
  @PrimaryColumn({ type: 'uuid' })
  userId!: string;

  @Index({ unique: true })
  @Column({ type: 'varchar' })
  stripeCustomerId!: string;

  @Column({ type: 'varchar', nullable: true })
  subscriptionId!: string | null;

  /** Plan key from the server-side allow-list (e.g. "premium_monthly"). */
  @Column({ type: 'varchar', nullable: true })
  plan!: string | null;

  /**
   * Stripe subscription status: active, trialing, past_due, canceled,
   * incomplete, incomplete_expired, unpaid, paused, or null if never subscribed.
   */
  @Column({ type: 'varchar', nullable: true })
  status!: string | null;

  /** Unix seconds when the current paid period ends. */
  @Column({ type: 'bigint', nullable: true })
  currentPeriodEnd!: number | null;

  @Column({ type: 'boolean', default: false })
  cancelAtPeriodEnd!: boolean;

  @CreateDateColumn()
  createdAt!: Date;

  @UpdateDateColumn()
  updatedAt!: Date;
}
