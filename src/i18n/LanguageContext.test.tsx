import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  applyLanguageToDocument,
  interpolate,
  LanguageProvider,
  LANGUAGE_STORAGE_KEY,
  translate,
  useLanguage,
} from './LanguageContext'
import { translations } from './translations'

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

const Probe = () => {
  const { language, setLanguage, t } = useLanguage()
  return (
    <>
      <span data-testid="language">{language}</span>
      <span data-testid="logout">{t('common.logout')}</span>
      <span data-testid="live">{t('home.hero.liveListings', { count: 7 })}</span>
      <button onClick={() => setLanguage('sw')}>set-sw</button>
      <button onClick={() => setLanguage('en')}>set-en</button>
    </>
  )
}

const renderProvider = () =>
  render(
    <LanguageProvider>
      <Probe />
    </LanguageProvider>,
  )

beforeEach(() => {
  Object.defineProperty(window, 'localStorage', { value: createStorageMock(), configurable: true })
  document.documentElement.removeAttribute('lang')
})

describe('LanguageProvider', () => {
  it('defaults to English when nothing is stored', () => {
    renderProvider()

    expect(screen.getByTestId('language')).toHaveTextContent('en')
    expect(screen.getByTestId('logout')).toHaveTextContent('Logout')
    expect(document.documentElement.getAttribute('lang')).toBe('en')
  })

  it('restores a stored Swahili preference', () => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, 'sw')
    renderProvider()

    expect(screen.getByTestId('language')).toHaveTextContent('sw')
    expect(screen.getByTestId('logout')).toHaveTextContent(translations.sw['common.logout'])
    expect(document.documentElement.getAttribute('lang')).toBe('sw')
  })

  it('ignores invalid stored values and falls back to English', () => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, 'fr')
    renderProvider()

    expect(screen.getByTestId('language')).toHaveTextContent('en')
    expect(document.documentElement.getAttribute('lang')).toBe('en')
  })

  it('persists explicit choices and applies them immediately', async () => {
    renderProvider()

    await userEvent.click(screen.getByRole('button', { name: 'set-sw' }))

    expect(screen.getByTestId('language')).toHaveTextContent('sw')
    expect(document.documentElement.getAttribute('lang')).toBe('sw')
    expect(window.localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe('sw')

    await userEvent.click(screen.getByRole('button', { name: 'set-en' }))
    expect(window.localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe('en')
  })

  it('interpolates parameters through t()', () => {
    renderProvider()

    expect(screen.getByTestId('live')).toHaveTextContent('7 live listings')
  })

  it('survives storage access errors and still switches in-memory', async () => {
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

    expect(screen.getByTestId('language')).toHaveTextContent('en')

    await userEvent.click(screen.getByRole('button', { name: 'set-sw' }))
    expect(screen.getByTestId('language')).toHaveTextContent('sw')
    expect(document.documentElement.getAttribute('lang')).toBe('sw')
  })

  it('throws when useLanguage is called outside the provider', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<Probe />)).toThrow('useLanguage must be used within LanguageProvider')
    consoleError.mockRestore()
  })
})

describe('translation helpers', () => {
  it('translate falls back from sw to en and then to the key itself', () => {
    const saved = translations.sw['common.logout']
    delete translations.sw['common.logout']
    try {
      expect(translate('sw', 'common.logout')).toBe(translations.en['common.logout'])
    } finally {
      translations.sw['common.logout'] = saved
    }

    expect(translate('en', 'missing.key.forever')).toBe('missing.key.forever')
  })

  it('interpolate replaces known params and keeps unknown placeholders', () => {
    expect(interpolate('Hi {name}, you owe {amount}', { name: 'Amina', amount: 5000 })).toBe(
      'Hi Amina, you owe 5000',
    )
    expect(interpolate('Hello {name}')).toBe('Hello {name}')
    expect(interpolate('No params here')).toBe('No params here')
  })

  it('applyLanguageToDocument writes the html lang attribute', () => {
    applyLanguageToDocument('sw')
    expect(document.documentElement.getAttribute('lang')).toBe('sw')
    applyLanguageToDocument('en')
    expect(document.documentElement.getAttribute('lang')).toBe('en')
  })
})
