import React, { useEffect, useState } from 'react'
import { managerService } from '../../services/manager'
import type { ManagerInquiry } from '../../services/manager'

const ManagerInquiries: React.FC = () => {
  const [inquiries, setInquiries] = useState<ManagerInquiry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    loadInquiries()
  }, [statusFilter])

  const loadInquiries = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: any = {}
      if (statusFilter) params.status = statusFilter
      const data = await managerService.getInquiries(params)
      setInquiries(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load inquiries')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="empty">Loading inquiries…</div>
  if (error) return <div className="empty error">{error}</div>

  return (
    <div className="management-container">
      <div className="management-header">
        <h1>Inquiries</h1>
        <p>Manage property inquiries from users</p>
      </div>

      <div className="controls-section">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="input"
        >
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="responded">Responded</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>User ID</th>
              <th>Property ID</th>
              <th>Message</th>
              <th>Status</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {inquiries.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                  No inquiries found
                </td>
              </tr>
            ) : (
              inquiries.map((inquiry) => (
                <tr key={inquiry.id}>
                  <td>{inquiry.user_id}</td>
                  <td>{inquiry.property_id}</td>
                  <td>
                    {inquiry.message ? inquiry.message.substring(0, 50) : '—'}
                    {inquiry.message && inquiry.message.length > 50 ? '...' : ''}
                  </td>
                  <td>
                    <span className={`badge status-${inquiry.status}`}>
                      {inquiry.status}
                    </span>
                  </td>
                  <td>
                    {inquiry.created_at ? new Date(inquiry.created_at).toLocaleDateString() : '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 24, textAlign: 'center' }}>
        <button onClick={loadInquiries} className="button" disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh Inquiries'}
        </button>
      </div>
    </div>
  )
}

export default ManagerInquiries
