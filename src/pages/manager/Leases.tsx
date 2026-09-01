import React, { useEffect, useState } from 'react'
import { managerService } from '../../services/manager'
import type { ManagerLease } from '../../services/manager'

const ManagerLeases: React.FC = () => {
  const [leases, setLeases] = useState<ManagerLease[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    loadLeases()
  }, [statusFilter])

  const loadLeases = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: any = {}
      if (statusFilter) params.status = statusFilter
      const data = await managerService.getLeases(params)
      setLeases(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load leases')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="empty">Loading leases…</div>
  if (error) return <div className="empty error">{error}</div>

  return (
    <div className="management-container">
      <div className="management-header">
        <h1>Leases</h1>
        <p>Manage all leases for your properties</p>
      </div>

      <div className="controls-section">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="input"
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="expired">Expired</option>
          <option value="pending">Pending</option>
          <option value="terminated">Terminated</option>
        </select>
      </div>

      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Tenant ID</th>
              <th>Property ID</th>
              <th>Start Date</th>
              <th>End Date</th>
              <th>Rent Amount</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {leases.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                  No leases found
                </td>
              </tr>
            ) : (
              leases.map((lease) => (
                <tr key={lease.id}>
                  <td>{lease.tenant_id}</td>
                  <td>{lease.property_id}</td>
                  <td>
                    {lease.start_date ? new Date(lease.start_date).toLocaleDateString() : '—'}
                  </td>
                  <td>
                    {lease.end_date ? new Date(lease.end_date).toLocaleDateString() : '—'}
                  </td>
                  <td>${lease.rent_amount.toFixed(2)}</td>
                  <td>
                    <span className={`badge status-${lease.status}`}>
                      {lease.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 24, textAlign: 'center' }}>
        <button onClick={loadLeases} className="button" disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh Leases'}
        </button>
      </div>
    </div>
  )
}

export default ManagerLeases
