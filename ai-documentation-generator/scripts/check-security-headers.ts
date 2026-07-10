import fs from 'node:fs'
import path from 'node:path'
import { requiredSecurityHeaders } from '../lib/security/headers'

const configPath = path.join(process.cwd(), 'next.config.ts')
const source = fs.readFileSync(configPath, 'utf8')
const missing = requiredSecurityHeaders.filter((header) => !source.includes(header))

if (missing.length > 0) {
  console.error(`Missing required security headers: ${missing.join(', ')}`)
  process.exit(1)
}

console.log(`Security header check passed: ${requiredSecurityHeaders.join(', ')}`)
