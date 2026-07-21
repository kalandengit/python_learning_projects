import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  PrimaryGeneratedColumn,
  UpdateDateColumn,
} from 'typeorm';

export enum UserRole {
  Student = 'student',
  Teacher = 'teacher',
  Admin = 'admin',
}

@Entity({ name: 'users' })
export class User {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Index({ unique: true })
  @Column({ type: 'varchar', length: 320 })
  email!: string;

  /** bcrypt hash — never select by default so it can't leak accidentally. */
  @Column({ type: 'varchar', select: false })
  passwordHash!: string;

  @Column({ type: 'varchar', length: 80 })
  displayName!: string;

  @Column({ type: 'varchar', default: UserRole.Student })
  role!: UserRole;

  @CreateDateColumn()
  createdAt!: Date;

  @UpdateDateColumn()
  updatedAt!: Date;
}
