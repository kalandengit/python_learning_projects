import { Controller, Get } from '@nestjs/common';
import { ApiBearerAuth, ApiOkResponse, ApiTags } from '@nestjs/swagger';
import {
  CurrentTenant,
  CurrentUser,
  RequestContextService,
  type Principal,
} from '@asa/auth';

/** The authenticated caller's own identity view. */
export interface MeResponse {
  subject: string;
  tenantId?: string;
  username?: string;
  email?: string;
  roles: string[];
  scopes: string[];
  correlationId?: string;
  /** Tenant read from the ambient request context (not the decorator). */
  contextTenantId?: string;
}

/**
 * Returns the current principal. Demonstrates the `@CurrentUser` /
 * `@CurrentTenant` parameter decorators and reading ambient state from the
 * {@link RequestContextService}. Authenticated by the global guard.
 */
@ApiTags('me')
@ApiBearerAuth()
@Controller('me')
export class MeController {
  constructor(private readonly context: RequestContextService) {}

  @Get()
  @ApiOkResponse({ description: 'The authenticated principal.' })
  me(
    @CurrentUser() user: Principal,
    @CurrentTenant() tenantId: string | undefined,
  ): MeResponse {
    return {
      subject: user.subject,
      tenantId,
      username: user.username,
      email: user.email,
      roles: user.roles,
      scopes: user.scopes,
      correlationId: this.context.correlationId,
      contextTenantId: this.context.tenantId,
    };
  }
}
