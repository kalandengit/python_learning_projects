import { NotFoundError } from '@asa/errors';
import { ExampleService } from './example.service';

describe('ExampleService', () => {
  let service: ExampleService;

  beforeEach(() => {
    service = new ExampleService();
  });

  describe('list', () => {
    it('returns the first page with default sizing', () => {
      const page = service.list({});
      expect(page.page).toBe(1);
      expect(page.total).toBe(3);
      expect(page.items).toHaveLength(3);
      expect(page.totalPages).toBe(1);
    });

    it('clamps oversized page sizes and slices correctly', () => {
      const page = service.list({ page: 1, pageSize: 2 });
      expect(page.items).toHaveLength(2);
      expect(page.items[0].id).toBe('ex-1');
      expect(page.totalPages).toBe(2);
    });

    it('returns the second page', () => {
      const page = service.list({ page: 2, pageSize: 2 });
      expect(page.items).toHaveLength(1);
      expect(page.items[0].id).toBe('ex-3');
    });

    it('normalizes invalid input to safe bounds', () => {
      const page = service.list({ page: -5, pageSize: 0 });
      expect(page.page).toBe(1);
      expect(page.pageSize).toBe(20);
    });
  });

  describe('getById', () => {
    it('returns a matching example', () => {
      expect(service.getById('ex-2').name).toBe('Second example');
    });

    it('throws a NotFoundError for unknown ids', () => {
      expect(() => service.getById('missing')).toThrow(NotFoundError);
    });
  });
});
