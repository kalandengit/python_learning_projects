/**
 * Minimal policy expectations used by CI to prevent accidental removal of
 * security headers from next.config.ts. Keep this in sync with the production
 * header configuration.
 */
export const requiredSecurityHeaders = [
  'Content-Security-Policy',
  'X-Frame-Options',
  'X-Content-Type-Options',
  'Referrer-Policy',
  'Permissions-Policy'
] as const

export type RequiredSecurityHeader = (typeof requiredSecurityHeaders)[number]
