import axios from 'axios';

/**
 * API client implementing the Section-9 contracts:
 * - Idempotency-Key (UUID) on every POST/PATCH (ADR-017)
 * - RFC 7807 problem+json surfaced as typed errors
 * - cursor pagination envelope helpers (ADR-018)
 */
export const api = axios.create({
  baseURL: '/v1',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  if (config.method === 'post' || config.method === 'patch') {
    config.headers['Idempotency-Key'] ??= crypto.randomUUID();
  }
  return config;
});

export interface Problem {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  traceId?: string;
}

api.interceptors.response.use(
  (r) => r,
  (error) => {
    const problem: Problem | undefined = error.response?.data?.type
      ? error.response.data
      : undefined;
    return Promise.reject(problem ?? error);
  },
);

export interface Page<T> {
  data: T[];
  links: { next: string | null; prev: string | null };
  meta: { pageSize: number };
}

export interface Visit {
  visitId: string;
  state:
    | 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'CHECKED_IN'
    | 'CHECKED_OUT' | 'CANCELLED' | 'EXPIRED' | 'SECURITY_REVIEW';
  visitor: { fullName: string; email: string; company?: string };
  hostId: string;
  siteId: string;
  purpose: string;
  window: { startsAt: string; endsAt: string };
  createdAt: string;
}

export const listVisits = async (params?: Record<string, string>) =>
  (await api.get<Page<Visit>>('/visitors', { params })).data;

export const registerVisit = async (body: {
  visitor: { fullName: string; email: string; company?: string };
  hostId: string;
  siteId: string;
  purpose: string;
  window: { startsAt: string; endsAt: string };
}) => (await api.post<Visit>('/visitors', body)).data;
