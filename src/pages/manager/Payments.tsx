import React, { useEffect, useState } from 'react'
import { managerService } from '../../services/manager'
import type { ManagerPayment, PaymentsOverview } from '../../services/manager'

const ManagerPayments: React.FC = () => {
  const [payments, setPayments] = useState<ManagerPayment[]>([])
  const [overview, setOverview] = useState<PaymentsOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    loadPayments()
    loadOverview()
  }, [statusFilter])

  const loadPayments = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: any = {}
      if (statusFilter) params.status = statusFilter
      const data = await managerService.getPayments(params)
      setPayments(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load payments')
    } finally {
      setLoading(false)
    }
  }

  const loadOverview = async () => {
    try {
      const data = await managerService.getPaymentsOverview()
      setOverview(data)
    } catch (err: any) {
      console.error('Failed to load overview:', err)
    }
  }

  if (loading) return <div className="empty">Loading payments…</div>
  if (error) return <div className="empty error">{error}</div>

  return (
    <div className="management-container">
      <div className="management-header">
        <h1>Payments</h1>
        <p>Monitor payment status and collections</p>
      </div>

      {/* Overview Cards */}
      {overview && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Total Payments</div>
            <div className="stat-value">{overview.total}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Paid</div>
            <div className="stat-value" style={{ color: '#388e3c' }}>{overview.paid}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Pending</div>
            <div className="stat-value" style={{ color: '#f57c00' }}>{overview.pending}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Overdue</div>
            <div className="stat-value" style={{ color: '#d32f2f' }}>{overview.overdue}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Outstanding Amount</div>
            <div className="stat-value">${overview.total_amount.toFixed(2)}</div>
          </div>
        </div>
      )}

      <div className="controls-section">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="input"
        >
          <option value="">All Statuses</option>
          <option value="paid">Paid</option>
          <option value="pending">Pending</option>
          <option value="overdue">Overdue</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Tenant ID</th>
              <th>Amount</th>
              <th>Due Date</th>
              <th>Payment Date</th>
              <th>Status</th>
              <th>Type</th>
            </tr>
          </thead>
          <tbody>
            {payments.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                  No payments found
                </td>
              </tr>
            ) : (
              payments.map((payment) => (
                <tr key={payment.id}>
                  <td>{payment.tenant_id}</td>
                  <td>${payment.amount.toFixed(2)}</td>
                  <td>
                    {payment.due_date ? new Date(payment.due_date).toLocaleDateString() : '—'}
                  </td>
                  <td>
                    {payment.payment_date ? new Date(payment.payment_date).toLocaleDateString() : '—'}
                  </td>
                  <td>
                    <span className={`badge status-${payment.status}`}>
                      {payment.status}
                    </span>
                  </td>
                  <td>{payment.payment_type || '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 24, textAlign: 'center' }}>
        <button onClick={() => { loadPayments(); loadOverview() }} className="button" disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh Payments'}
        </button>
      </div>
    </div>
  )
}

export default ManagerPayments
