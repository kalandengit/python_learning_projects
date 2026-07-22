import { RequestContextService } from './request-context';
import type { Principal } from './principal';

function principal(tenantId: string): Principal {
  return { subject: 'u', tenantId, roles: [], scopes: [], claims: {} };
}

describe('RequestContextService', () => {
  let service: RequestContextService;

  beforeEach(() => {
    service = new RequestContextService();
  });

  it('returns undefined outside of a request scope', () => {
    expect(service.store).toBeUndefined();
    expect(service.correlationId).toBeUndefined();
    expect(service.tenantId).toBeUndefined();
  });

  it('exposes the bound store within run()', () => {
    service.run({ correlationId: 'cid-1', principal: principal('t-1') }, () => {
      expect(service.correlationId).toBe('cid-1');
      expect(service.tenantId).toBe('t-1');
      expect(service.principal?.subject).toBe('u');
    });
  });

  it('isolates concurrent contexts', async () => {
    const seen: Array<string | undefined> = [];
    await Promise.all([
      new Promise<void>((resolve) =>
        service.run({ correlationId: 'a' }, () => {
          setTimeout(() => {
            seen.push(service.correlationId);
            resolve();
          }, 5);
        }),
      ),
      new Promise<void>((resolve) =>
        service.run({ correlationId: 'b' }, () => {
          setTimeout(() => {
            seen.push(service.correlationId);
            resolve();
          }, 1);
        }),
      ),
    ]);
    expect(seen.sort()).toEqual(['a', 'b']);
  });

  it('setPrincipal mutates the active store', () => {
    service.run({ correlationId: 'cid' }, () => {
      expect(service.principal).toBeUndefined();
      service.setPrincipal(principal('t-9'));
      expect(service.tenantId).toBe('t-9');
    });
  });

  it('setPrincipal is a no-op outside a scope', () => {
    expect(() => service.setPrincipal(principal('t'))).not.toThrow();
  });
});
