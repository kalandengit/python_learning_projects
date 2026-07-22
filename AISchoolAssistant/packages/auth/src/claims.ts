import type { JWTPayload } from 'jose';
import type { Principal } from './principal';

/** Options controlling how raw JWT claims are mapped to a {@link Principal}. */
export interface ClaimMappingOptions {
  /** Claim name holding the tenant id (e.g. `tenant_id`). */
  tenantClaim: string;
  /** Optional client id whose `resource_access` roles are also included. */
  clientId?: string;
}

interface KeycloakAccess {
  roles?: unknown;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === 'string');
}

function asString(value: unknown): string | undefined {
  return typeof value === 'string' && value.length > 0 ? value : undefined;
}

/**
 * Extract realm roles (`realm_access.roles`) and, when a client id is
 * configured, that client's roles (`resource_access[clientId].roles`). Both
 * are de-duplicated so a role granted at both levels appears once.
 */
function extractRoles(payload: JWTPayload, clientId?: string): string[] {
  const realm = payload.realm_access as KeycloakAccess | undefined;
  const roles = new Set(asStringArray(realm?.roles));

  if (clientId) {
    const resource = payload.resource_access as
      Record<string, KeycloakAccess> | undefined;
    for (const role of asStringArray(resource?.[clientId]?.roles)) {
      roles.add(role);
    }
  }

  return [...roles];
}

/**
 * Map a verified JWT payload onto the platform {@link Principal}. Pure and
 * side-effect free so it is trivially unit-testable and reused wherever a
 * principal must be derived from claims.
 */
export function toPrincipal(
  payload: JWTPayload,
  options: ClaimMappingOptions,
): Principal {
  const subject = asString(payload.sub);
  if (!subject) {
    throw new Error('Access token is missing the required `sub` claim.');
  }

  const scope = asString(payload.scope);

  return {
    subject,
    tenantId: asString(payload[options.tenantClaim]),
    username: asString(payload.preferred_username),
    email: asString(payload.email),
    roles: extractRoles(payload, options.clientId),
    scopes: scope ? scope.split(' ').filter(Boolean) : [],
    claims: payload as Record<string, unknown>,
  };
}
