import React, { useEffect, useState } from 'react'
import { mfaService } from '../services/mfa'
import type { MfaSetup, MfaStatus } from '../services/mfa'
import { useToast } from './ToastProvider'

const inputStyle: React.CSSProperties = { width: '100%' }

const MfaPanel: React.FC = () => {
  const { addToast } = useToast()
  const [status, setStatus] = useState<MfaStatus | null>(null)
  const [setup, setSetup] = useState<MfaSetup | null>(null)
  const [code, setCode] = useState('')
  const [codes, setCodes] = useState<string[] | null>(null)
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)

  const fail = (err: any, fallback: string) =>
    addToast({ message: err?.message || fallback, type: 'error' })

  const load = async () => {
    setLoading(true)
    try {
      setStatus(await mfaService.status())
    } catch (err: any) {
      fail(err, 'Failed to load MFA status')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const beginSetup = async () => {
    setBusy(true)
    try {
      setSetup(await mfaService.setup())
      setCodes(null)
    } catch (err: any) {
      fail(err, 'Could not start MFA enrolment')
    } finally {
      setBusy(false)
    }
  }

  const enable = async () => {
    if (code.trim().length === 0) return
    setBusy(true)
    try {
      const result = await mfaService.enable(code.trim())
      setCodes(result.recovery_codes)
      setSetup(null)
      setCode('')
      addToast({ message: 'Two-factor authentication enabled', type: 'success' })
      load()
    } catch (err: any) {
      fail(err, 'Invalid code - check your authenticator and try again')
    } finally {
      setBusy(false)
    }
  }

  const disable = async () => {
    if (code.trim().length === 0) return
    setBusy(true)
    try {
      await mfaService.disable(code.trim())
      setCode('')
      setCodes(null)
      addToast({ message: 'Two-factor authentication disabled', type: 'success' })
      load()
    } catch (err: any) {
      fail(err, 'Invalid code - MFA was not disabled')
    } finally {
      setBusy(false)
    }
  }

  const regenerate = async () => {
    if (code.trim().length === 0) return
    setBusy(true)
    try {
      const result = await mfaService.regenerateRecoveryCodes(code.trim())
      setCodes(result.recovery_codes)
      setCode('')
      load()
    } catch (err: any) {
      fail(err, 'Invalid code - recovery codes were not regenerated')
    } finally {
      setBusy(false)
    }
  }

  const enabled = Boolean(status?.mfa_enabled)

  return (
    <div className="card">
      <h3 style={{ marginBottom: 12 }}>Two-Factor Authentication</h3>

      {loading && <div className="empty">Loading security settings…</div>}

      {!loading && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <span
              className="badge"
              style={{
                fontWeight: 600,
                background: enabled ? '#d1fae5' : '#fef3c7',
                color: enabled ? '#047857' : '#92400e',
              }}
            >
              {enabled ? 'Enabled' : 'Disabled'}
            </span>
            {status?.mandatory_for_admin && !enabled && (
              <span style={{ color: 'var(--danger)', fontSize: 13 }}>Required for your role</span>
            )}
          </div>

          {status && enabled && (
            <div style={{ display: 'grid', gap: 6, fontSize: 13, marginBottom: 12 }}>
              <div>Recovery codes remaining: {status.recovery_codes_remaining}</div>
              <div>SMS backup: {status.sms_available ? 'available' : 'add a phone number to your profile'}</div>
            </div>
          )}

          {status && !enabled && !setup && (
            <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>
              Protect this account with a time-based code from an authenticator app
              (Google Authenticator, Authy, 1Password).
            </p>
          )}

          {setup && (
            <div style={{ display: 'grid', gap: 10, marginBottom: 12 }}>
              <div style={{ fontSize: 13 }}>
                Add your account to an authenticator app using the secret below, then enter the
                6-digit code it shows.
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <code style={{ background: 'var(--bg-secondary)', padding: '6px 8px', borderRadius: 4, wordBreak: 'break-all' }}>
                  {setup.secret}
                </code>
                <a className="button muted" href={setup.provisioning_uri}>Open in authenticator app</a>
              </div>
              <div style={{ fontSize: 12, color: 'var(--muted)' }}>
                Or scan this provisioning URI as a QR code: <span style={{ wordBreak: 'break-all' }}>{setup.provisioning_uri}</span>
              </div>
              <div>
                <label htmlFor="mfa-setup-code" style={{ display: 'block', marginBottom: 4, fontSize: 12, fontWeight: 600 }}>Verification code</label>
                <input
                  id="mfa-setup-code"
                  className="input"
                  style={inputStyle}
                  inputMode="numeric"
                  maxLength={8}
                  placeholder="123456"
                  value={code}
                  onChange={e => setCode(e.target.value)}
                />
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="button" onClick={enable} disabled={busy}>{busy ? 'Verifying…' : 'Enable MFA'}</button>
                <button className="button muted" onClick={() => { setSetup(null); setCode('') }} disabled={busy}>Cancel</button>
              </div>
            </div>
          )}

          {!setup && (enabled || status?.has_secret) && (
            <div style={{ display: 'grid', gap: 8, marginBottom: 12 }}>
              <label htmlFor="mfa-action-code" style={{ display: 'block', fontSize: 12, fontWeight: 600 }}>
                Authenticator code {enabled ? '(required to change settings)' : ''}
              </label>
              <input
                id="mfa-action-code"
                className="input"
                style={inputStyle}
                inputMode="numeric"
                maxLength={8}
                placeholder="123456"
                value={code}
                onChange={e => setCode(e.target.value)}
              />
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {!enabled && <button className="button" onClick={beginSetup} disabled={busy}>Restart setup</button>}
                {enabled && (
                  <>
                    <button className="button secondary" onClick={regenerate} disabled={busy || !code.trim()}>
                      Regenerate recovery codes
                    </button>
                    <button className="button muted" onClick={disable} disabled={busy || !code.trim()}>
                      Disable MFA
                    </button>
                  </>
                )}
              </div>
            </div>
          )}

          {!enabled && !setup && !status?.has_secret && (
            <button className="button" onClick={beginSetup} disabled={busy}>
              {busy ? 'Preparing…' : 'Set up authenticator app'}
            </button>
          )}

          {codes && (
            <div
              className="card"
              style={{
                marginTop: 12,
                border: '1px solid var(--warning, #d97706)',
                display: 'grid',
                gap: 8,
              }}
            >
              <strong style={{ fontSize: 13 }}>Save these recovery codes now</strong>
              <p style={{ fontSize: 12, color: 'var(--muted)' }}>
                Each code works once if you lose your authenticator. They are shown only this time.
              </p>
              <pre style={{ margin: 0, fontSize: 12, fontFamily: 'ui-monospace, monospace', whiteSpace: 'pre-wrap' }}>
                {codes.join('\n')}
              </pre>
              <button className="button muted" onClick={() => setCodes(null)}>Done</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default MfaPanel
