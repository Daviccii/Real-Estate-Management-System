import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMyDeletionRequest, requestAccountDeletion, cancelAccountDeletion, exportMyData, type DeletionRequestInfo } from '../services/privacy'
import { useAuth } from '../contexts/AuthContext'

const DATA_CATEGORIES: Array<{ title: string; body: string }> = [
  {
    title: 'Account data',
    body: 'Your name, email address, phone number, role, and profile photo. Used to operate your account and cannot be removed while the account exists, but can be exported or erased with the account.',
  },
  {
    title: 'Property activity',
    body: 'Favorites, inquiries, viewings, and rental applications you create. Exported on request; erased with your account except where a signed lease or payment record must be retained.',
  },
  {
    title: 'Financial records',
    body: 'Leases, payments, and invoices. Retained for the period required by tax and accounting law, with your identity anonymized once your account is erased.',
  },
  {
    title: 'Security records',
    body: 'Audit logs and login events. Retained in anonymized form to detect fraud and comply with security obligations.',
  },
]

const Privacy: React.FC = () => {
  const { user } = useAuth()
  const [deletion, setDeletion] = useState<DeletionRequestInfo | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    if (!user) return
    let cancelled = false
    getMyDeletionRequest()
      .then((res) => { if (!cancelled) setDeletion(res.request) })
      .catch(() => {})
    return () => { cancelled = true }
  }, [user])

  const openSettings = () => window.dispatchEvent(new Event('pn-open-consent'))

  const handleExport = async () => {
    setBusy(true); setError(null)
    try {
      await exportMyData()
    } catch {
      setError('Could not download your export. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  const handleRequestDeletion = async () => {
    if (!window.confirm('Request deletion of your account and personal data? An administrator will review it; you can cancel until it is executed.')) return
    setBusy(true); setError(null)
    try {
      const res = await requestAccountDeletion('Requested by user from privacy page')
      setDeletion(res.request)
      setNotice('Your deletion request has been submitted.')
    } catch {
      setError('Could not submit your deletion request.')
    } finally {
      setBusy(false)
    }
  }

  const handleCancelDeletion = async () => {
    setBusy(true); setError(null)
    try {
      await cancelAccountDeletion()
      setDeletion((d) => (d ? { ...d, status: 'cancelled' } : d))
      setNotice('Your deletion request has been cancelled.')
    } catch {
      setError('Could not cancel the request.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container" style={{ maxWidth: 860, margin: '0 auto', padding: '32px 16px' }}>
      <h1>Privacy Policy</h1>
      <p style={{ color: '#6b7280' }}>
        How PropNoxa collects, uses, and protects your personal data. Policy version 1.0.
        You can revisit your cookie choices at any time via{' '}
        <button className="link" onClick={openSettings} style={{ padding: 0, border: 'none', background: 'none', cursor: 'pointer', textDecoration: 'underline' }}>
          cookie settings
        </button>.
      </p>

      <h2>What we collect</h2>
      {DATA_CATEGORIES.map((c) => (
        <div key={c.title} className="card" style={{ marginBottom: 12, padding: 16 }}>
          <h3 style={{ margin: '0 0 6px' }}>{c.title}</h3>
          <p style={{ margin: 0 }}>{c.body}</p>
        </div>
      ))}

      <h2>Cookies</h2>
      <p>
        Essential cookies keep you signed in and secure. Analytics and marketing cookies
        are optional and only set after you opt in through the consent banner. We record
        every consent decision (including refusals) so we can honour your choices.
      </p>

      <h2>Your rights</h2>
      <p>
        You can export all data we hold about you as a machine-readable JSON file, and you
        can request erasure of your account. Financial and security records are retained
        where the law requires it, with your identity anonymized.
      </p>

      {user && (
        <div className="card" style={{ padding: 16, marginTop: 24 }}>
          <h2 style={{ marginTop: 0 }}>Your data controls</h2>
          {notice && <p style={{ color: '#15803d' }}>{notice}</p>}
          {error && <p style={{ color: '#b91c1c' }}>{error}</p>}
          {deletion && deletion.status === 'pending' && (
            <p style={{ color: '#b45309' }}>
              A deletion request submitted {deletion.requested_at ? new Date(deletion.requested_at).toLocaleString() : ''} is pending review.
            </p>
          )}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button className="button" onClick={handleExport} disabled={busy}>
              Download my data (JSON)
            </button>
            {deletion?.status === 'pending' ? (
              <button className="button muted" onClick={handleCancelDeletion} disabled={busy}>
                Cancel deletion request
              </button>
            ) : (
              <button className="button danger" onClick={handleRequestDeletion} disabled={busy}>
                Request account deletion
              </button>
            )}
          </div>
        </div>
      )}

      {!user && (
        <p style={{ marginTop: 24 }}>
          <Link to="/login">Sign in</Link> to download your data or request account deletion.
        </p>
      )}

      <h2>Contact</h2>
      <p>
        Questions about this policy or your data? Contact our data protection team through the{' '}
        <Link to="/contact">contact page</Link>.
      </p>
    </div>
  )
}

export default Privacy
