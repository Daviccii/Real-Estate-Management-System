import { afterEach, describe, expect, it, vi } from 'vitest'

import { registerServiceWorker } from './registerServiceWorker'

interface ServiceWorkerStub {
  getRegistrations?: () => Promise<{ unregister: () => void }[]>
  register?: (url: string) => Promise<unknown>
}

const installServiceWorker = (stub: ServiceWorkerStub) => {
  Object.defineProperty(window.navigator, 'serviceWorker', {
    configurable: true,
    value: {
      getRegistrations: stub.getRegistrations ?? (() => Promise.resolve([])),
      register: stub.register ?? (() => Promise.resolve({})),
    },
  })
}

afterEach(() => {
  delete (window.navigator as { serviceWorker?: unknown }).serviceWorker
})

describe('registerServiceWorker', () => {
  it('does nothing in browsers without service worker support', () => {
    expect('serviceWorker' in navigator).toBe(false)
    expect(() => registerServiceWorker(true)).not.toThrow()
    expect(() => registerServiceWorker(false)).not.toThrow()
  })

  it('unregisters stale workers in development so dev never serves cached assets', async () => {
    const unregistered: number[] = []
    installServiceWorker({
      getRegistrations: () =>
        Promise.resolve([
          { unregister: () => unregistered.push(1) },
          { unregister: () => unregistered.push(2) },
        ]),
    })

    registerServiceWorker(false)

    await vi.waitFor(() => expect(unregistered).toEqual([1, 2]))
  })

  it('waits for the window load event before registering in production', async () => {
    const registered: string[] = []
    installServiceWorker({
      register: (url) => {
        registered.push(url)
        return Promise.resolve({})
      },
    })

    registerServiceWorker(true)
    expect(registered).toEqual([])

    window.dispatchEvent(new Event('load'))
    await vi.waitFor(() => expect(registered).toEqual(['/sw.js']))
  })
})
