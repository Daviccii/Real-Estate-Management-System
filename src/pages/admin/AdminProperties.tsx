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
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedProperty, setSelectedProperty] = useState<AdminProperty | null>(null)
  const [editForm, setEditForm] = useState({
    name: '',
    city: '',
    status: '',
    purpose: '',
    property_type: '',
    price_label: ''
  })
  const [reassignForm, setReassignForm] = useState({ owner_id: '', manager_id: '' })
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

  const handleEditProperty = (property: AdminProperty) => {
    setSelectedProperty(property)
    setEditForm({
      name: property.name,
      city: property.city || '',
      status: property.status,
      purpose: property.purpose || '',
      property_type: property.property_type || '',
      price_label: property.price_label || ''
    })
    setReassignForm({ owner_id: String(property.owner_id), manager_id: '' })
    setShowEditModal(true)
  }

  const handlePropertyUpdate = async () => {
    if (!selectedProperty) return
    
    try {
      await adminService.updateProperty(selectedProperty.id, editForm)

      // Reassignment is a separate call/endpoint (owner_id/manager_id aren't
      // part of the regular update schema — see admin.py's PropertyReassign).
      // Only sent if the admin actually changed one of these fields, to
      // avoid unnecessary requests or clobbering manager_id with an empty
      // value when only the owner was being changed.
      const ownerChanged = reassignForm.owner_id && Number(reassignForm.owner_id) !== selectedProperty.owner_id
      const managerProvided = reassignForm.manager_id.trim() !== ''
      if (ownerChanged || managerProvided) {
        const reassignPayload: { owner_id?: number; manager_id?: number } = {}
        if (ownerChanged) reassignPayload.owner_id = Number(reassignForm.owner_id)
        if (managerProvided) reassignPayload.manager_id = Number(reassignForm.manager_id)
        await adminService.reassignProperty(selectedProperty.id, reassignPayload)
      }

      addToast({ 
        message: 'Property updated successfully', 
        type: 'success' 
      })
      setShowEditModal(false)
      setSelectedProperty(null)
      loadProperties()
    } catch (error: any) {
      addToast({ 
        message: error?.message || 'Failed to update property', 
        type: 'error' 
      })
    }
  }

  const confirmDelete = async () => {
    if (!selectedProperty) return
    
    try {
      await adminService.deleteProperty(selectedProperty.id)
      addToast({ 
        message: 'Property deleted successfully', 
        type: 'success' 
      })
      setShowDeleteConfirm(false)
      setSelectedProperty(null)
      loadProperties() // Reload the properties list
    } catch (error: any) {
      addToast({ 
        message: error?.message || 'Failed to delete property', 
        type: 'error' 
      })
    }
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

  // FIX: 'buy' used var(--primary), which renders near-invisible against
  // this table's white background — confirmed via screen recording that
  // Meridian Residences/Nova Heights/Cedar Park (all purpose=buy) showed no
  // visible badge at all while rent/invest rendered fine. Explicit hex
  // values instead of depending on a CSS var whose resolved value wasn't
  // verified against this table's background.
  const getPurposeBadgeColor = (purpose: string | null) => {
    if (!purpose) return '#64748b'
    const colors: Record<string, string> = {
      buy: '#1d3fd6',
      rent: '#16a34a',
      invest: '#d97706'
    }
    return colors[purpose] || '#64748b'
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
        <div className="admin-filters">
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
        <div className="card admin-table-container">
          <table className="admin-table">
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
                  <td data-label="ID" style={{ padding: 12 }}>{property.id}</td>
                  <td data-label="Name" style={{ padding: 12, fontWeight: 600 }}>{property.name}</td>
                  <td data-label="Location" style={{ padding: 12 }}>{property.city || '—'}</td>
                  <td data-label="Owner" style={{ padding: 12 }}>#{property.owner_id}</td>
                  <td data-label="Purpose" style={{ padding: 12 }}>
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
                  <td data-label="Status" style={{ padding: 12 }}>
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
                  <td data-label="Type" style={{ padding: 12, fontSize: 12 }}>
                    {property.property_type || '—'}
                  </td>
                  <td data-label="Units" style={{ padding: 12, fontSize: 12 }}>
                    {property.units_count || '—'}
                  </td>
                  <td data-label="Price" style={{ padding: 12, fontSize: 12 }}>
                    {property.price_label || '—'}
                  </td>
                  <td data-label="Created" style={{ padding: 12, fontSize: 12 }}>
                    {property.created_at ? new Date(property.created_at).toLocaleDateString() : 'N/A'}
                  </td>
                  <td data-label="Actions" style={{ padding: 12, textAlign: 'right' }}>
                    <div className="admin-actions">
                      <button 
                        className="button muted" 
                        style={{ padding: '4px 8px', fontSize: 12 }}
                        onClick={() => handleEditProperty(property)}
                      >
                        Edit
                      </button>
                      <button 
                        className="button danger" 
                        style={{ padding: '4px 8px', fontSize: 12 }}
                        onClick={() => handleDeleteProperty(property)}
                      >
                        Delete
                      </button>
                    </div>
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

      <ConfirmDialog 
        open={showEditModal}
        title="Edit Property"
        description={`Edit ${selectedProperty?.name}`}
        onConfirm={handlePropertyUpdate}
        onCancel={() => {
          setShowEditModal(false)
          setSelectedProperty(null)
        }}
      >
        <div style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Name:</label>
            <input
              className="input"
              value={editForm.name}
              onChange={(e) => setEditForm({...editForm, name: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>City:</label>
            <input
              className="input"
              value={editForm.city}
              onChange={(e) => setEditForm({...editForm, city: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Status:</label>
            <select
              className="input"
              value={editForm.status}
              onChange={(e) => setEditForm({...editForm, status: e.target.value})}
              style={{ width: '100%' }}
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="pending">Pending</option>
              <option value="sold">Sold</option>
              <option value="rented">Rented</option>
            </select>
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Purpose:</label>
            <select
              className="input"
              value={editForm.purpose}
              onChange={(e) => setEditForm({...editForm, purpose: e.target.value})}
              style={{ width: '100%' }}
            >
              <option value="">Select purpose</option>
              <option value="buy">Buy</option>
              <option value="rent">Rent</option>
              <option value="invest">Invest</option>
            </select>
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Property Type:</label>
            <input
              className="input"
              value={editForm.property_type}
              onChange={(e) => setEditForm({...editForm, property_type: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Price Label:</label>
            <input
              className="input"
              value={editForm.price_label}
              onChange={(e) => setEditForm({...editForm, price_label: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>

          <hr style={{ margin: '16px 0', border: 'none', borderTop: '1px solid #f1f5f9' }} />
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 12 }}>
            Reassignment — enter a user ID. Leave manager blank to leave it unchanged.
          </p>
          <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Owner ID:</label>
              <input
                type="number"
                className="input"
                value={reassignForm.owner_id}
                onChange={(e) => setReassignForm({...reassignForm, owner_id: e.target.value})}
                style={{ width: '100%' }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Manager ID:</label>
              <input
                type="number"
                className="input"
                placeholder="(unassigned)"
                value={reassignForm.manager_id}
                onChange={(e) => setReassignForm({...reassignForm, manager_id: e.target.value})}
                style={{ width: '100%' }}
              />
            </div>
          </div>
        </div>
      </ConfirmDialog>
    </div>
  )
}

export default PropertiesManagement