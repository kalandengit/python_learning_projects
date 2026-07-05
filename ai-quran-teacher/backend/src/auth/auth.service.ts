import {
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcryptjs';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from '../users/user.entity';
import { AuthCredential } from './auth.entity';
import { LoginDto, RegisterDto } from './auth.dto';

const BCRYPT_ROUNDS = 12;

export interface AuthResult {
  accessToken: string;
  user: Pick<User, 'id' | 'email' | 'name' | 'role'>;
}

@Injectable()
export class AuthService {
  constructor(
    @InjectRepository(User)
    private readonly usersRepository: Repository<User>,
    @InjectRepository(AuthCredential)
    private readonly credentialsRepository: Repository<AuthCredential>,
    private readonly jwtService: JwtService,
  ) {}

  async register(dto: RegisterDto): Promise<AuthResult> {
    const existing = await this.usersRepository.findOne({
      where: { email: dto.email },
    });
    if (existing) {
      throw new UnauthorizedException('Email is already registered');
    }
    const user = await this.usersRepository.save(
      this.usersRepository.create({
        email: dto.email,
        name: dto.name,
        role: dto.role,
        language: dto.language,
      }),
    );
    const passwordHash = await bcrypt.hash(dto.password, BCRYPT_ROUNDS);
    await this.credentialsRepository.save(
      this.credentialsRepository.create({ userId: user.id, passwordHash }),
    );
    return this.issueToken(user);
  }

  async login(dto: LoginDto): Promise<AuthResult> {
    const user = await this.usersRepository.findOne({
      where: { email: dto.email },
    });
    if (!user) {
      throw new UnauthorizedException('Invalid email or password');
    }
    const credential = await this.credentialsRepository.findOne({
      where: { userId: user.id },
    });
    const ok =
      credential &&
      (await bcrypt.compare(dto.password, credential.passwordHash));
    if (!ok) {
      throw new UnauthorizedException('Invalid email or password');
    }
    return this.issueToken(user);
  }

  private issueToken(user: User): AuthResult {
    const accessToken = this.jwtService.sign({
      sub: user.id,
      email: user.email,
      role: user.role,
    });
    return {
      accessToken,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        role: user.role,
      },
    };
  }
}
