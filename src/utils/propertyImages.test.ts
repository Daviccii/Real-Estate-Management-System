import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { Property } from '../types'
import { placeholderPropertyImage, resolvePropertyImage } from './propertyImages'

const property = (overrides: Partial<Property> = {}) =>
  ({ id: 42, name: 'Test listing', property_type: 'Apartment', purpose: 'rent', ...overrides }) as Property

const pexelsResponse = (url: string) =>
  new Response(JSON.stringify({ photos: [{ src: { large: url } }] }), { status: 200 })

describe('propertyImages', () => {
  beforeEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  it('returns a deterministic picsum placeholder', () => {
    expect(placeholderPropertyImage(property({ id: 7 }))).toContain('picsum.photos/seed/propnoxa-7')
  })

  it('prefers an explicit image_url over anything else', async () => {
    const url = await resolvePropertyImage(property({ image_url: 'https://cdn.test/real.jpg' }))
    expect(url).toBe('https://cdn.test/real.jpg')
  })

  it('reuses the session cache without hitting the network', async () => {
    sessionStorage.setItem('pn-image-cache:42', 'https://cached.test/photo.jpg')
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    const url = await resolvePropertyImage(property())
    expect(url).toBe('https://cached.test/photo.jpg')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('falls back to picsum when no Pexels key is configured', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    vi.stubEnv('VITE_PEXELS_API_KEY', '')

    const mod = await import('./propertyImages')
    const url = await mod.resolvePropertyImage(property({ id: 9 }))
    expect(url).toContain('picsum.photos/seed/propnoxa-9')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('queries Pexels with a type-aware search and caches the result', async () => {
    vi.stubEnv('VITE_PEXELS_API_KEY', 'pexels-key')
    const fetchMock = vi.fn().mockResolvedValue(pexelsResponse('https://pexels.test/villa.jpg'))
    vi.stubGlobal('fetch', fetchMock)

    const mod = await import('./propertyImages')
    const url = await mod.resolvePropertyImage(property({ id: 3, property_type: 'Villa', purpose: 'sale' }))

    expect(url).toBe('https://pexels.test/villa.jpg')
    const [calledUrl, options] = fetchMock.mock.calls[0]
    expect(decodeURIComponent(calledUrl as string)).toContain('luxury villa exterior')
    expect((options as RequestInit).headers).toEqual({ Authorization: 'pexels-key' })
    expect(sessionStorage.getItem('pn-image-cache:3')).toBe('https://pexels.test/villa.jpg')
  })

  it('never throws: network and API failures degrade to the placeholder', async () => {
    vi.stubEnv('VITE_PEXELS_API_KEY', 'pexels-key')

    const mod = await import('./propertyImages')

    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))
    expect(await mod.resolvePropertyImage(property({ id: 11 }))).toContain('seed/propnoxa-11')

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 500 })))
    expect(await mod.resolvePropertyImage(property({ id: 12 }))).toContain('seed/propnoxa-12')

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ photos: [] }), { status: 200 })))
    expect(await mod.resolvePropertyImage(property({ id: 13 }))).toContain('seed/propnoxa-13')
  })
})
