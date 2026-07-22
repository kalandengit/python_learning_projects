import { describe, it, expect } from 'vitest';
import {
  createPage,
  normalizePageQuery,
  MAX_PAGE_SIZE,
  DEFAULT_PAGE,
  DEFAULT_PAGE_SIZE,
} from './pagination';

describe('normalizePageQuery', () => {
  it('applies defaults for missing input', () => {
    expect(normalizePageQuery({})).toEqual({
      page: DEFAULT_PAGE,
      pageSize: DEFAULT_PAGE_SIZE,
      sort: undefined,
    });
  });

  it('clamps page to >= 1 and pageSize to [1, MAX]', () => {
    expect(normalizePageQuery({ page: -5, pageSize: 0 }).page).toBe(1);
    expect(normalizePageQuery({ page: 0, pageSize: 0 }).pageSize).toBe(
      DEFAULT_PAGE_SIZE,
    );
    expect(normalizePageQuery({ pageSize: 9999 }).pageSize).toBe(MAX_PAGE_SIZE);
  });

  it('coerces non-numeric input safely', () => {
    const q = normalizePageQuery({
      page: 'abc' as unknown as number,
      pageSize: 'x' as unknown as number,
    });
    expect(q.page).toBe(DEFAULT_PAGE);
    expect(q.pageSize).toBe(DEFAULT_PAGE_SIZE);
  });
});

describe('createPage', () => {
  it('computes totalPages by ceiling', () => {
    const page = createPage([1, 2], 5, { page: 1, pageSize: 2 });
    expect(page).toEqual({
      items: [1, 2],
      page: 1,
      pageSize: 2,
      total: 5,
      totalPages: 3,
    });
  });

  it('handles an empty result set', () => {
    const page = createPage([], 0, { page: 1, pageSize: 20 });
    expect(page.total).toBe(0);
    expect(page.totalPages).toBe(0);
  });
});
