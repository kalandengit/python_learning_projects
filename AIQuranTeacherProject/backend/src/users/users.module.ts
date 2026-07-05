import { Module } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtModule, JwtModuleOptions } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { TypeOrmModule } from '@nestjs/typeorm';
import { JwtConfig } from '../config/configuration';
import { JwtStrategy } from './strategies/jwt.strategy';
import { User } from './user.entity';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';

@Module({
  imports: [
    TypeOrmModule.forFeature([User]),
    PassportModule,
    JwtModule.registerAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService): JwtModuleOptions => {
        const jwt = config.getOrThrow<JwtConfig>('jwt');
        return {
          secret: jwt.secret,
          // `expiresIn` accepts an `ms`-style string (e.g. "3600s"); the value
          // is validated config, so assert to the library's expected type.
          signOptions: {
            expiresIn: jwt.expiresIn as unknown as number,
          },
        };
      },
    }),
  ],
  controllers: [UsersController],
  providers: [UsersService, JwtStrategy],
  exports: [UsersService],
})
export class UsersModule {}
