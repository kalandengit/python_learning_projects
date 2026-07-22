import { AsyncLocalStorage } from 'node:async_hooks';
import { Injectable } from '@nestjs/common';
import type { Principal } from './principal';

/** Per-request ambient state propagated to every layer of a request. */
export interface RequestContextStore {
  /** Correlation id for tracing/logging this request end-to-end. */
  correlationId: string;
  /** The authenticated principal, once the auth guard has run. */
  principal?: Principal;
}

/**
 * Ambient request context backed by {@link AsyncLocalStorage}. Lets deep layers
 * (repositories, clients, loggers) read the current tenant/principal and
 * correlation id without threading them through every signature — essential for
 * tenant isolation and correlated observability.
 */
@Injectable()
export class RequestContextService {
  private readonly storage = new AsyncLocalStorage<RequestContextStore>();

  /** Run `callback` with the given store bound as the ambient context. */
  run<T>(store: RequestContextStore, callback: () => T): T {
    return this.storage.run(store, callback);
  }

  /** The active store, or `undefined` when outside a request scope. */
  get store(): RequestContextStore | undefined {
    return this.storage.getStore();
  }

  get correlationId(): string | undefined {
    return this.store?.correlationId;
  }

  get principal(): Principal | undefined {
    return this.store?.principal;
  }

  get tenantId(): string | undefined {
    return this.store?.principal?.tenantId;
  }

  /** Attach the principal to the active store (called by the auth guard). */
  setPrincipal(principal: Principal): void {
    const store = this.store;
    if (store) {
      store.principal = principal;
    }
  }
}
