import React, { useEffect, useState } from 'react'
import { managerService } from '../../services/manager'
import type { ManagerTenant } from '../../services/manager'

const ManagerTenants: React.FC = () => {
  const [tenants, setTenants] = useState<ManagerTenant[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    loadTenants()
  }, [])

  const loadTenants = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await managerService.getTenants()
      setTenants(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load tenants')
    } finally {
      setLoading(false)
    }
  }

  const filteredTenants = tenants.filter(tenant => {
    const matchesSearch = !searchTerm || 
      tenant.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tenant.email.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesSearch
  })

  if (loading) return <div className="empty">Loading tenants…</div>
  if (error) return <div className="empty error">{error}</div>

  return (
    <div className="management-container">
      <div className="management-header">
        <h1>Tenants</h1>
        <p>Manage active tenants in your properties</p>
      </div>

      <div className="controls-section">
        <input
          type="text"
          placeholder="Search tenants by name or email…"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="input"
          style={{ flex: 1, maxWidth: 400 }}
        />
      </div>

      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Status</th>
              <th>Joined</th>
            </tr>
          </thead>
          <tbody>
            {filteredTenants.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                  No tenants found
                </td>
              </tr>
            ) : (
              filteredTenants.map((tenant) => (
                <tr key={tenant.id}>
                  <td><strong>{tenant.full_name || 'N/A'}</strong></td>
                  <td>{tenant.email}</td>
                  <td>
                    <span className={`badge ${tenant.is_active ? 'status-active' : 'status-inactive'}`}>
                      {tenant.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    {tenant.created_at ? new Date(tenant.created_at).toLocaleDateString() : '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 24, textAlign: 'center' }}>
        <button onClick={loadTenants} className="button" disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh Tenants'}
        </button>
      </div>
    </div>
  )
}

export default ManagerTenants
