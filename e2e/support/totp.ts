import { createHmac } from 'node:crypto'

const BASE32 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'

/** RFC 6238 TOTP, matching backend/app/utils/totp.py. Used only by e2e tests. */
export function totpCode(secret: string, digits = 6, periodSeconds = 30, now = Date.now()): string {
  const normalized = secret.replace(/[\s=]/g, '').toUpperCase()
  let bits = ''
  for (const character of normalized) {
    const index = BASE32.indexOf(character)
    if (index < 0) throw new Error(`Invalid base32 character: ${character}`)
    bits += index.toString(2).padStart(5, '0')
  }

  const key = Buffer.alloc(Math.floor(bits.length / 8))
  for (let index = 0; index < key.length; index += 1) {
    key[index] = parseInt(bits.slice(index * 8, index * 8 + 8), 2)
  }

  const counter = Buffer.alloc(8)
  counter.writeBigUInt64BE(BigInt(Math.floor(now / 1000 / periodSeconds)))

  const digest = createHmac('sha1', key).update(counter).digest()
  const offset = digest[digest.length - 1] & 0x0f
  const binary =
    ((digest[offset] & 0x7f) << 24) |
    (digest[offset + 1] << 16) |
    (digest[offset + 2] << 8) |
    digest[offset + 3]

  return String(binary % 10 ** digits).padStart(digits, '0')
}
