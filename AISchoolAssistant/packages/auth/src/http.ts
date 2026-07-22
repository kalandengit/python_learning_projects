import type { Principal } from './principal';

/**
 * Minimal structural view of an HTTP request the auth layer needs. Declared
 * locally so the package stays decoupled from any specific HTTP framework
 * (Express, Fastify, …) — it only reads headers and attaches the principal.
 */
export interface HttpRequest {
  headers: Record<string, string | string[] | undefined>;
  principal?: Principal;
}

/** Minimal structural view of an HTTP response (used to echo correlation ids). */
export interface HttpResponse {
  setHeader(name: string, value: string): void;
}
