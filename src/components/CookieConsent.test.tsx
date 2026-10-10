import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import CookieConsent, { getConsent } from './CookieConsent'
import * as privacy from '../services/privacy'

vi.mock('../services/privacy', () => ({
  recordConsent: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, MemoryRouter: actual.MemoryRouter }
})

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

const renderBanner = () =>
  render(
    <MemoryRouter>
      <CookieConsent />
    </MemoryRouter>,
  )

beforeEach(() => {
  Object.defineProperty(window, 'localStorage', { value: createStorageMock(), configurable: true })
  // setup.ts's afterEach restoreAllMocks strips factory-set implementations.
  const recordConsentMock = vi.mocked(privacy.recordConsent)
  recordConsentMock.mockClear()
  recordConsentMock.mockResolvedValue(undefined)
})

describe('CookieConsent', () => {
  it('shows the banner until a decision is stored', () => {
    renderBanner()
    expect(screen.getByRole('dialog', { name: 'Cookie consent' })).toBeInTheDocument()
  })

  it('stays hidden once consent was already decided', () => {
    window.localStorage.setItem('pn-consent', JSON.stringify({ analytics: true, marketing: false, decidedAt: '2026-01-01' }))
    const { container } = renderBanner()
    expect(container).toBeEmptyDOMElement()
  })

  it('accept-all hides the banner, persists the choice, and records both categories', async () => {
    renderBanner()
    await userEvent.click(screen.getByRole('button', { name: 'Accept all' }))

    expect(screen.queryByRole('dialog', { name: 'Cookie consent' })).not.toBeInTheDocument()
    expect(getConsent()).toMatchObject({ analytics: true, marketing: true })
    expect(privacy.recordConsent).toHaveBeenCalledWith(
      expect.objectContaining({ consent_type: 'cookie_analytics', granted: true }),
    )
    expect(privacy.recordConsent).toHaveBeenCalledWith(
      expect.objectContaining({ consent_type: 'cookie_marketing', granted: true }),
    )
  })

  it('essential-only records refusals so the log shows consent was asked', async () => {
    renderBanner()
    await userEvent.click(screen.getByRole('button', { name: 'Essential only' }))

    expect(getConsent()).toMatchObject({ analytics: false, marketing: false })
    expect(privacy.recordConsent).toHaveBeenCalledWith(
      expect.objectContaining({ consent_type: 'cookie_analytics', granted: false }),
    )
    expect(privacy.recordConsent).toHaveBeenCalledWith(
      expect.objectContaining({ consent_type: 'cookie_marketing', granted: false }),
    )
  })

  it('customise lets the user save per-category choices', async () => {
    renderBanner()
    await userEvent.click(screen.getByRole('button', { name: 'Customise' }))

    const checkboxes = screen.getAllByRole('checkbox')
    expect(checkboxes[0]).toBeDisabled() // essential always on
    await userEvent.click(checkboxes[1]) // analytics off
    await userEvent.click(screen.getByRole('button', { name: 'Save my choices' }))

    expect(getConsent()).toMatchObject({ analytics: false, marketing: false })
  })

  it('reopens when the privacy page dispatches pn-open-consent', async () => {
    window.localStorage.setItem('pn-consent', JSON.stringify({ analytics: true, marketing: true, decidedAt: '2026-01-01' }))
    renderBanner()
    expect(screen.queryByRole('dialog', { name: 'Cookie consent' })).not.toBeInTheDocument()

    window.dispatchEvent(new Event('pn-open-consent'))
    expect(await screen.findByRole('dialog', { name: 'Cookie consent' })).toBeInTheDocument()
  })
})
