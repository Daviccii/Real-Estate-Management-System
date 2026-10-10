import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

// Node 24 exposes a `localStorage` global that shadows jsdom's and is undefined
// unless started with --localstorage-file, so reach through window explicitly.
const clearStorage = () => {
  const store = globalThis.window as unknown as { localStorage?: Storage; sessionStorage?: Storage }
  store?.localStorage?.clear()
  store?.sessionStorage?.clear()
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
  clearStorage()
})
