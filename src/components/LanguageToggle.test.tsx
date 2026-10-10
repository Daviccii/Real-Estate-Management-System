import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'

import LanguageToggle from './LanguageToggle'
import { LanguageProvider, LANGUAGE_STORAGE_KEY } from '../i18n/LanguageContext'

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

const renderToggle = () =>
  render(
    <LanguageProvider>
      <LanguageToggle />
    </LanguageProvider>,
  )

beforeEach(() => {
  Object.defineProperty(window, 'localStorage', { value: createStorageMock(), configurable: true })
  document.documentElement.removeAttribute('lang')
})

describe('LanguageToggle', () => {
  it('shows the current language and toggles between English and Kiswahili', async () => {
    renderToggle()

    const button = screen.getByRole('button', { name: 'Language: English. Activate for Kiswahili.' })
    expect(button).toHaveAttribute('data-language', 'en')
    expect(button).toHaveTextContent('EN')

    await userEvent.click(button)
    expect(button).toHaveAttribute('data-language', 'sw')
    expect(button).toHaveAccessibleName('Language: Kiswahili. Activate for English.')
    expect(button).toHaveTextContent('SW')
    expect(document.documentElement.getAttribute('lang')).toBe('sw')
    expect(window.localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe('sw')

    await userEvent.click(button)
    expect(button).toHaveAttribute('data-language', 'en')
    expect(button).toHaveTextContent('EN')
    expect(document.documentElement.getAttribute('lang')).toBe('en')
    expect(window.localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe('en')
  })

  it('reflects a stored Swahili preference on first render', () => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, 'sw')
    renderToggle()

    const button = screen.getByRole('button', { name: 'Language: Kiswahili. Activate for English.' })
    expect(button).toHaveTextContent('SW')
    expect(document.documentElement.getAttribute('lang')).toBe('sw')
  })

  it('accepts an extra className without dropping its own styles', () => {
    render(
      <LanguageProvider>
        <LanguageToggle className="custom-slot" />
      </LanguageProvider>,
    )

    const button = screen.getByRole('button', { name: /Language:/ })
    expect(button).toHaveClass('button')
    expect(button).toHaveClass('muted')
    expect(button).toHaveClass('language-toggle')
    expect(button).toHaveClass('custom-slot')
  })
})
