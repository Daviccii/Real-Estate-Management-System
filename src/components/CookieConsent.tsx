import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { recordConsent } from '../services/privacy'

const STORAGE_KEY = 'pn-consent'
const CLIENT_ID_KEY = 'pn-consent-client'
const POLICY_VERSION = '1.0'

// Reach through window: Node 24 exposes a broken bare `localStorage` global.
const storage = (): Storage | null => {
  try {
    return window.localStorage
  } catch {
    return null
  }
}

export interface ConsentState {
  analytics: boolean
  marketing: boolean
  decidedAt: string
}

export function getConsent(): ConsentState | null {
  try {
    const raw = storage()?.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as ConsentState) : null
  } catch {
    return null
  }
}

export function getClientId(): string {
  const store = storage()
  try {
    let id = store?.getItem(CLIENT_ID_KEY) || null
    if (!id) {
      id = `c-${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`
      store?.setItem(CLIENT_ID_KEY, id)
    }
    return id
  } catch {
    return 'c-unknown'
  }
}

export function saveConsent(choices: { analytics: boolean; marketing: boolean }): void {
  const state: ConsentState = { ...choices, decidedAt: new Date().toISOString() }
  try {
    storage()?.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
    /* storage unavailable (private mode) — banner will reappear next visit */
  }
  const clientId = getClientId()
  // Record refusals too: the log must show consent was asked, not assumed.
  void recordConsent({ consent_type: 'cookie_analytics', granted: choices.analytics, policy_version: POLICY_VERSION, client_id: clientId }).catch(() => {})
  void recordConsent({ consent_type: 'cookie_marketing', granted: choices.marketing, policy_version: POLICY_VERSION, client_id: clientId }).catch(() => {})
}

const CookieConsent: React.FC = () => {
  const [visible, setVisible] = useState(false)
  const [details, setDetails] = useState(false)
  const [analytics, setAnalytics] = useState(true)
  const [marketing, setMarketing] = useState(false)

  useEffect(() => {
    if (!getConsent()) setVisible(true)
    const reopen = () => setVisible(true)
    window.addEventListener('pn-open-consent', reopen)
    return () => window.removeEventListener('pn-open-consent', reopen)
  }, [])

  if (!visible) return null

  const decide = (choices: { analytics: boolean; marketing: boolean }) => {
    saveConsent(choices)
    setVisible(false)
  }

  return (
    <div
      role="dialog"
      aria-label="Cookie consent"
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        background: '#111827',
        color: '#f9fafb',
        padding: '16px 24px',
        boxShadow: '0 -4px 16px rgba(0,0,0,0.25)',
      }}
    >
      <div style={{ maxWidth: 960, margin: '0 auto' }}>
        <p style={{ margin: '0 0 8px', fontSize: 14 }}>
          We use essential cookies to run PropNoxa. With your permission we also use
          analytics and marketing cookies. Read our{' '}
          <Link to="/privacy" style={{ color: '#93c5fd' }}>privacy policy</Link>.
        </p>
        {details && (
          <div style={{ margin: '8px 0', fontSize: 13 }}>
            <label style={{ display: 'block', opacity: 0.7 }}>
              <input type="checkbox" checked disabled /> Essential (always on)
            </label>
            <label style={{ display: 'block' }}>
              <input
                type="checkbox"
                checked={analytics}
                onChange={(e) => setAnalytics(e.target.checked)}
              />{' '}
              Analytics — usage statistics that help us improve the product
            </label>
            <label style={{ display: 'block' }}>
              <input
                type="checkbox"
                checked={marketing}
                onChange={(e) => setMarketing(e.target.checked)}
              />{' '}
              Marketing — personalised property recommendations and offers
            </label>
          </div>
        )}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button className="button" onClick={() => decide({ analytics: true, marketing: true })}>
            Accept all
          </button>
          <button className="button muted" onClick={() => decide({ analytics: false, marketing: false })}>
            Essential only
          </button>
          <button
            className="button muted"
            onClick={() => (details ? decide({ analytics, marketing }) : setDetails(true))}
          >
            {details ? 'Save my choices' : 'Customise'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default CookieConsent
