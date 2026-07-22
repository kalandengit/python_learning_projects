/**
 * The authenticated caller for a request, derived from a verified access
 * token. This is the single, framework-agnostic representation of "who is
 * making this request" that guards, controllers, and downstream layers read.
 */
export interface Principal {
  /** Stable subject identifier (`sub` claim). */
  subject: string;
  /** Tenant/organization the caller belongs to, for multi-tenant isolation. */
  tenantId?: string;
  /** Human-friendly username (`preferred_username`), when present. */
  username?: string;
  /** Email address, when present and the caller consented to the scope. */
  email?: string;
  /** Flattened realm + client roles used for RBAC checks. */
  roles: string[];
  /** OAuth scopes granted to the token (`scope` claim, space-delimited). */
  scopes: string[];
  /** The raw verified claim set, for advanced or feature-specific needs. */
  claims: Record<string, unknown>;
}

/** True when the principal has every one of the required roles. */
export function hasAllRoles(principal: Principal, required: string[]): boolean {
  return required.every((role) => principal.roles.includes(role));
}

/** True when the principal has at least one of the required roles. */
export function hasAnyRole(principal: Principal, required: string[]): boolean {
  return required.some((role) => principal.roles.includes(role));
}
