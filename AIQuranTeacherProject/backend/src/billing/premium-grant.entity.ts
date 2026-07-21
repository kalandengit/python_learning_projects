import {
  Column,
  CreateDateColumn,
  Entity,
  PrimaryColumn,
  UpdateDateColumn,
} from 'typeorm';

/**
 * A "whitelist" grant: an admin gives a user premium access without payment,
 * optionally until a defined expiry. One grant per user (upserted). A grant
 * with `expiresAt = null` never expires until revoked.
 */
@Entity({ name: 'premium_grants' })
export class PremiumGrant {
  @PrimaryColumn({ type: 'uuid' })
  userId!: string;

  /** Why the grant was given (e.g. "beta tester", "scholarship"). */
  @Column({ type: 'varchar', length: 200, nullable: true })
  reason!: string | null;

  /** The admin user id who created the grant (audit trail). */
  @Column({ type: 'uuid', nullable: true })
  grantedBy!: string | null;

  /**
   * When the free access ends, as Unix seconds. Null = indefinite (until
   * revoked). Stored as an integer for portability across SQLite and Postgres.
   */
  @Column({ type: 'bigint', nullable: true })
  expiresAt!: number | null;

  @CreateDateColumn()
  createdAt!: Date;

  @UpdateDateColumn()
  updatedAt!: Date;
}
