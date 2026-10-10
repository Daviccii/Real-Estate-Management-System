import { beforeEach, describe, expect, it, vi } from 'vitest'

import { authService } from './auth'
import { getToken, setToken } from './token'

const respond = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

/** Queue one fresh Response per fetch call (bodies are single-use). */
const queueFetch = (...bodies: Array<{ status?: number; body: unknown }>) => {
  const calls: string[] = []
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    calls.push(String(input))
    const next = bodies.shift() ?? bodies[0]
    return respond(next.body, next.status ?? 200)
  })
  vi.stubGlobal('fetch', fetchMock)
  return calls
}

describe('authService.login', () => {
  beforeEach(() => {
    setToken(null)
  })

  it('returns the MFA challenge untouched and keeps the user signed out', async () => {
    const challenge = {
      mfa_required: true,
      mfa_setup_required: false,
      mfa_token: 'mfa-abc',
      allowed_methods: ['totp', 'sms', 'recovery'],
    }
    const urls = queueFetch({ body: challenge })

    const result = await authService.login('a@b.com', 'password')

    expect(result).toEqual(challenge)
    expect(getToken()).toBeNull()
    expect(urls).toHaveLength(1)
    expect(urls[0]).toMatch(/\/api\/v1\/auth\/login$/)
  })

  it('stores the access token and returns the session user', async () => {
    const urls = queueFetch({ body: { access_token: 'jwt-1', user: { id: 1, role: 'admin' }, redirect_url: '/admin' } })

    const result = await authService.login('a@b.com', 'password')

    expect(result).toEqual({ user: { id: 1, role: 'admin' }, redirect_url: '/admin' })
    expect(getToken()).toBe('jwt-1')
    expect(urls).toHaveLength(1)
  })

  it('fetches the profile when the login payload omits the user', async () => {
    const urls = queueFetch(
      { body: { access_token: 'jwt-2' } },
      { body: { id: 7, role: 'manager', email: 'a@b.com' } },
    )

    const result: any = await authService.login('a@b.com', 'password')

    expect(result.user.id).toBe(7)
    expect(result.redirect_url).toBe('/app')
    expect(urls[1]).toMatch(/\/api\/v1\/users\/me$/)
  })

  it('fails loudly when the response carries neither a session nor a challenge', async () => {
    queueFetch({ body: { detail: 'bad credentials' }, status: 401 })

    await expect(authService.login('a@b.com', 'wrong')).rejects.toThrow('bad credentials')
    expect(getToken()).toBeNull()
  })
})
