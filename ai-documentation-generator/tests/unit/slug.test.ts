import { describe, expect, it } from 'vitest'
import { slugify } from '@/lib/slug'

describe('slugify', () => {
  it('normalizes titles for URLs', () => {
    expect(slugify('Create a New Project!')).toBe('create-a-new-project')
  })

  it('falls back to untitled for empty values', () => {
    expect(slugify('   !!!   ')).toBe('untitled')
  })

  it('keeps slugs bounded for database and route safety', () => {
    expect(slugify('a'.repeat(120)).length).toBeLessThanOrEqual(72)
  })
})
