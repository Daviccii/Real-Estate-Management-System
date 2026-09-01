import React, { useEffect, useState } from 'react'
import { managerService } from '../../services/manager'
import type { ManagerDashboard } from '../../services/manager'
import StatCard from '../../components/StatCard'

const ManagerDashboard: React.FC = () => {
  const [dashboard, setDashboard] = useState<ManagerDashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await managerService.getDashboard()
      setDashboard(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="empty">Loading dashboard…</div>
  if (error) return <div className="empty error">{error}</div>
  if (!dashboard) return <div className="empty">No data available</div>

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Manager Dashboard</h1>
        <p>Overview of your managed properties and operations</p>
      </div>

      {/* Quick Stats Grid */}
      <div className="stats-grid">
        <StatCard
          title="Managed Properties"
          value={dashboard.properties.total}
          icon="🏠"
          color="blue"
        />
        <StatCard
          title="Occupied Units"
          value={dashboard.properties.occupied}
          icon="👤"
          color="green"
        />
        <StatCard
          title="Vacant Units"
          value={dashboard.properties.vacant}
          icon="🏢"
          color="orange"
        />
        <StatCard
          title="Active Leases"
          value={dashboard.leases.active}
          icon="📄"
          color="blue"
        />
        <StatCard
          title="Total Tenants"
          value={dashboard.tenants.total}
          icon="👥"
          color="purple"
        />
        <StatCard
          title="Pending Payments"
          value={dashboard.payments.pending}
          icon="⏰"
          color="red"
        />
        <StatCard
          title="Open Maintenance"
          value={dashboard.maintenance.open}
          icon="🔧"
          color="yellow"
        />
        <StatCard
          title="Pending Inquiries"
          value={dashboard.inquiries.pending}
          icon="💬"
          color="cyan"
        />
      </div>

      {/* Key Metrics */}
      <div className="metrics-section">
        <div className="metric-card">
          <h3>Lease Status</h3>
          <div className="metric-item">
            <span>Active Leases</span>
            <strong>{dashboard.leases.active}</strong>
          </div>
          <div className="metric-item">
            <span>Expiring Soon (30 days)</span>
            <strong>{dashboard.leases.expiring_soon}</strong>
          </div>
          <div className="metric-item">
            <span>Total Leases</span>
            <strong>{dashboard.leases.total}</strong>
          </div>
        </div>

        <div className="metric-card">
          <h3>Payment Status</h3>
          <div className="metric-item">
            <span>Overdue Payments</span>
            <strong style={{ color: '#d32f2f' }}>{dashboard.payments.overdue}</strong>
          </div>
          <div className="metric-item">
            <span>Pending Payments</span>
            <strong>{dashboard.payments.pending}</strong>
          </div>
          <div className="metric-item">
            <span>Paid Payments</span>
            <strong style={{ color: '#388e3c' }}>
              {Math.max(0, dashboard.payments.total - dashboard.payments.pending)}
            </strong>
          </div>
          <div className="metric-item" style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid #e0e0e0' }}>
            <span>Outstanding Amount</span>
            <strong>${(dashboard.payments.pending_amount || 0).toFixed(2)}</strong>
          </div>
        </div>

        <div className="metric-card">
          <h3>Maintenance</h3>
          <div className="metric-item">
            <span>Open Requests</span>
            <strong>{dashboard.maintenance.open}</strong>
          </div>
          <div className="metric-item">
            <span>In Progress</span>
            <strong>{dashboard.maintenance.in_progress}</strong>
          </div>
          <div className="metric-item">
            <span>Total Requests</span>
            <strong>{dashboard.maintenance.total}</strong>
          </div>
        </div>
      </div>

      {/* Property Status Distribution */}
      {Object.keys(dashboard.properties.by_status).length > 0 && (
        <div className="properties-status-section">
          <h3>Properties by Status</h3>
          <div className="status-grid">
            {Object.entries(dashboard.properties.by_status).map(([status, count]) => (
              <div key={status} className="status-item">
                <span className="status-label">{status}</span>
                <span className="status-value">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      {dashboard.recent_activity.properties.length > 0 && (
        <div className="recent-activity">
          <h3>Recent Updates</h3>
          <div className="activity-list">
            {dashboard.recent_activity.properties.map((prop) => (
              <div key={`prop-${prop.id}`} className="activity-item">
                <span className="activity-icon">🏠</span>
                <div className="activity-info">
                  <span className="activity-title">{prop.name}</span>
                  <span className="activity-meta">{prop.city} • {prop.status}</span>
                </div>
                {prop.updated_at && (
                  <span className="activity-time">
                    {new Date(prop.updated_at).toLocaleDateString()}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Loading Indicator for Refresh */}
      <div style={{ marginTop: 24, textAlign: 'center' }}>
        <button onClick={loadDashboard} className="button" disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh Dashboard'}
        </button>
      </div>
    </div>
  )
}

export default ManagerDashboard
