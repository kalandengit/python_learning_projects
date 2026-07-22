import { MetricsService } from './metrics.service';

describe('MetricsService', () => {
  let service: MetricsService;

  beforeEach(() => {
    service = new MetricsService();
  });

  afterEach(() => {
    service.registry.clear();
  });

  it('renders default process metrics', async () => {
    const output = await service.render();
    expect(output).toContain('process_cpu_user_seconds_total');
  });

  it('records HTTP request count and duration', async () => {
    service.observe('GET', '/api/v1/examples', 200, 0.012);
    const output = await service.render();
    expect(output).toContain('http_requests_total');
    expect(output).toContain('method="GET"');
    expect(output).toContain('status="200"');
    expect(output).toContain('http_request_duration_seconds');
  });

  it('exposes the Prometheus content type', () => {
    expect(service.contentType).toContain('text/plain');
  });
});
