import React, { useEffect, useState } from 'react'
import { unitService } from '../../services/unit'
import type { Unit } from '../../types'
import ConfirmDialog from '../../components/ConfirmDialog'
import { useToast } from '../../components/ToastProvider'

const UnitsManagement: React.FC = () => {
  const [units, setUnits] = useState<Unit[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedUnit, setSelectedUnit] = useState<Unit | null>(null)
  const [editForm, setEditForm] = useState({
    unit_number: '',
    unit_type: '',
    bedrooms: 0,
    bathrooms: 0,
    area: '',
    rent: '',
    status: ''
  })
  const { addToast } = useToast()

  useEffect(() => {
    loadUnits()
  }, [statusFilter])

  const loadUnits = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: any = {}
      if (statusFilter) params.status = statusFilter
      const data = await unitService.list(params)
      setUnits(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load units')
    } finally {
      setLoading(false)
    }
  }

  const filteredUnits = units.filter(unit => {
    const matchesSearch = !searchTerm || 
      unit.unit_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (unit.unit_type && unit.unit_type.toLowerCase().includes(searchTerm.toLowerCase()))
    return matchesSearch
  })

  const handleDeleteUnit = (unit: Unit) => {
    setSelectedUnit(unit)
    setShowDeleteConfirm(true)
  }

  const handleEditUnit = (unit: Unit) => {
    setSelectedUnit(unit)
    setEditForm({
      unit_number: unit.unit_number,
      unit_type: unit.unit_type || '',
      bedrooms: unit.bedrooms || 0,
      bathrooms: unit.bathrooms || 0,
      area: unit.area || '',
      rent: unit.rent || '',
      status: unit.status
    })
    setShowEditModal(true)
  }

  const confirmDelete = async () => {
    if (!selectedUnit) return
    
    try {
      await unitService.delete(selectedUnit.id)
      addToast({ message: 'Unit deleted successfully', type: 'success' })
      setShowDeleteConfirm(false)
      setSelectedUnit(null)
      loadUnits()
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to delete unit', type: 'error' })
    }
  }

  const handleUnitUpdate = async () => {
    if (!selectedUnit) return
    
    try {
      await unitService.update(selectedUnit.id, editForm)
      addToast({ message: 'Unit updated successfully', type: 'success' })
      setShowEditModal(false)
      setSelectedUnit(null)
      loadUnits()
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to update unit', type: 'error' })
    }
  }

  const getStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      available: 'var(--success)',
      occupied: 'var(--primary)',
      reserved: 'var(--warning)',
      maintenance: 'var(--danger)'
    }
    return colors[status] || 'var(--muted)'
  }

  if (loading) {
    return (
      <div className="page">
        <h1>Unit Management</h1>
        <div className="empty">Loading units…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <h1>Unit Management</h1>
        <div className="card" style={{ color: 'var(--danger)' }}>
          Failed to load units: {error}
          <button className="button" onClick={loadUnits} style={{ marginTop: 12 }}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <h1>Unit Management</h1>
      
      {/* Filters */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="admin-filters">
          <input
            type="text"
            className="input"
            placeholder="Search by unit number or type..."
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
            <option value="available">Available</option>
            <option value="occupied">Occupied</option>
            <option value="reserved">Reserved</option>
            <option value="maintenance">Maintenance</option>
          </select>
        </div>
      </div>

      {/* Units Table */}
      {filteredUnits.length === 0 ? (
        <div className="empty">
          {searchTerm || statusFilter ? 'No units match your filters' : 'No units found'}
        </div>
      ) : (
        <div className="card admin-table-container">
          <table className="admin-table">
            <thead>
              <tr style={{ borderBottom: '2px solid #f1f5f9' }}>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>ID</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Unit Number</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Type</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Details</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Rent</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Status</th>
                <th style={{ textAlign: 'right', padding: 12, fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUnits.map((unit) => (
                <tr key={unit.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td data-label="ID" style={{ padding: 12 }}>{unit.id}</td>
                  <td data-label="Unit Number" style={{ padding: 12, fontWeight: 600 }}>{unit.unit_number}</td>
                  <td data-label="Type" style={{ padding: 12 }}>{unit.unit_type || '—'}</td>
                  <td data-label="Details" style={{ padding: 12 }}>
                    <div>
                      {unit.bedrooms !== null && `${unit.bedrooms} bed`}
                      {unit.bedrooms !== null && unit.bathrooms !== null && ' • '}
                      {unit.bathrooms !== null && `${unit.bathrooms} bath`}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--muted)' }}>{unit.area || '—'}</div>
                  </td>
                  <td data-label="Rent" style={{ padding: 12 }}>{unit.rent || '—'}</td>
                  <td data-label="Status" style={{ padding: 12 }}>
                    <span style={{ 
                      color: 'white',
                      background: getStatusBadgeColor(unit.status),
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: 12,
                      fontWeight: 600
                    }}>
                      {unit.status.toUpperCase()}
                    </span>
                  </td>
                  <td data-label="Actions" style={{ padding: 12, textAlign: 'right' }}>
                    <div className="admin-actions">
                      <button 
                        className="button muted" 
                        style={{ padding: '4px 8px', fontSize: 12 }}
                        onClick={() => handleEditUnit(unit)}
                      >
                        Edit
                      </button>
                      <button 
                        className="button danger" 
                        style={{ padding: '4px 8px', fontSize: 12 }}
                        onClick={() => handleDeleteUnit(unit)}
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
        title="Delete Unit"
        description={`Are you sure you want to delete unit ${selectedUnit?.unit_number}? This action cannot be undone.`}
        onConfirm={confirmDelete}
        onCancel={() => {
          setShowDeleteConfirm(false)
          setSelectedUnit(null)
        }}
      />

      <ConfirmDialog 
        open={showEditModal}
        title="Edit Unit"
        description={`Edit ${selectedUnit?.unit_number}`}
        onConfirm={handleUnitUpdate}
        onCancel={() => {
          setShowEditModal(false)
          setSelectedUnit(null)
        }}
      >
        <div style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Unit Number:</label>
            <input
              className="input"
              value={editForm.unit_number}
              onChange={(e) => setEditForm({...editForm, unit_number: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Unit Type:</label>
            <input
              className="input"
              value={editForm.unit_type}
              onChange={(e) => setEditForm({...editForm, unit_type: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Bedrooms:</label>
            <input
              type="number"
              className="input"
              value={editForm.bedrooms}
              onChange={(e) => setEditForm({...editForm, bedrooms: parseInt(e.target.value) || 0})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Bathrooms:</label>
            <input
              type="number"
              className="input"
              value={editForm.bathrooms}
              onChange={(e) => setEditForm({...editForm, bathrooms: parseInt(e.target.value) || 0})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Area:</label>
            <input
              className="input"
              value={editForm.area}
              onChange={(e) => setEditForm({...editForm, area: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Rent:</label>
            <input
              className="input"
              value={editForm.rent}
              onChange={(e) => setEditForm({...editForm, rent: e.target.value})}
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
              <option value="available">Available</option>
              <option value="occupied">Occupied</option>
              <option value="reserved">Reserved</option>
              <option value="maintenance">Maintenance</option>
            </select>
          </div>
        </div>
      </ConfirmDialog>
    </div>
  )
}

export default UnitsManagement