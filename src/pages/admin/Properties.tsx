import React, { useEffect, useState } from 'react'
import { adminService } from '../../services/admin'
import type { AdminProperty } from '../../services/admin'
import ConfirmDialog from '../../components/ConfirmDialog'
import { useToast } from '../../components/ToastProvider'

const PropertiesManagement: React.FC = () => {
  const [properties, setProperties] = useState<AdminProperty[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [selectedProperty, setSelectedProperty] = useState<AdminProperty | null>(null)
  const { addToast } = useToast()

  useEffect(() => {
    loadProperties()
  }, [statusFilter])

  const loadProperties = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: any = {}
      if (statusFilter) params.status = statusFilter
      const data = await adminService.getProperties(params)
      setProperties(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load properties')
    } finally {
      setLoading(false)
    }
  }

  const filteredProperties = properties.filter(property => {
    const matchesSearch = !searchTerm || 
      property.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (property.city && property.city.toLowerCase().includes(searchTerm.toLowerCase()))
    return matchesSearch
  })

  const handleDeleteProperty = (property: AdminProperty) => {
    setSelectedProperty(property)
    setShowDeleteConfirm(true)
  }

  const confirmDelete = async () => {
    if (!selectedProperty) return
    
    // Note: This requires backend endpoint implementation
    // For now, just show a message
    addToast({ 
      message: 'Property deletion requires backend endpoint implementation', 
      type: 'warning' 
    })
    setShowDeleteConfirm(false)
    setSelectedProperty(null)
  }

  const getStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'var(--success)',
      inactive: 'var(--danger)',
      pending: 'var(--warning)',
      sold: 'var(--primary)',
      rented: 'var(--primary)'
    }
    return colors[status] || 'var(--muted)'
  }

  const getPurposeBadgeColor = (purpose: string | null) => {
    if (!purpose) return 'var(--muted)'
    const colors: Record<string, string> = {
      buy: 'var(--primary)',
      rent: 'var(--success)',
      invest: 'var(--warning)'
    }
    return colors[purpose] || 'var(--muted)'
  }

  if (loading) {
    return (
      <div className="page">
        <h1>Property Management</h1>
        <div className="empty">Loading properties…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <h1>Property Management</h1>
        <div className="card" style={{ color: 'var(--danger)' }}>
          Failed to load properties: {error}
          <button className="button" onClick={loadProperties} style={{ marginTop: 12 }}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <h1>Property Management</h1>
      
      {/* Filters */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <input
            type="text"
            className="input"
            placeholder="Search by name or city..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ flex: 1, minWidth: 200 }}
          />
          
          <select
            className="input"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ minWidth: 150 }}
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="pending">Pending</option>
            <option value="sold">Sold</option>
            <option value="rented">Rented</option>
          </select>
        </div>
      </div>

      {/* Properties Table */}
      {filteredProperties.length === 0 ? (
        <div className="empty">
          {searchTerm || statusFilter ? 'No properties match your filters' : 'No properties found'}
        </div>
      ) : (
        <div className="card">
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #f1f5f9' }}>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>ID</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Name</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Location</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Owner</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Purpose</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Status</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Type</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Units</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Price</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Created</th>
                <th style={{ textAlign: 'right', padding: 12, fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredProperties.map((property) => (
                <tr key={property.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: 12 }}>{property.id}</td>
                  <td style={{ padding: 12, fontWeight: 600 }}>{property.name}</td>
                  <td style={{ padding: 12 }}>{property.city || '—'}</td>
                  <td style={{ padding: 12 }}>#{property.owner_id}</td>
                  <td style={{ padding: 12 }}>
                    {property.purpose && (
                      <span style={{ 
                        color: 'white',
                        background: getPurposeBadgeColor(property.purpose),
                        padding: '2px 8px',
                        borderRadius: 4,
                        fontSize: 12,
                        fontWeight: 600
                      }}>
                        {property.purpose.toUpperCase()}
                      </span>
                    )}
                  </td>
                  <td style={{ padding: 12 }}>
                    <span style={{ 
                      color: 'white',
                      background: getStatusBadgeColor(property.status),
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: 12,
                      fontWeight: 600
                    }}>
                      {property.status.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: 12, fontSize: 12 }}>
                    {property.property_type || '—'}
                  </td>
                  <td style={{ padding: 12, fontSize: 12 }}>
                    {property.units_count || '—'}
                  </td>
                  <td style={{ padding: 12, fontSize: 12 }}>
                    {property.price_label || '—'}
                  </td>
                  <td style={{ padding: 12, fontSize: 12 }}>
                    {property.created_at ? new Date(property.created_at).toLocaleDateString() : 'N/A'}
                  </td>
                  <td style={{ padding: 12, textAlign: 'right' }}>
                    <button 
                      className="button muted" 
                      style={{ padding: '4px 8px', fontSize: 12 }}
                      onClick={() => {/* TODO: Implement edit */}}
                    >
                      Edit
                    </button>
                    <button 
                      className="button danger" 
                      style={{ padding: '4px 8px', fontSize: 12, marginLeft: 4 }}
                      onClick={() => handleDeleteProperty(property)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmDialog 
        open={showDeleteConfirm}
        title="Delete Property"
        description={`Are you sure you want to delete ${selectedProperty?.name}? This action cannot be undone.`}
        onConfirm={confirmDelete}
        onCancel={() => {
          setShowDeleteConfirm(false)
          setSelectedProperty(null)
        }}
      />
    </div>
  )
}

export default PropertiesManagement