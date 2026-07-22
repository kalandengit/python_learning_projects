import { SetMetadata } from '@nestjs/common';

/** Metadata key marking a route handler (or controller) as unauthenticated. */
export const IS_PUBLIC_KEY = 'asa:auth:public';

/**
 * Opt a route out of authentication. Use sparingly — health probes, metrics,
 * and OIDC callbacks. Everything else is authenticated by default (deny-by-
 * default posture).
 */
export const Public = (): MethodDecorator & ClassDecorator =>
  SetMetadata(IS_PUBLIC_KEY, true);
