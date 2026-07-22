import {
  DynamicModule,
  InjectionToken,
  MiddlewareConsumer,
  Module,
  NestModule,
  OptionalFactoryDependency,
  Provider,
} from '@nestjs/common';
import { APP_GUARD } from '@nestjs/core';
import { JwtAuthGuard } from './jwt-auth.guard';
import { RequestContextMiddleware } from './request-context.middleware';
import { RequestContextService } from './request-context';
import { RolesGuard } from './roles.guard';
import { TokenVerifier } from './token-verifier';
import { AUTH_OPTIONS, TOKEN_VERIFIER, type AuthOptions } from './tokens';

/** Async configuration for {@link AuthModule.forRootAsync}. */
export interface AuthModuleAsyncOptions {
  imports?: DynamicModule['imports'];
  inject?: Array<InjectionToken | OptionalFactoryDependency>;
  useFactory: (...args: never[]) => AuthOptions | Promise<AuthOptions>;
}

/**
 * Global authentication + authorization module.
 *
 * Wires the {@link TokenVerifier} (remote JWKS) under {@link TOKEN_VERIFIER},
 * {@link JwtAuthGuard} then {@link RolesGuard} as global guards (order matters:
 * authenticate before authorizing), and the {@link RequestContextInterceptor}
 * for ambient request context.
 *
 * Tests override the {@link TOKEN_VERIFIER} provider with a locally-keyed
 * verifier, exercising the real verification path without a network dependency.
 */
@Module({})
export class AuthModule implements NestModule {
  configure(consumer: MiddlewareConsumer): void {
    consumer.apply(RequestContextMiddleware).forRoutes('*');
  }

  static forRoot(options: AuthOptions): DynamicModule {
    return AuthModule.build([{ provide: AUTH_OPTIONS, useValue: options }]);
  }

  static forRootAsync(options: AuthModuleAsyncOptions): DynamicModule {
    return AuthModule.build(
      [
        {
          provide: AUTH_OPTIONS,
          useFactory: options.useFactory,
          inject: options.inject ?? [],
        },
      ],
      options.imports,
    );
  }

  private static build(
    optionsProviders: Provider[],
    imports?: DynamicModule['imports'],
  ): DynamicModule {
    const providers: Provider[] = [
      ...optionsProviders,
      {
        provide: TOKEN_VERIFIER,
        useFactory: (opts: AuthOptions) =>
          TokenVerifier.remote(opts.jwksUri, {
            issuer: opts.issuer,
            audience: opts.audience,
          }),
        inject: [AUTH_OPTIONS],
      },
      RequestContextService,
      { provide: APP_GUARD, useClass: JwtAuthGuard },
      { provide: APP_GUARD, useClass: RolesGuard },
    ];

    return {
      module: AuthModule,
      global: true,
      imports: imports ?? [],
      providers,
      exports: [AUTH_OPTIONS, TOKEN_VERIFIER, RequestContextService],
    };
  }
}
