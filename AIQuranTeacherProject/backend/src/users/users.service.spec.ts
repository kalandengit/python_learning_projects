import { ConflictException, UnauthorizedException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcryptjs';
import { User } from './user.entity';
import { UsersService } from './users.service';

describe('UsersService', () => {
  let service: UsersService;
  let repo: {
    findOne: jest.Mock;
    create: jest.Mock;
    save: jest.Mock;
    createQueryBuilder: jest.Mock;
  };
  let jwt: { sign: jest.Mock };
  let config: { getOrThrow: jest.Mock };

  const password = 'Password123';
  let hash: string;

  beforeAll(async () => {
    hash = await bcrypt.hash(password, 10);
  });

  beforeEach(() => {
    repo = {
      findOne: jest.fn(),
      create: jest.fn((x) => x),
      save: jest.fn(async (x) => ({
        id: 'user-1',
        createdAt: new Date(),
        role: 'student',
        ...x,
      })),
      createQueryBuilder: jest.fn(),
    };
    jwt = { sign: jest.fn().mockReturnValue('signed.jwt.token') };
    config = {
      getOrThrow: jest.fn().mockReturnValue({
        secret: 'x'.repeat(32),
        expiresIn: '3600s',
      }),
    };
    service = new UsersService(
      repo as never,
      jwt as unknown as JwtService,
      config as unknown as ConfigService,
    );
  });

  describe('register', () => {
    it('hashes the password, issues a token and hides the hash', async () => {
      repo.findOne.mockResolvedValue(null);
      const result = await service.register({
        email: 'Test@Example.com',
        displayName: 'Aisha',
        password,
      });

      expect(result.accessToken).toBe('signed.jwt.token');
      expect(result.user.email).toBe('test@example.com'); // normalised
      expect(result.user).not.toHaveProperty('passwordHash');

      const saved = repo.save.mock.calls[0][0] as User;
      expect(saved.passwordHash).not.toBe(password);
      await expect(bcrypt.compare(password, saved.passwordHash)).resolves.toBe(
        true,
      );
    });

    it('rejects a duplicate email', async () => {
      repo.findOne.mockResolvedValue({ id: 'existing' });
      await expect(
        service.register({
          email: 'test@example.com',
          displayName: 'Aisha',
          password,
        }),
      ).rejects.toBeInstanceOf(ConflictException);
    });
  });

  describe('login', () => {
    const mockQueryBuilder = (user: Partial<User> | null) => ({
      addSelect: jest.fn().mockReturnThis(),
      where: jest.fn().mockReturnThis(),
      getOne: jest.fn().mockResolvedValue(user),
    });

    it('returns a token for valid credentials', async () => {
      repo.createQueryBuilder.mockReturnValue(
        mockQueryBuilder({
          id: 'user-1',
          email: 'test@example.com',
          displayName: 'Aisha',
          passwordHash: hash,
          role: 'student' as never,
          createdAt: new Date(),
        }),
      );
      const result = await service.login({
        email: 'test@example.com',
        password,
      });
      expect(result.accessToken).toBe('signed.jwt.token');
    });

    it('rejects a wrong password', async () => {
      repo.createQueryBuilder.mockReturnValue(
        mockQueryBuilder({
          id: 'user-1',
          email: 'test@example.com',
          passwordHash: hash,
        }),
      );
      await expect(
        service.login({
          email: 'test@example.com',
          password: 'wrong-password',
        }),
      ).rejects.toBeInstanceOf(UnauthorizedException);
    });

    it('rejects an unknown user without leaking which field failed', async () => {
      repo.createQueryBuilder.mockReturnValue(mockQueryBuilder(null));
      await expect(
        service.login({ email: 'ghost@example.com', password }),
      ).rejects.toBeInstanceOf(UnauthorizedException);
    });
  });
});
