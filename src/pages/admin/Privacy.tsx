import React, { useEffect, useState } from 'react'
import { listDeletionRequests, executeDeletionRequest, declineDeletionRequest, type DeletionRequestInfo } from '../../services/privacy'

const STATUS_STYLES: Record<string, React.CSSProperties> = {
  pending: { color: '#b45309', fontWeight: 600 },
  completed: { color: '#15803d', fontWeight: 600 },
  cancelled: { color: '#6b7280' },
  declined: { color: '#b91c1c' },
}

const AdminPrivacy: React.FC = () => {
  const [requests, setRequests] = useState<DeletionRequestInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [decliningId, setDecliningId] = useState<number | null>(null)
  const [declineNotes, setDeclineNotes] = useState('')

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await listDeletionRequests()
      setRequests(res.requests)
    } catch {
      setError('Could not load deletion requests.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const handleExecute = async (id: number) => {
    if (!window.confirm('Permanently anonymize this user account? This cannot be undone.')) return
    try {
      await executeDeletionRequest(id)
      await load()
    } catch {
      setError('Could not execute the deletion.')
    }
  }

  const handleDecline = async (id: number) => {
    try {
      await declineDeletionRequest(id, declineNotes || undefined)
      setDecliningId(null)
      setDeclineNotes('')
      await load()
    } catch {
      setError('Could not decline the request.')
    }
  }

  return (
    <div>
      <h1>Deletion Requests</h1>
      <p style={{ color: 'var(--muted)' }}>
        User requests for account erasure (GDPR Art. 17). Executing a request irreversibly
        anonymizes the account; financial and security records are retained without personal identity.
      </p>
      {error && <p style={{ color: '#b91c1c' }}>{error}</p>}
      {loading ? (
        <div className="empty">Loading requests…</div>
      ) : requests.length === 0 ? (
        <div className="empty">No deletion requests.</div>
      ) : (
        <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', padding: 12 }}>Request</th>
                <th style={{ textAlign: 'left', padding: 12 }}>User</th>
                <th style={{ textAlign: 'left', padding: 12 }}>Requested</th>
                <th style={{ textAlign: 'left', padding: 12 }}>Reason</th>
                <th style={{ textAlign: 'left', padding: 12 }}>Status</th>
                <th style={{ textAlign: 'left', padding: 12 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {requests.map((r) => (
                <tr key={r.id}>
                  <td style={{ padding: 12 }}>#{r.id}</td>
                  <td style={{ padding: 12 }}>user #{r.user_id ?? '—'}</td>
                  <td style={{ padding: 12 }}>{r.requested_at ? new Date(r.requested_at).toLocaleString() : '—'}</td>
                  <td style={{ padding: 12 }}>{r.reason || '—'}</td>
                  <td style={{ padding: 12 }}>
                    <span style={STATUS_STYLES[r.status] || {}}>{r.status}</span>
                    {r.notes && <div style={{ fontSize: 12, color: 'var(--muted)' }}>{r.notes}</div>}
                  </td>
                  <td style={{ padding: 12 }}>
                    {r.status === 'pending' && (
                      decliningId === r.id ? (
                        <div style={{ display: 'flex', gap: 6, flexDirection: 'column', minWidth: 220 }}>
                          <input
                            aria-label="Decline reason"
                            placeholder="Reason for declining"
                            value={declineNotes}
                            onChange={(e) => setDeclineNotes(e.target.value)}
                          />
                          <div style={{ display: 'flex', gap: 6 }}>
                            <button className="button" onClick={() => handleDecline(r.id)}>Confirm decline</button>
                            <button className="button muted" onClick={() => { setDecliningId(null); setDeclineNotes('') }}>Cancel</button>
                          </div>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button className="button danger" onClick={() => handleExecute(r.id)}>Execute</button>
                          <button className="button muted" onClick={() => setDecliningId(r.id)}>Decline</button>
                        </div>
                      )
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default AdminPrivacy
