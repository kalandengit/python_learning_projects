import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';
import { AuthenticatedUser } from '../../common/decorators/current-user.decorator';
import { JwtConfig } from '../../config/configuration';

export interface JwtPayload {
  sub: string;
  email: string;
}

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor(configService: ConfigService) {
    const jwt = configService.getOrThrow<JwtConfig>('jwt');
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: jwt.secret,
      // Pin the accepted algorithm so a forged "none"/RS256->HS256 token is
      // rejected (algorithm-confusion mitigation), and bind tokens to this
      // service via issuer/audience.
      algorithms: [jwt.algorithm],
      issuer: jwt.issuer,
      audience: jwt.audience,
    });
  }

  /** Return value is attached to `request.user`. */
  validate(payload: JwtPayload): AuthenticatedUser {
    return { userId: payload.sub, email: payload.email };
  }
}
