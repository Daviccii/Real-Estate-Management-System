import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api, ApiError } from './api'
import { setToken } from './token'

const jsonResponse = (body: unknown, status = 200) =>
  new Response(typeof body === 'string' ? body : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })

describe('api.request', () => {
  beforeEach(() => {
    setToken(null)
  })

  it('puts every caller onto the versioned prefix', async () => {
    // A Response body can only be read once, so hand back a fresh one per call.
    const fetchMock = vi.fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>(
      async () => jsonResponse({ ok: true }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await api.request('/properties/')
    await api.request('units')
    await api.request('/api/agent/workspace')
    await api.request('/api/v1/auth/login', { method: 'POST' })
    await api.request('http://other.host/health')

    const urls = fetchMock.mock.calls.map((call) => call[0] as string)
    expect(urls[0]).toMatch(/\/api\/v1\/properties\/$/)
    expect(urls[1]).toMatch(/\/api\/v1\/units$/)
    expect(urls[2]).toMatch(/\/api\/v1\/agent\/workspace$/)
    expect(urls[3]).toMatch(/\/api\/v1\/auth\/login$/)
    expect(urls[4]).toBe('http://other.host/health')
  })

  it('attaches the bearer token and cookie credentials', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse([]))
    vi.stubGlobal('fetch', fetchMock)
    setToken('abc123')

    await api.request('/properties/')

    const [, options] = fetchMock.mock.calls[0]
    expect((options.headers as Headers).get('Authorization')).toBe('Bearer abc123')
    expect(options.credentials).toBe('include')
  })

  it('turns FastAPI 422 detail arrays into a readable message', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      jsonResponse({ detail: [{ loc: ['body', 'email'], msg: 'value is not a valid email', type: 'value_error' }] }, 422)
    ))

    await expect(api.request('/auth/register')).rejects.toThrow('value is not a valid email')
  })

  it('joins several validation errors instead of showing [object Object]', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      jsonResponse({ detail: [{ msg: 'name required' }, { msg: 'price invalid' }] }, 422)
    ))

    await expect(api.request('/properties/')).rejects.toThrow('name required; price invalid')
  })

  it('keeps a plain string detail', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ detail: 'Email already registered' }, 400)))
    await expect(api.request('/auth/register')).rejects.toThrow('Email already registered')
  })

  it('hides internals behind a generic message for 5xx responses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ detail: 'psycopg connection refused' }, 500)))
    await expect(api.request('/properties/')).rejects.toThrow(/temporarily unavailable/)
  })

  it('reports an unreachable backend rather than a raw TypeError', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    await expect(api.request('/properties/')).rejects.toThrow(/cannot be reached/)
  })

  it('exposes the status code and payload on ApiError', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ detail: 'nope' }, 403)))
    const error = await api.request('/admin/settings').catch((err) => err as ApiError)
    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(403)
    expect(error.data).toEqual({ detail: 'nope' })
  })

  it('returns null for an empty 204-style body', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })))
    await expect(api.request('/properties/1', { method: 'DELETE' })).resolves.toBeNull()
  })
})
