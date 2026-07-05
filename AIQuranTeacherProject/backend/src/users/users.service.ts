import {
  ConflictException,
  Injectable,
  Logger,
  UnauthorizedException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';
import { InjectRepository } from '@nestjs/typeorm';
import * as bcrypt from 'bcryptjs';
import { Repository } from 'typeorm';
import { JwtConfig } from '../config/configuration';
import { JwtPayload } from './strategies/jwt.strategy';
import { LoginDto } from './dto/login.dto';
import { RegisterDto } from './dto/register.dto';
import { User } from './user.entity';

export interface PublicUser {
  id: string;
  email: string;
  displayName: string;
  role: string;
  createdAt: Date;
}

export interface AuthResult {
  accessToken: string;
  expiresIn: string;
  user: PublicUser;
}

const BCRYPT_ROUNDS = 12;

@Injectable()
export class UsersService {
  private readonly logger = new Logger(UsersService.name);

  constructor(
    @InjectRepository(User) private readonly users: Repository<User>,
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
  ) {}

  async register(dto: RegisterDto): Promise<AuthResult> {
    const email = dto.email.trim().toLowerCase();
    const existing = await this.users.findOne({ where: { email } });
    if (existing) {
      // Do not reveal which field collided beyond the email itself.
      throw new ConflictException('An account with this email already exists.');
    }

    const passwordHash = await bcrypt.hash(dto.password, BCRYPT_ROUNDS);
    const user = this.users.create({
      email,
      displayName: dto.displayName.trim(),
      passwordHash,
    });
    const saved = await this.users.save(user);
    this.logger.log(`Registered user ${saved.id}`);
    return this.issueToken(saved);
  }

  async login(dto: LoginDto): Promise<AuthResult> {
    const email = dto.email.trim().toLowerCase();
    // passwordHash is `select: false`, so request it explicitly.
    const user = await this.users
      .createQueryBuilder('user')
      .addSelect('user.passwordHash')
      .where('user.email = :email', { email })
      .getOne();

    // Always run a compare to keep timing consistent whether or not the user
    // exists, mitigating user-enumeration via response time.
    const hash =
      user?.passwordHash ??
      '$2a$12$invalidinvalidinvalidinvalidinvalidinvalidinva';
    const ok = await bcrypt.compare(dto.password, hash);
    if (!user || !ok) {
      throw new UnauthorizedException('Invalid email or password.');
    }
    return this.issueToken(user);
  }

  async findById(id: string): Promise<User | null> {
    return this.users.findOne({ where: { id } });
  }

  private issueToken(user: User): AuthResult {
    const payload: JwtPayload = { sub: user.id, email: user.email };
    const jwtConfig = this.configService.getOrThrow<JwtConfig>('jwt');
    const accessToken = this.jwtService.sign(payload);
    return {
      accessToken,
      expiresIn: jwtConfig.expiresIn,
      user: this.toPublic(user),
    };
  }

  toPublic(user: User): PublicUser {
    return {
      id: user.id,
      email: user.email,
      displayName: user.displayName,
      role: user.role,
      createdAt: user.createdAt,
    };
  }
}
