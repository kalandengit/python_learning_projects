import { Injectable } from '@nestjs/common';
import {
  type Page,
  type PageQuery,
  createPage,
  normalizePageQuery,
} from '@asa/contracts';
import { NotFoundError } from '@asa/errors';
import type { Example } from './example.model';

/**
 * In-memory example store. Stands in for a repository-backed service so the
 * template demonstrates pagination and problem+json error mapping without a
 * database dependency. Replace with a real persistence adapter per feature.
 */
@Injectable()
export class ExampleService {
  private readonly items: Example[] = [
    {
      id: 'ex-1',
      name: 'First example',
      createdAt: '2024-01-01T00:00:00.000Z',
    },
    {
      id: 'ex-2',
      name: 'Second example',
      createdAt: '2024-01-02T00:00:00.000Z',
    },
    {
      id: 'ex-3',
      name: 'Third example',
      createdAt: '2024-01-03T00:00:00.000Z',
    },
  ];

  list(query: Partial<PageQuery>): Page<Example> {
    const normalized = normalizePageQuery(query);
    const start = (normalized.page - 1) * normalized.pageSize;
    const slice = this.items.slice(start, start + normalized.pageSize);
    return createPage(slice, this.items.length, normalized);
  }

  getById(id: string): Example {
    const found = this.items.find((item) => item.id === id);
    if (!found) {
      throw new NotFoundError(`Example "${id}" was not found.`);
    }
    return found;
  }
}
