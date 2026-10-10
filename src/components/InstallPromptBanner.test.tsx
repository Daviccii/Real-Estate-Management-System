import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import InstallPromptBanner from './InstallPromptBanner'
import { INSTALL_PROMPT_DISMISSED_KEY } from '../hooks/useInstallPrompt'
import { LANGUAGE_STORAGE_KEY, LanguageProvider } from '../i18n/LanguageContext'

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

type PromptEvent = Event & {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const makePromptEvent = (outcome: 'accepted' | 'dismissed' = 'accepted'): PromptEvent => {
  const event = new Event('beforeinstallprompt') as PromptEvent
  Object.assign(event, {
    prompt: () => Promise.resolve(),
    userChoice: Promise.resolve({ outcome }),
  })
  return event
}

const originalUserAgent = window.navigator.userAgent

const setUserAgent = (userAgent: string) => {
  Object.defineProperty(window.navigator, 'userAgent', { configurable: true, value: userAgent })
}

const renderBanner = () =>
  render(
    <LanguageProvider>
      <InstallPromptBanner />
    </LanguageProvider>,
  )

beforeEach(() => {
  Object.defineProperty(window, 'localStorage', { value: createStorageMock(), configurable: true })
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    writable: true,
    value: (query: string) => ({ matches: false, media: query }),
  })
})

afterEach(() => {
  setUserAgent(originalUserAgent)
})

describe('InstallPromptBanner', () => {
  it('stays hidden until the browser offers an install', () => {
    const { container } = renderBanner()
    expect(container).toBeEmptyDOMElement()
  })

  it('appears with the English copy once beforeinstallprompt fires', () => {
    renderBanner()
    act(() => {
      window.dispatchEvent(makePromptEvent())
    })

    const banner = screen.getByRole('complementary', { name: 'Install PropNoxa' })
    expect(banner).toBeInTheDocument()
    expect(screen.getByText(/Add PropNoxa to your home screen/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Install' })).toBeInTheDocument()
  })

  it('renders in Kiswahili when that is the active language', () => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, 'sw')
    renderBanner()
    act(() => {
      window.dispatchEvent(makePromptEvent())
    })

    expect(screen.getByRole('complementary', { name: 'Sakinisha PropNoxa' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sakinisha' })).toBeInTheDocument()
  })

  it('invokes the native prompt and disappears once the choice is made', async () => {
    renderBanner()
    act(() => {
      window.dispatchEvent(makePromptEvent('accepted'))
    })

    await userEvent.click(screen.getByRole('button', { name: 'Install' }))

    await waitFor(() => expect(screen.queryByRole('complementary')).not.toBeInTheDocument())
  })

  it('dismiss persists so the banner stays gone on the next visit', async () => {
    const first = renderBanner()
    act(() => {
      window.dispatchEvent(makePromptEvent())
    })
    await userEvent.click(screen.getByRole('button', { name: 'Dismiss install suggestion' }))

    expect(screen.queryByRole('complementary')).not.toBeInTheDocument()
    expect(window.localStorage.getItem(INSTALL_PROMPT_DISMISSED_KEY)).toBe('1')

    first.unmount()
    renderBanner()
    act(() => {
      window.dispatchEvent(makePromptEvent())
    })
    expect(screen.queryByRole('complementary')).not.toBeInTheDocument()
  })

  it('shows manual Safari instructions on iOS instead of an Install button', () => {
    setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15')
    renderBanner()

    expect(screen.getByText(/Add to Home Screen/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Install' })).not.toBeInTheDocument()
  })

  it('renders nothing on iOS when already installed to the home screen', () => {
    setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15')
    Object.defineProperty(window, 'matchMedia', {
      configurable: true,
      writable: true,
      value: (query: string) => ({ matches: true, media: query }),
    })
    const { container } = renderBanner()
    expect(container).toBeEmptyDOMElement()
  })
})
