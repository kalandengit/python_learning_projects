import type { JWTPayload } from 'jose';
import { toPrincipal } from './claims';

const base: JWTPayload = {
  sub: 'user-1',
  preferred_username: 'ada',
  email: 'ada@example.test',
  tenant_id: 'tenant-42',
  scope: 'openid profile examples:read',
  realm_access: { roles: ['teacher', 'user'] },
  resource_access: { 'asa-api': { roles: ['examples:admin'] } },
};

describe('toPrincipal', () => {
  it('maps subject, tenant, username, email, and scopes', () => {
    const principal = toPrincipal(base, { tenantClaim: 'tenant_id' });
    expect(principal.subject).toBe('user-1');
    expect(principal.tenantId).toBe('tenant-42');
    expect(principal.username).toBe('ada');
    expect(principal.email).toBe('ada@example.test');
    expect(principal.scopes).toEqual(['openid', 'profile', 'examples:read']);
  });

  it('includes realm roles only when no client id is configured', () => {
    const principal = toPrincipal(base, { tenantClaim: 'tenant_id' });
    expect(principal.roles).toEqual(['teacher', 'user']);
  });

  it('merges client roles when a client id is configured (de-duplicated)', () => {
    const principal = toPrincipal(
      { ...base, resource_access: { 'asa-api': { roles: ['teacher', 'x'] } } },
      { tenantClaim: 'tenant_id', clientId: 'asa-api' },
    );
    expect(principal.roles).toEqual(['teacher', 'user', 'x']);
  });

  it('tolerates missing optional claims', () => {
    const principal = toPrincipal(
      { sub: 'user-2' },
      { tenantClaim: 'tenant_id' },
    );
    expect(principal.tenantId).toBeUndefined();
    expect(principal.roles).toEqual([]);
    expect(principal.scopes).toEqual([]);
  });

  it('throws when the subject claim is absent', () => {
    expect(() => toPrincipal({}, { tenantClaim: 'tenant_id' })).toThrow(/sub/);
  });

  it('ignores malformed role structures instead of throwing', () => {
    const principal = toPrincipal(
      { sub: 'user-3', realm_access: { roles: 'not-an-array' } },
      { tenantClaim: 'tenant_id' },
    );
    expect(principal.roles).toEqual([]);
  });
});
