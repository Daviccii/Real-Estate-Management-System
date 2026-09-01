import React, { useEffect, useState } from 'react'
import { managerService } from '../../services/manager'
import type { ManagerProperty } from '../../services/manager'
import ConfirmDialog from '../../components/ConfirmDialog'
import { useToast } from '../../components/ToastProvider'

const ManagerProperties: React.FC = () => {
  const [properties, setProperties] = useState<ManagerProperty[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedProperty, setSelectedProperty] = useState<ManagerProperty | null>(null)
  const [editForm, setEditForm] = useState({
    name: '',
    city: '',
    status: '',
    address: '',
    property_type: ''
  })
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
      const data = await managerService.getProperties(params)
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

  const handleEditProperty = (property: ManagerProperty) => {
    setSelectedProperty(property)
    setEditForm({
      name: property.name,
      city: property.city || '',
      status: property.status,
      address: property.address || '',
      property_type: property.property_type || ''
    })
    setShowEditModal(true)
  }

  const handlePropertyUpdate = async () => {
    if (!selectedProperty) return
    
    try {
      await managerService.updateProperty(selectedProperty.id, editForm)
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

  if (loading) return <div className="empty">Loading properties…</div>
  if (error) return <div className="empty error">{error}</div>

  return (
    <div className="management-container">
      <div className="management-header">
        <h1>My Properties</h1>
        <p>Manage your assigned properties</p>
      </div>

      {/* Search and Filter */}
      <div className="controls-section">
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Search properties by name or city…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input"
            style={{ flex: 1, minWidth: 200 }}
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="pending">Pending</option>
            <option value="sold">Sold</option>
            <option value="rented">Rented</option>
          </select>
        </div>
      </div>

      {/* Properties Table */}
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Property Name</th>
              <th>Location</th>
              <th>Type</th>
              <th>Status</th>
              <th>Units</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredProperties.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                  No properties found
                </td>
              </tr>
            ) : (
              filteredProperties.map((property) => (
                <tr key={property.id}>
                  <td>
                    <strong>{property.name}</strong>
                  </td>
                  <td>{property.city || property.address || '—'}</td>
                  <td>{property.property_type || '—'}</td>
                  <td>
                    <span className={`badge status-${property.status}`}>
                      {property.status}
                    </span>
                  </td>
                  <td>{property.units_count || 1}</td>
                  <td>
                    <button
                      onClick={() => handleEditProperty(property)}
                      className="button small"
                      style={{ marginRight: 8 }}
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Edit Modal */}
      {showEditModal && selectedProperty && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Edit Property</h2>
              <button onClick={() => setShowEditModal(false)} className="close-button">✕</button>
            </div>
            
            <div className="form-group">
              <label>Property Name</label>
              <input
                type="text"
                value={editForm.name}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                className="input"
              />
            </div>

            <div className="form-group">
              <label>Address</label>
              <input
                type="text"
                value={editForm.address}
                onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
                className="input"
              />
            </div>

            <div className="form-group">
              <label>City</label>
              <input
                type="text"
                value={editForm.city}
                onChange={(e) => setEditForm({ ...editForm, city: e.target.value })}
                className="input"
              />
            </div>

            <div className="form-group">
              <label>Property Type</label>
              <input
                type="text"
                value={editForm.property_type}
                onChange={(e) => setEditForm({ ...editForm, property_type: e.target.value })}
                className="input"
              />
            </div>

            <div className="form-group">
              <label>Status</label>
              <select
                value={editForm.status}
                onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                className="input"
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="pending">Pending</option>
                <option value="sold">Sold</option>
                <option value="rented">Rented</option>
              </select>
            </div>

            <div className="modal-footer">
              <button onClick={() => setShowEditModal(false)} className="button secondary">Cancel</button>
              <button onClick={handlePropertyUpdate} className="button">Save Changes</button>
            </div>
          </div>
        </div>
      )}

      {/* Refresh Button */}
      <div style={{ marginTop: 24, textAlign: 'center' }}>
        <button onClick={loadProperties} className="button" disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh Properties'}
        </button>
      </div>
    </div>
  )
}

export default ManagerProperties
