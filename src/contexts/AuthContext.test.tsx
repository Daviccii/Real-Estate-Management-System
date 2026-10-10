import type React from 'react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { act, renderHook } from '@testing-library/react'

import { AuthProvider, getRoleDashboardPath, useAuth } from './AuthContext'
import { authService } from '../services/auth'
import type { User } from '../types'

vi.mock('../services/auth', () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
    refresh: vi.fn(),
    logout: vi.fn(),
  },
}))

const user = (overrides: Partial<User> = {}) =>
  ({ id: 1, email: 'a@b.com', role: 'manager', full_name: 'Ada', ...overrides }) as User

const session = (as: User) => ({ user: as, redirect_url: '/app' })

const wrapper = ({ children }: { children: React.ReactNode }) => <AuthProvider>{children}</AuthProvider>

describe('getRoleDashboardPath', () => {
  it('maps every backend role to its own portal', () => {
    expect(getRoleDashboardPath('admin')).toBe('/admin/dashboard')
    expect(getRoleDashboardPath('MANAGER')).toBe('/manager/dashboard')
    expect(getRoleDashboardPath('landlord')).toBe('/owner/dashboard')
    expect(getRoleDashboardPath('realtor')).toBe('/agent/dashboard')
    expect(getRoleDashboardPath('resident')).toBe('/tenant/dashboard')
    expect(getRoleDashboardPath('vendor')).toBe('/provider/dashboard')
    expect(getRoleDashboardPath('user')).toBe('/tenant/dashboard')
    expect(getRoleDashboardPath(undefined)).toBe('/tenant/dashboard')
  })
})

describe('AuthProvider', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/')
    vi.mocked(authService.refresh).mockResolvedValue(null as any)
    vi.mocked(authService.logout).mockResolvedValue(undefined)
  })

  it('does not probe the session on public routes', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    await vi.waitFor(() => expect(result.current.loading).toBe(false))
    expect(authService.refresh).not.toHaveBeenCalled()
    expect(result.current.user).toBeNull()
  })

  it('restores the session on a protected route', async () => {
    window.history.pushState({}, '', '/admin/dashboard')
    vi.mocked(authService.refresh).mockResolvedValue(user({ role: 'admin' }))

    const { result } = renderHook(() => useAuth(), { wrapper })

    await vi.waitFor(() => expect(result.current.user?.role).toBe('admin'))
    expect(authService.refresh).toHaveBeenCalled()
  })

  it('keeps loading true until the refresh settles', async () => {
    window.history.pushState({}, '', '/manager')
    let release: (value: User) => void = () => {}
    vi.mocked(authService.refresh).mockImplementation(() => new Promise<User>((resolve) => { release = resolve }))

    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.loading).toBe(true)

    await act(async () => { release(user()) })
    await vi.waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.user?.role).toBe('manager')
  })

  it('stores the user from a plain login but not from an MFA challenge', async () => {
    vi.mocked(authService.login).mockResolvedValue(session(user({ role: 'owner' })))
    const { result } = renderHook(() => useAuth(), { wrapper })

    await act(async () => { await result.current.login('a@b.com', 'secret') })
    expect(result.current.user?.role).toBe('owner')

    vi.mocked(authService.login).mockResolvedValue({
      mfa_required: true,
      mfa_setup_required: false,
      mfa_token: 'mfa-1',
      allowed_methods: ['totp'],
    })
    await act(async () => { await result.current.login('a@b.com', 'secret') })
    expect(result.current.user?.role).toBe('owner')
  })

  it('clears the user on logout even though auth state is local', async () => {
    vi.mocked(authService.login).mockResolvedValue(session(user()))
    const { result } = renderHook(() => useAuth(), { wrapper })
    await act(async () => { await result.current.login('a@b.com', 'secret') })

    await act(async () => {
      result.current.logout()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(authService.logout).toHaveBeenCalled()
    expect(result.current.user).toBeNull()
  })

  it('treats admin as holding every role and honours roles_csv', async () => {
    vi.mocked(authService.login).mockResolvedValue(session(user({ role: 'admin' })))
    const admin = renderHook(() => useAuth(), { wrapper })
    await act(async () => { await admin.result.current.login('a@b.com', 'secret') })

    expect(admin.result.current.hasRole('owner')).toBe(true)
    expect(admin.result.current.hasAnyRole(['tenant'])).toBe(true)
    admin.unmount()

    vi.mocked(authService.login).mockResolvedValue(
      session(user({ role: 'agent', roles_csv: 'agent, owner' })),
    )
    const agent = renderHook(() => useAuth(), { wrapper })
    await act(async () => { await agent.result.current.login('a@b.com', 'secret') })

    expect(agent.result.current.hasRole('owner')).toBe(true)
    expect(agent.result.current.hasRole('tenant')).toBe(false)
    expect(agent.result.current.hasAnyRole(['tenant', 'owner'])).toBe(true)
  })

  it('sends visitors without a session to sign-in', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    await vi.waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.getDashboardPath()).toBe('/login')

    vi.mocked(authService.login).mockResolvedValue(session(user({ role: 'service_provider' })))
    await act(async () => { await result.current.login('a@b.com', 'secret') })
    expect(result.current.getDashboardPath()).toBe('/provider/dashboard')
  })

  it('registers through the auth service', async () => {
    vi.mocked(authService.register).mockResolvedValue(undefined)
    const { result } = renderHook(() => useAuth(), { wrapper })

    await act(async () => { await result.current.register('a@b.com', 'secret', 'Ada') })

    expect(authService.register).toHaveBeenCalledWith('a@b.com', 'secret', 'Ada')
    expect(result.current.loading).toBe(false)
  })
})
