export type HealthState = 'ok' | 'degraded' | 'error';

export interface HealthCheck {
  name: string;
  status: HealthState;
  detail?: string;
}

export interface HealthReport {
  status: HealthState;
  checks: HealthCheck[];
  timestamp: string;
}
