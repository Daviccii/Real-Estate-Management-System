import React, { useEffect, useState } from 'react'
import StatCard from '../../components/StatCard'
import { adminService } from '../../services/admin'
import type { DashboardStats } from '../../services/admin'

const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await adminService.getDashboard()
      setStats(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="page">
        <h1>Admin Dashboard</h1>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14 }}>
          {[...Array(8)].map((_, i) => (
            <StatCard key={i} title="Loading..." value="..." loading />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <h1>Admin Dashboard</h1>
        <div className="card" style={{ color: 'var(--danger)' }}>
          Failed to load dashboard: {error}
          <button className="button" onClick={loadDashboard} style={{ marginTop: 12 }}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="page">
        <h1>Admin Dashboard</h1>
        <div className="empty">No data available</div>
      </div>
    )
  }

  const formatRole = (role: string) => {
    return role.charAt(0).toUpperCase() + role.slice(1)
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1>Admin Dashboard</h1>
        <button 
          className="button" 
          onClick={loadDashboard}
          style={{ display: 'flex', alignItems: 'center', gap: 8 }}
        >
          Refresh Data
        </button>
      </div>
      
      {/* User Statistics */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 18, marginBottom: 12 }}>User Statistics</h2>
        <div className="admin-responsive-grid">
          <StatCard title="Total Users" value={stats.users.total} />
          {Object.entries(stats.users.by_role).map(([role, count]) => (
            <StatCard 
              key={role} 
              title={`${formatRole(role)}s`} 
              value={count} 
              subtitle={`${((count / stats.users.total) * 100).toFixed(1)}% of users`}
            />
          ))}
        </div>
      </div>

      {/* Property Statistics */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 18, marginBottom: 12 }}>Property Statistics</h2>
        <div className="admin-responsive-grid">
          <StatCard title="Total Properties" value={stats.properties.total} />
          <StatCard 
            title="Active Properties" 
            value={stats.properties.active} 
            subtitle={`${((stats.properties.active / stats.properties.total) * 100).toFixed(1)}% active`}
          />
          {Object.entries(stats.properties.by_purpose).map(([purpose, count]) => (
            <StatCard 
              key={purpose} 
              title={`${purpose.charAt(0).toUpperCase() + purpose.slice(1)} Properties`} 
              value={count}
            />
          ))}
        </div>
      </div>

      {/* Inquiry Statistics */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 18, marginBottom: 12 }}>Inquiry Statistics</h2>
        <div className="admin-responsive-grid">
          <StatCard title="Total Inquiries" value={stats.inquiries.total} />
          {Object.entries(stats.inquiries.by_status).map(([status, count]) => (
            <StatCard 
              key={status} 
              title={`${status.charAt(0).toUpperCase() + status.slice(1)} Inquiries`} 
              value={count}
            />
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Recent Properties</h3>
          {stats.recent_activity.properties.length === 0 ? (
            <div className="empty">No recent properties</div>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {stats.recent_activity.properties.map((property) => (
                <li key={property.id} style={{ 
                  padding: '8px 0', 
                  borderBottom: '1px solid #f1f5f9',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <div style={{ fontWeight: 700 }}>{property.name}</div>
                    <div style={{ fontSize: 12, color: 'var(--muted)' }}>
                      {property.city || 'Unknown location'} • Owner ID: {property.owner_id}
                    </div>
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--muted)' }}>
                    {property.created_at ? new Date(property.created_at).toLocaleDateString() : 'N/A'}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Recent Inquiries</h3>
          {stats.recent_activity.inquiries.length === 0 ? (
            <div className="empty">No recent inquiries</div>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {stats.recent_activity.inquiries.map((inquiry) => (
                <li key={inquiry.id} style={{ 
                  padding: '8px 0', 
                  borderBottom: '1px solid #f1f5f9',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <div style={{ fontWeight: 700 }}>Inquiry #{inquiry.id}</div>
                    <div style={{ fontSize: 12, color: 'var(--muted)' }}>
                      User: {inquiry.user_id} • Property: {inquiry.property_id}
                    </div>
                  </div>
                  <div style={{ 
                    padding: '2px 8px', 
                    borderRadius: 4, 
                    fontSize: 11, 
                    background: inquiry.status === 'pending' ? 'var(--warning-bg)' : 'var(--success-bg)',
                    color: inquiry.status === 'pending' ? 'var(--warning)' : 'var(--success)'
                  }}>
                    {inquiry.status}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}

export default AdminDashboard