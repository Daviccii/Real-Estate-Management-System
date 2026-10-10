import { beforeEach, describe, expect, it, vi } from 'vitest'

import { isMfaChallenge, mfaService } from './mfa'
import { getToken, setToken } from './token'

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

const lastCall = (fetchMock: ReturnType<typeof vi.fn>) => {
  const [url, init] = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]
  const options = init as RequestInit
  return {
    url: url as string,
    init: options,
    headers: new Headers(options.headers as Record<string, string>),
    body: options.body ? JSON.parse(String(options.body)) : null,
  }
}

describe('isMfaChallenge', () => {
  it('only accepts a payload that carries both flags of a challenge', () => {
    expect(isMfaChallenge({ mfa_required: true, mfa_token: 'abc' })).toBe(true)
    expect(isMfaChallenge({ mfa_required: true })).toBe(false)
    expect(isMfaChallenge({ mfa_token: 'abc' })).toBe(false)
    expect(isMfaChallenge({ access_token: 'jwt', user: {} as any })).toBe(false)
    expect(isMfaChallenge(null)).toBe(false)
  })
})

describe('mfaService', () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    setToken(null)
    fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
  })

  it('exchanges the challenge token for a session and stores the access token', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ access_token: 'jwt-session', token_type: 'bearer' }))

    const data = await mfaService.verify('mfa-token', 'totp', '123456')

    const call = lastCall(fetchMock)
    expect(call.url).toMatch(/\/api\/v1\/auth\/mfa\/verify$/)
    expect(call.body).toEqual({ mfa_token: 'mfa-token', method: 'totp', code: '123456' })
    expect(data?.access_token).toBe('jwt-session')
    expect(getToken()).toBe('jwt-session')
  })

  it('does not overwrite the stored token when verification fails', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'Invalid or expired MFA token' }, 401))

    await expect(mfaService.verify('mfa-token', 'sms', '000000')).rejects.toThrow(/Invalid or expired/)
    expect(getToken()).toBeNull()
  })

  it('requests an SMS code against the challenge token', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ message: 'SMS code sent', dev_code: '246810' }))

    const result = await mfaService.sendSms('mfa-token')

    expect(lastCall(fetchMock).url).toMatch(/\/auth\/mfa\/send-sms$/)
    expect(result.dev_code).toBe('246810')
  })

  it('reads MFA status with the bearer session', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ mfa_enabled: true, has_secret: true, sms_available: false, recovery_codes_remaining: 8, mandatory_for_admin: false }),
    )
    setToken('jwt-session')

    const status = await mfaService.status()

    const call = lastCall(fetchMock)
    expect(call.url).toMatch(/\/api\/v1\/auth\/mfa\/status$/)
    expect(call.init.method ?? 'GET').toBe('GET')
    expect(call.headers.get('Authorization')).toBe('Bearer jwt-session')
    expect(status.recovery_codes_remaining).toBe(8)
  })

  it('sends a null mfa_token for enrolment done from an authenticated session', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ message: 'MFA enabled', recovery_codes: ['r1'], warning: '' }))

    await mfaService.enable('123456')

    expect(lastCall(fetchMock).url).toMatch(/\/api\/v1\/auth\/mfa\/enable$/)
    expect(lastCall(fetchMock).body).toEqual({ code: '123456', mfa_token: null })
  })

  it('regenerates recovery codes with the current TOTP code', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ recovery_codes: ['a1', 'b2'], warning: 'old codes invalid' }))

    const result = await mfaService.regenerateRecoveryCodes('654321')

    expect(lastCall(fetchMock).url).toMatch(/\/auth\/mfa\/recovery-codes\/regenerate$/)
    expect(lastCall(fetchMock).body).toEqual({ code: '654321' })
    expect(result.recovery_codes).toEqual(['a1', 'b2'])
  })
})
