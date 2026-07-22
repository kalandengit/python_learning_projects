/** A normalized pagination request. */
export interface PageQuery {
  page: number;
  pageSize: number;
  sort?: string;
}

/** A page of results with total metadata. */
export interface Page<T> {
  items: T[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

export const DEFAULT_PAGE = 1;
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

/**
 * Clamp arbitrary (possibly untrusted) pagination input into safe bounds:
 * page >= 1, 1 <= pageSize <= {@link MAX_PAGE_SIZE}.
 */
export function normalizePageQuery(input: Partial<PageQuery>): PageQuery {
  const rawPage = Math.trunc(Number(input.page)) || DEFAULT_PAGE;
  const rawSize = Math.trunc(Number(input.pageSize)) || DEFAULT_PAGE_SIZE;
  return {
    page: Math.max(1, rawPage),
    pageSize: Math.min(MAX_PAGE_SIZE, Math.max(1, rawSize)),
    sort: input.sort,
  };
}

/** Build a {@link Page} envelope from a slice of items and the total count. */
export function createPage<T>(
  items: T[],
  total: number,
  query: PageQuery,
): Page<T> {
  const totalPages =
    query.pageSize > 0 ? Math.ceil(Math.max(0, total) / query.pageSize) : 0;
  return {
    items,
    page: query.page,
    pageSize: query.pageSize,
    total,
    totalPages,
  };
}
