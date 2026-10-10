import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'

import ThemeToggle from './ThemeToggle'
import { ThemeProvider, THEME_STORAGE_KEY } from '../contexts/ThemeContext'

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

// Plain closures instead of vi.fn() so setup.ts's restoreAllMocks cannot strip
// the implementation between tests.
const installMatchMedia = (matches: boolean) => {
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    writable: true,
    value: () => ({
      matches,
      media: '(prefers-color-scheme: dark)',
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => true,
    }),
  })
}

const renderToggle = () =>
  render(
    <ThemeProvider>
      <ThemeToggle />
    </ThemeProvider>,
  )

beforeEach(() => {
  Object.defineProperty(window, 'localStorage', { value: createStorageMock(), configurable: true })
  document.documentElement.removeAttribute('data-theme')
})

describe('ThemeToggle', () => {
  it('shows the current preference and cycles light → dark → system', async () => {
    installMatchMedia(false)
    renderToggle()

    const button = screen.getByRole('button', { name: 'Theme: System. Activate for Light.' })
    expect(button).toHaveAttribute('data-theme-preference', 'system')
    expect(button).toHaveTextContent('🖥️')

    await userEvent.click(button)
    expect(button).toHaveAttribute('data-theme-preference', 'light')
    expect(button).toHaveAccessibleName('Theme: Light. Activate for Dark.')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('light')

    await userEvent.click(button)
    expect(button).toHaveAttribute('data-theme-preference', 'dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')

    await userEvent.click(button)
    expect(button).toHaveAttribute('data-theme-preference', 'system')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('system')
  })

  it('reflects a stored dark preference on first render', () => {
    installMatchMedia(false)
    window.localStorage.setItem(THEME_STORAGE_KEY, 'dark')
    renderToggle()

    const button = screen.getByRole('button', { name: 'Theme: Dark. Activate for System.' })
    expect(button).toHaveTextContent('🌙')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('accepts an extra className without dropping its own styles', () => {
    installMatchMedia(false)
    render(
      <ThemeProvider>
        <ThemeToggle className="custom-slot" />
      </ThemeProvider>,
    )

    const button = screen.getByRole('button', { name: /Theme:/ })
    expect(button).toHaveClass('button')
    expect(button).toHaveClass('muted')
    expect(button).toHaveClass('theme-toggle')
    expect(button).toHaveClass('custom-slot')
  })
})
