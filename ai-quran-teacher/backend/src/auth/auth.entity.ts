import {
  Column,
  Entity,
  Index,
  PrimaryGeneratedColumn,
  UpdateDateColumn,
} from 'typeorm';

/** Password credentials, kept separate from the User profile entity. */
@Entity('auth_credentials')
export class AuthCredential {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Index({ unique: true })
  @Column()
  userId: string;

  @Column()
  passwordHash: string;

  @UpdateDateColumn()
  updatedAt: Date;
}
