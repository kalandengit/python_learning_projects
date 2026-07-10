import { describe, expect, it } from 'vitest'
import { requiredSecurityHeaders } from '@/lib/security/headers'

describe('requiredSecurityHeaders', () => {
  it('requires baseline browser hardening headers', () => {
    expect(requiredSecurityHeaders).toEqual(
      expect.arrayContaining([
        'Content-Security-Policy',
        'X-Frame-Options',
        'X-Content-Type-Options',
        'Referrer-Policy',
        'Permissions-Policy'
      ])
    )
  })
})
