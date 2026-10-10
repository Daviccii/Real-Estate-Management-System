import type React from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { act, renderHook } from '@testing-library/react'

import { FavoriteProvider, useFavorites } from './FavoriteContext'
import { useAuth } from './AuthContext'
import { favoriteService } from '../services/favorite'

vi.mock('./AuthContext')
vi.mock('../services/favorite')

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <FavoriteProvider>{children}</FavoriteProvider>
)

describe('FavoriteContext', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.mocked(useAuth).mockReturnValue({ user: { id: 1, email: 'a@b.com', role: 'tenant' } } as any)
    vi.mocked(favoriteService.list).mockResolvedValue([
      { id: 1, property_id: 10 },
      { id: 2, property_id: 22 },
    ] as any)
    vi.mocked(favoriteService.add).mockResolvedValue({} as any)
    vi.mocked(favoriteService.remove).mockResolvedValue({} as any)
  })

  it('loads the saved property ids for a signed-in visitor', async () => {
    const { result } = renderHook(() => useFavorites(), { wrapper })

    await act(async () => { await Promise.resolve() })

    expect(result.current.favorites).toEqual([10, 22])
    expect(result.current.isFavorite(22)).toBe(true)
    expect(result.current.isFavorite(7)).toBe(false)
    expect(result.current.loading).toBe(false)
  })

  it('skips the API entirely when nobody is signed in', async () => {
    vi.mocked(useAuth).mockReturnValue({ user: null } as any)
    const { result } = renderHook(() => useFavorites(), { wrapper })

    await act(async () => { await Promise.resolve() })

    expect(favoriteService.list).not.toHaveBeenCalled()
    expect(result.current.favorites).toEqual([])
  })

  it('adds a favourite locally once the server accepts it', async () => {
    const { result } = renderHook(() => useFavorites(), { wrapper })
    await act(async () => { await Promise.resolve() })

    await act(async () => { await result.current.addFavorite(31) })

    expect(favoriteService.add).toHaveBeenCalledWith(31)
    expect(result.current.isFavorite(31)).toBe(true)
  })

  it('refuses to add without a session', async () => {
    vi.mocked(useAuth).mockReturnValue({ user: null } as any)
    const { result } = renderHook(() => useFavorites(), { wrapper })
    await act(async () => { await Promise.resolve() })

    await expect(result.current.addFavorite(5)).rejects.toThrow('User not authenticated')
    expect(favoriteService.add).not.toHaveBeenCalled()
  })

  it('drops a favourite once the server confirms removal', async () => {
    const { result } = renderHook(() => useFavorites(), { wrapper })
    await act(async () => { await Promise.resolve() })

    await act(async () => { await result.current.removeFavorite(10) })

    expect(result.current.favorites).toEqual([22])
  })

  it('propagates a failed write so the caller can show the error', async () => {
    vi.mocked(favoriteService.remove).mockRejectedValue(new Error('not found'))
    const { result } = renderHook(() => useFavorites(), { wrapper })
    await act(async () => { await Promise.resolve() })

    await expect(result.current.removeFavorite(10)).rejects.toThrow('not found')
    expect(result.current.favorites).toEqual([10, 22])
  })

  it('keeps the previous list when a refresh fails', async () => {
    const { result } = renderHook(() => useFavorites(), { wrapper })
    await act(async () => { await Promise.resolve() })

    vi.mocked(favoriteService.list).mockRejectedValue(new Error('offline'))
    await act(async () => { await result.current.refreshFavorites() })

    expect(result.current.favorites).toEqual([10, 22])
    expect(result.current.loading).toBe(false)
  })
})
