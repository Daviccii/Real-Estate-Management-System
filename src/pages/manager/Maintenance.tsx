import React, { useEffect, useState } from 'react'
import { managerService } from '../../services/manager'
import type { ManagerMaintenance } from '../../services/manager'
import { useToast } from '../../components/ToastProvider'

const ManagerMaintenance: React.FC = () => {
  const [maintenance, setMaintenance] = useState<ManagerMaintenance[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [selectedMaintenance, setSelectedMaintenance] = useState<ManagerMaintenance | null>(null)
  const [showStatusModal, setShowStatusModal] = useState(false)
  const [newStatus, setNewStatus] = useState('')
  const { addToast } = useToast()

  useEffect(() => {
    loadMaintenance()
  }, [statusFilter])

  const loadMaintenance = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: any = {}
      if (statusFilter) params.status = statusFilter
      const data = await managerService.getMaintenance(params)
      setMaintenance(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load maintenance requests')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateStatus = async () => {
    if (!selectedMaintenance) return
    
    try {
      await managerService.updateMaintenanceStatus(selectedMaintenance.id, newStatus)
      addToast({ 
        message: 'Maintenance status updated successfully', 
        type: 'success' 
      })
      setShowStatusModal(false)
      setSelectedMaintenance(null)
      setNewStatus('')
      loadMaintenance()
    } catch (error: any) {
      addToast({ 
        message: error?.message || 'Failed to update maintenance status', 
        type: 'error' 
      })
    }
  }

  if (loading) return <div className="empty">Loading maintenance requests…</div>
  if (error) return <div className="empty error">{error}</div>

  return (
    <div className="management-container">
      <div className="management-header">
        <h1>Maintenance Requests</h1>
        <p>Track and manage maintenance issues</p>
      </div>

      <div className="controls-section">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="input"
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Property ID</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {maintenance.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                  No maintenance requests found
                </td>
              </tr>
            ) : (
              maintenance.map((item) => (
                <tr key={item.id}>
                  <td>
                    <strong>{item.title}</strong>
                    {item.description && (
                      <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                        {item.description.substring(0, 50)}...
                      </div>
                    )}
                  </td>
                  <td>
                    <span className={`badge priority-${item.priority}`}>
                      {item.priority || 'Normal'}
                    </span>
                  </td>
                  <td>
                    <span className={`badge status-${item.status}`}>
                      {item.status}
                    </span>
                  </td>
                  <td>{item.property_id}</td>
                  <td>
                    {item.created_at ? new Date(item.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td>
                    <button
                      onClick={() => {
                        setSelectedMaintenance(item)
                        setNewStatus(item.status)
                        setShowStatusModal(true)
                      }}
                      className="button small"
                    >
                      Update Status
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Status Update Modal */}
      {showStatusModal && selectedMaintenance && (
        <div className="modal-overlay" onClick={() => setShowStatusModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Update Maintenance Status</h2>
              <button onClick={() => setShowStatusModal(false)} className="close-button">✕</button>
            </div>
            
            <div className="form-group">
              <label>Title</label>
              <input
                type="text"
                value={selectedMaintenance.title}
                disabled
                className="input"
              />
            </div>

            <div className="form-group">
              <label>New Status</label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                className="input"
              >
                <option value="open">Open</option>
                <option value="in_progress">In Progress</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
            </div>

            <div className="modal-footer">
              <button onClick={() => setShowStatusModal(false)} className="button secondary">Cancel</button>
              <button onClick={handleUpdateStatus} className="button">Update Status</button>
            </div>
          </div>
        </div>
      )}

      <div style={{ marginTop: 24, textAlign: 'center' }}>
        <button onClick={loadMaintenance} className="button" disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh Maintenance'}
        </button>
      </div>
    </div>
  )
}

export default ManagerMaintenance
