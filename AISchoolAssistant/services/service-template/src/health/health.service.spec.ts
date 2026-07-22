import { HealthService } from './health.service';

describe('HealthService', () => {
  let service: HealthService;

  beforeEach(() => {
    service = new HealthService();
  });

  it('reports liveness as ok', () => {
    const report = service.liveness();
    expect(report.status).toBe('ok');
    expect(report.checks[0].name).toBe('process');
  });

  it('reports ok readiness when no indicators are registered', async () => {
    const report = await service.readiness();
    expect(report.status).toBe('ok');
  });

  it('rolls up to error when any indicator fails', async () => {
    service.register({
      name: 'db',
      check: () => ({ name: 'db', status: 'ok' }),
    });
    service.register({
      name: 'cache',
      check: () => ({ name: 'cache', status: 'error' }),
    });
    const report = await service.readiness();
    expect(report.status).toBe('error');
  });

  it('rolls up to degraded when an indicator is degraded but none error', async () => {
    service.register({
      name: 'db',
      check: () => ({ name: 'db', status: 'ok' }),
    });
    service.register({
      name: 'broker',
      check: () => ({ name: 'broker', status: 'degraded' }),
    });
    const report = await service.readiness();
    expect(report.status).toBe('degraded');
  });

  it('captures thrown indicator errors as an error check', async () => {
    service.register({
      name: 'flaky',
      check: () => {
        throw new Error('connection refused');
      },
    });
    const report = await service.readiness();
    expect(report.status).toBe('error');
    const flaky = report.checks.find((c) => c.name === 'flaky');
    expect(flaky?.detail).toBe('connection refused');
  });
});
