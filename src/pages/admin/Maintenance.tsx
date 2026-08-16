import React, { useEffect, useState } from 'react'
import { maintenanceService } from '../../services/maintenance'
import type { Maintenance } from '../../types'
import ConfirmDialog from '../../components/ConfirmDialog'
import { useToast } from '../../components/ToastProvider'

const MaintenanceManagement: React.FC = () => {
  const [requests, setRequests] = useState<Maintenance[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [showResolveModal, setShowResolveModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedRequest, setSelectedRequest] = useState<Maintenance | null>(null)
  const [assignForm, setAssignForm] = useState({ assigned_manager_id: '', notes: '' })
  const [resolveForm, setResolveForm] = useState({ resolution_notes: '', cost: '' })
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    category: '',
    priority: '',
    status: '',
    cost: '',
    notes: ''
  })
  const { addToast } = useToast()

  useEffect(() => {
    loadRequests()
  }, [statusFilter, priorityFilter])

  const loadRequests = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: any = {}
      if (statusFilter) params.status = statusFilter
      if (priorityFilter) params.priority = priorityFilter
      const data = await maintenanceService.list(params)
      setRequests(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load maintenance requests')
    } finally {
      setLoading(false)
    }
  }

  const filteredRequests = requests.filter(request => {
    const matchesSearch = !searchTerm || 
      request.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (request.description && request.description.toLowerCase().includes(searchTerm.toLowerCase()))
    return matchesSearch
  })

  const handleDeleteRequest = (request: Maintenance) => {
    setSelectedRequest(request)
    setShowDeleteConfirm(true)
  }

  const handleAssignRequest = (request: Maintenance) => {
    setSelectedRequest(request)
    setAssignForm({ assigned_manager_id: '', notes: '' })
    setShowAssignModal(true)
  }

  const handleResolveRequest = (request: Maintenance) => {
    setSelectedRequest(request)
    setResolveForm({ resolution_notes: '', cost: '' })
    setShowResolveModal(true)
  }

  const handleEditRequest = (request: Maintenance) => {
    setSelectedRequest(request)
    setEditForm({
      title: request.title,
      description: request.description || '',
      category: request.category || '',
      priority: request.priority,
      status: request.status,
      cost: request.cost || '',
      notes: request.notes || ''
    })
    setShowEditModal(true)
  }

  const confirmDelete = async () => {
    if (!selectedRequest) return
    
    try {
      await maintenanceService.delete(selectedRequest.id)
      addToast({ message: 'Maintenance request deleted successfully', type: 'success' })
      setShowDeleteConfirm(false)
      setSelectedRequest(null)
      loadRequests()
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to delete maintenance request', type: 'error' })
    }
  }

  const handleAssign = async () => {
    if (!selectedRequest) return
    
    try {
      await maintenanceService.assign(selectedRequest.id, assignForm)
      addToast({ message: 'Maintenance request assigned successfully', type: 'success' })
      setShowAssignModal(false)
      setSelectedRequest(null)
      loadRequests()
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to assign maintenance request', type: 'error' })
    }
  }

  const handleResolve = async () => {
    if (!selectedRequest) return
    
    try {
      await maintenanceService.resolve(selectedRequest.id, resolveForm)
      addToast({ message: 'Maintenance request resolved successfully', type: 'success' })
      setShowResolveModal(false)
      setSelectedRequest(null)
      loadRequests()
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to resolve maintenance request', type: 'error' })
    }
  }

  const handleRequestUpdate = async () => {
    if (!selectedRequest) return
    
    try {
      await maintenanceService.update(selectedRequest.id, editForm)
      addToast({ message: 'Maintenance request updated successfully', type: 'success' })
      setShowEditModal(false)
      setSelectedRequest(null)
      loadRequests()
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to update maintenance request', type: 'error' })
    }
  }

  const getStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'var(--warning)',
      assigned: 'var(--primary)',
      in_progress: 'var(--warning)',
      completed: 'var(--success)',
      cancelled: 'var(--muted)'
    }
    return colors[status] || 'var(--muted)'
  }

  const getPriorityBadgeColor = (priority: string) => {
    const colors: Record<string, string> = {
      low: 'var(--muted)',
      medium: 'var(--primary)',
      high: 'var(--warning)',
      urgent: 'var(--danger)'
    }
    return colors[priority] || 'var(--muted)'
  }

  if (loading) {
    return (
      <div className="page">
        <h1>Maintenance Management</h1>
        <div className="empty">Loading maintenance requests…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <h1>Maintenance Management</h1>
        <div className="card" style={{ color: 'var(--danger)' }}>
          Failed to load maintenance requests: {error}
          <button className="button" onClick={loadRequests} style={{ marginTop: 12 }}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <h1>Maintenance Management</h1>
      
      {/* Filters */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="admin-filters">
          <input
            type="text"
            className="input"
            placeholder="Search requests..."
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
            <option value="pending">Pending</option>
            <option value="assigned">Assigned</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          
          <select
            className="input"
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            style={{ minWidth: 150 }}
          >
            <option value="">All Priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
        </div>
      </div>

      {/* Requests Table */}
      {filteredRequests.length === 0 ? (
        <div className="empty">
          {searchTerm || statusFilter || priorityFilter ? 'No requests match your filters' : 'No maintenance requests found'}
        </div>
      ) : (
        <div className="card admin-table-container">
          <table className="admin-table">
            <thead>
              <tr style={{ borderBottom: '2px solid #f1f5f9' }}>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>ID</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Title</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Property</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Category</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Priority</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Status</th>
                <th style={{ textAlign: 'right', padding: 12, fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredRequests.map((request) => (
                <tr key={request.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td data-label="ID" style={{ padding: 12 }}>#{request.id}</td>
                  <td data-label="Title" style={{ padding: 12 }}>
                    <div style={{ fontWeight: 600 }}>{request.title}</div>
                    {request.description && (
                      <div style={{ fontSize: 12, color: 'var(--muted)' }}>{request.description}</div>
                    )}
                  </td>
                  <td data-label="Property" style={{ padding: 12 }}>#{request.property_id}</td>
                  <td data-label="Category" style={{ padding: 12 }}>{request.category || '—'}</td>
                  <td data-label="Priority" style={{ padding: 12 }}>
                    <span style={{ 
                      color: 'white',
                      background: getPriorityBadgeColor(request.priority),
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: 12,
                      fontWeight: 600
                    }}>
                      {request.priority.toUpperCase()}
                    </span>
                  </td>
                  <td data-label="Status" style={{ padding: 12 }}>
                    <span style={{ 
                      color: 'white',
                      background: getStatusBadgeColor(request.status),
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: 12,
                      fontWeight: 600
                    }}>
                      {request.status.toUpperCase()}
                    </span>
                  </td>
                  <td data-label="Actions" style={{ padding: 12, textAlign: 'right' }}>
                    <div className="admin-actions">
                      <button 
                        className="button muted" 
                        style={{ padding: '4px 8px', fontSize: 12 }}
                        onClick={() => handleEditRequest(request)}
                      >
                        Edit
                      </button>
                      {request.status === 'pending' && (
                        <button 
                          className="button muted" 
                          style={{ padding: '4px 8px', fontSize: 12 }}
                          onClick={() => handleAssignRequest(request)}
                        >
                          Assign
                        </button>
                      )}
                      {(request.status === 'assigned' || request.status === 'in_progress') && (
                        <button 
                          className="button muted" 
                          style={{ padding: '4px 8px', fontSize: 12 }}
                          onClick={() => handleResolveRequest(request)}
                        >
                          Resolve
                        </button>
                      )}
                      <button 
                        className="button danger" 
                        style={{ padding: '4px 8px', fontSize: 12 }}
                        onClick={() => handleDeleteRequest(request)}
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
        title="Delete Maintenance Request"
        description={`Are you sure you want to delete "${selectedRequest?.title}"? This action cannot be undone.`}
        onConfirm={confirmDelete}
        onCancel={() => {
          setShowDeleteConfirm(false)
          setSelectedRequest(null)
        }}
      />

      <ConfirmDialog 
        open={showAssignModal}
        title="Assign Maintenance Request"
        description={`Assign "${selectedRequest?.title}"`}
        onConfirm={handleAssign}
        onCancel={() => {
          setShowAssignModal(false)
          setSelectedRequest(null)
        }}
      >
        <div style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Assign to Manager ID:</label>
            <input
              type="number"
              className="input"
              value={assignForm.assigned_manager_id}
              onChange={(e) => setAssignForm({...assignForm, assigned_manager_id: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Notes (optional):</label>
            <textarea
              className="input"
              value={assignForm.notes}
              onChange={(e) => setAssignForm({...assignForm, notes: e.target.value})}
              style={{ width: '100%' }}
              rows={3}
            />
          </div>
        </div>
      </ConfirmDialog>

      <ConfirmDialog 
        open={showResolveModal}
        title="Resolve Maintenance Request"
        description={`Resolve "${selectedRequest?.title}"`}
        onConfirm={handleResolve}
        onCancel={() => {
          setShowResolveModal(false)
          setSelectedRequest(null)
        }}
      >
        <div style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Resolution Notes:</label>
            <textarea
              className="input"
              value={resolveForm.resolution_notes}
              onChange={(e) => setResolveForm({...resolveForm, resolution_notes: e.target.value})}
              style={{ width: '100%' }}
              rows={3}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Cost (optional):</label>
            <input
              className="input"
              value={resolveForm.cost}
              onChange={(e) => setResolveForm({...resolveForm, cost: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
        </div>
      </ConfirmDialog>

      <ConfirmDialog 
        open={showEditModal}
        title="Edit Maintenance Request"
        description={`Edit "${selectedRequest?.title}"`}
        onConfirm={handleRequestUpdate}
        onCancel={() => {
          setShowEditModal(false)
          setSelectedRequest(null)
        }}
      >
        <div style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Title:</label>
            <input
              className="input"
              value={editForm.title}
              onChange={(e) => setEditForm({...editForm, title: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Description:</label>
            <textarea
              className="input"
              value={editForm.description}
              onChange={(e) => setEditForm({...editForm, description: e.target.value})}
              style={{ width: '100%' }}
              rows={3}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Category:</label>
            <input
              className="input"
              value={editForm.category}
              onChange={(e) => setEditForm({...editForm, category: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Priority:</label>
            <select
              className="input"
              value={editForm.priority}
              onChange={(e) => setEditForm({...editForm, priority: e.target.value})}
              style={{ width: '100%' }}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Status:</label>
            <select
              className="input"
              value={editForm.status}
              onChange={(e) => setEditForm({...editForm, status: e.target.value})}
              style={{ width: '100%' }}
            >
              <option value="pending">Pending</option>
              <option value="assigned">Assigned</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Cost (optional):</label>
            <input
              className="input"
              value={editForm.cost}
              onChange={(e) => setEditForm({...editForm, cost: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Notes:</label>
            <textarea
              className="input"
              value={editForm.notes}
              onChange={(e) => setEditForm({...editForm, notes: e.target.value})}
              style={{ width: '100%' }}
              rows={3}
            />
          </div>
        </div>
      </ConfirmDialog>
    </div>
  )
}

export default MaintenanceManagement