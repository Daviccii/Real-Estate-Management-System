import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  applyThemeToDocument,
  resolveTheme,
  ThemeProvider,
  THEME_STORAGE_KEY,
  useTheme,
} from './ThemeContext'

// Node 24's bare localStorage global shadows jsdom's and is undefined under
// vitest, so install a fresh in-memory implementation before each test.
const createStorageMock = (): Storage => {
  const map = new Map<string, string>()
  return {
    get length() {
      return map.size
    },
    clear: () => map.clear(),
    getItem: (key: string) => map.get(key) ?? null,
    key: (index: number) => [...map.keys()][index] ?? null,
    removeItem: (key: string) => map.delete(key),
    setItem: (key: string, value: string) => map.set(key, value),
  }
}

type MediaListener = (event: { matches: boolean }) => void

// Plain closures instead of vi.fn() because setup.ts restores mocks after
// every test, which would strip a vi.fn's implementation.
const installMatchMedia = (initialMatches: boolean) => {
  const listeners = new Set<MediaListener>()
  const state = { matches: initialMatches }
  const mediaQueryList = {
    get matches() {
      return state.matches
    },
    media: '(prefers-color-scheme: dark)',
    onchange: null,
    addEventListener: (_type: string, listener: MediaListener) => listeners.add(listener),
    removeEventListener: (_type: string, listener: MediaListener) => listeners.delete(listener),
    addListener: (listener: MediaListener) => listeners.add(listener),
    removeListener: (listener: MediaListener) => listeners.delete(listener),
    dispatchEvent: () => true,
  }
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    writable: true,
    value: () => mediaQueryList,
  })
  return {
    setMatches: (matches: boolean) => {
      state.matches = matches
      listeners.forEach((listener) => listener({ matches }))
    },
    listenerCount: () => listeners.size,
  }
}

const Probe = () => {
  const { preference, theme, setPreference } = useTheme()
  return (
    <>
      <span data-testid="preference">{preference}</span>
      <span data-testid="theme">{theme}</span>
      <button onClick={() => setPreference('light')}>set-light</button>
      <button onClick={() => setPreference('dark')}>set-dark</button>
      <button onClick={() => setPreference('system')}>set-system</button>
    </>
  )
}

const renderProvider = () =>
  render(
    <ThemeProvider>
      <Probe />
    </ThemeProvider>,
  )

beforeEach(() => {
  Object.defineProperty(window, 'localStorage', { value: createStorageMock(), configurable: true })
  document.documentElement.removeAttribute('data-theme')
})

describe('ThemeProvider', () => {
  it('defaults to the system preference when nothing is stored', () => {
    installMatchMedia(true)
    renderProvider()

    expect(screen.getByTestId('preference')).toHaveTextContent('system')
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('resolves to light when the OS has no dark preference', () => {
    installMatchMedia(false)
    renderProvider()

    expect(screen.getByTestId('theme')).toHaveTextContent('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('restores a stored explicit preference over the OS setting', () => {
    installMatchMedia(false)
    window.localStorage.setItem(THEME_STORAGE_KEY, 'dark')
    renderProvider()

    expect(screen.getByTestId('preference')).toHaveTextContent('dark')
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('ignores invalid stored values and falls back to system', () => {
    installMatchMedia(true)
    window.localStorage.setItem(THEME_STORAGE_KEY, 'banana')
    renderProvider()

    expect(screen.getByTestId('preference')).toHaveTextContent('system')
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
  })

  it('persists explicit choices and applies them immediately', async () => {
    installMatchMedia(true)
    renderProvider()

    await userEvent.click(screen.getByRole('button', { name: 'set-light' }))

    expect(screen.getByTestId('theme')).toHaveTextContent('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('light')
  })

  it('follows OS changes while in system mode only', async () => {
    const media = installMatchMedia(false)
    renderProvider()

    act(() => media.setMatches(true))
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
    expect(media.listenerCount()).toBe(1)

    await userEvent.click(screen.getByRole('button', { name: 'set-light' }))
    expect(media.listenerCount()).toBe(0)

    act(() => media.setMatches(false))
    act(() => media.setMatches(true))
    expect(screen.getByTestId('theme')).toHaveTextContent('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('re-subscribes when switching back to system mode', async () => {
    const media = installMatchMedia(false)
    renderProvider()

    await userEvent.click(screen.getByRole('button', { name: 'set-dark' }))
    expect(media.listenerCount()).toBe(0)

    await userEvent.click(screen.getByRole('button', { name: 'set-system' }))
    expect(media.listenerCount()).toBe(1)
    expect(screen.getByTestId('theme')).toHaveTextContent('light')
  })

  it('survives environments without matchMedia', () => {
    Object.defineProperty(window, 'matchMedia', { configurable: true, writable: true, value: undefined })
    renderProvider()

    expect(screen.getByTestId('preference')).toHaveTextContent('system')
    expect(screen.getByTestId('theme')).toHaveTextContent('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('survives storage access errors and still applies in-memory choices', async () => {
    installMatchMedia(false)
    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      value: {
        ...createStorageMock(),
        getItem: () => {
          throw new Error('denied')
        },
        setItem: () => {
          throw new Error('denied')
        },
      },
    })
    renderProvider()

    expect(screen.getByTestId('preference')).toHaveTextContent('system')

    await userEvent.click(screen.getByRole('button', { name: 'set-dark' }))
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('throws when useTheme is called outside the provider', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<Probe />)).toThrow('useTheme must be used within ThemeProvider')
    consoleError.mockRestore()
  })
})

describe('theme helpers', () => {
  it('resolveTheme maps explicit preferences directly', () => {
    installMatchMedia(true)
    expect(resolveTheme('light')).toBe('light')
    expect(resolveTheme('dark')).toBe('dark')
    expect(resolveTheme('system')).toBe('dark')
  })

  it('applyThemeToDocument writes the data-theme attribute', () => {
    applyThemeToDocument('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    applyThemeToDocument('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })
})
