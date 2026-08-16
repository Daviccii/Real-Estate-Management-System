import React, { useEffect, useState } from 'react'
import { leaseService } from '../../services/lease'
import type { Lease } from '../../types'
import ConfirmDialog from '../../components/ConfirmDialog'
import { useToast } from '../../components/ToastProvider'

const LeasesManagement: React.FC = () => {
  const [leases, setLeases] = useState<Lease[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showRenewModal, setShowRenewModal] = useState(false)
  const [showTerminateModal, setShowTerminateModal] = useState(false)
  const [selectedLease, setSelectedLease] = useState<Lease | null>(null)
  const [renewForm, setRenewForm] = useState({ new_end_date: '', new_rent_amount: '', notes: '' })
  const [terminateForm, setTerminateForm] = useState({ termination_date: '', reason: '', notes: '' })
  const { addToast } = useToast()

  useEffect(() => {
    loadLeases()
  }, [statusFilter])

  const loadLeases = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: any = {}
      if (statusFilter) params.status = statusFilter
      const data = await leaseService.list(params)
      setLeases(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load leases')
    } finally {
      setLoading(false)
    }
  }

  const filteredLeases = leases.filter(lease => {
    const matchesSearch = !searchTerm || 
      lease.id.toString().includes(searchTerm)
    return matchesSearch
  })

  const handleDeleteLease = (lease: Lease) => {
    setSelectedLease(lease)
    setShowDeleteConfirm(true)
  }

  const handleRenewLease = (lease: Lease) => {
    setSelectedLease(lease)
    setRenewForm({ new_end_date: '', new_rent_amount: '', notes: '' })
    setShowRenewModal(true)
  }

  const handleTerminateLease = (lease: Lease) => {
    setSelectedLease(lease)
    setTerminateForm({ termination_date: '', reason: '', notes: '' })
    setShowTerminateModal(true)
  }

  const confirmDelete = async () => {
    if (!selectedLease) return
    
    try {
      await leaseService.delete(selectedLease.id)
      addToast({ message: 'Lease deleted successfully', type: 'success' })
      setShowDeleteConfirm(false)
      setSelectedLease(null)
      loadLeases()
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to delete lease', type: 'error' })
    }
  }

  const handleRenew = async () => {
    if (!selectedLease) return
    
    try {
      await leaseService.renew(selectedLease.id, renewForm)
      addToast({ message: 'Lease renewed successfully', type: 'success' })
      setShowRenewModal(false)
      setSelectedLease(null)
      loadLeases()
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to renew lease', type: 'error' })
    }
  }

  const handleTerminate = async () => {
    if (!selectedLease) return
    
    try {
      await leaseService.terminate(selectedLease.id, terminateForm)
      addToast({ message: 'Lease terminated successfully', type: 'success' })
      setShowTerminateModal(false)
      setSelectedLease(null)
      loadLeases()
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to terminate lease', type: 'error' })
    }
  }

  const getStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'var(--success)',
      draft: 'var(--muted)',
      terminated: 'var(--danger)',
      renewed: 'var(--primary)',
      expired: 'var(--warning)'
    }
    return colors[status] || 'var(--muted)'
  }

  if (loading) {
    return (
      <div className="page">
        <h1>Lease Management</h1>
        <div className="empty">Loading leases…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <h1>Lease Management</h1>
        <div className="card" style={{ color: 'var(--danger)' }}>
          Failed to load leases: {error}
          <button className="button" onClick={loadLeases} style={{ marginTop: 12 }}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <h1>Lease Management</h1>
      
      {/* Filters */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="admin-filters">
          <input
            type="text"
            className="input"
            placeholder="Search leases..."
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
            <option value="draft">Draft</option>
            <option value="terminated">Terminated</option>
            <option value="renewed">Renewed</option>
            <option value="expired">Expired</option>
          </select>
        </div>
      </div>

      {/* Leases Table */}
      {filteredLeases.length === 0 ? (
        <div className="empty">
          {searchTerm || statusFilter ? 'No leases match your filters' : 'No leases found'}
        </div>
      ) : (
        <div className="card admin-table-container">
          <table className="admin-table">
            <thead>
              <tr style={{ borderBottom: '2px solid #f1f5f9' }}>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>ID</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Property</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Unit</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Period</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Rent</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Status</th>
                <th style={{ textAlign: 'right', padding: 12, fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredLeases.map((lease) => (
                <tr key={lease.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td data-label="ID" style={{ padding: 12 }}>#{lease.id}</td>
                  <td data-label="Property" style={{ padding: 12 }}>#{lease.property_id}</td>
                  <td data-label="Unit" style={{ padding: 12 }}>#{lease.unit_id}</td>
                  <td data-label="Period" style={{ padding: 12 }}>
                    {new Date(lease.start_date).toLocaleDateString()} - {new Date(lease.end_date).toLocaleDateString()}
                  </td>
                  <td data-label="Rent" style={{ padding: 12 }}>{lease.rent_amount}</td>
                  <td data-label="Status" style={{ padding: 12 }}>
                    <span style={{ 
                      color: 'white',
                      background: getStatusBadgeColor(lease.status),
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: 12,
                      fontWeight: 600
                    }}>
                      {lease.status.toUpperCase()}
                    </span>
                  </td>
                  <td data-label="Actions" style={{ padding: 12, textAlign: 'right' }}>
                    <div className="admin-actions">
                      {lease.status === 'active' && (
                        <>
                          <button 
                            className="button muted" 
                            style={{ padding: '4px 8px', fontSize: 12 }}
                            onClick={() => handleRenewLease(lease)}
                          >
                            Renew
                          </button>
                          <button 
                            className="button danger" 
                            style={{ padding: '4px 8px', fontSize: 12 }}
                            onClick={() => handleTerminateLease(lease)}
                          >
                            Terminate
                          </button>
                        </>
                      )}
                      <button 
                        className="button danger" 
                        style={{ padding: '4px 8px', fontSize: 12 }}
                        onClick={() => handleDeleteLease(lease)}
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
        title="Delete Lease"
        description={`Are you sure you want to delete lease #${selectedLease?.id}? This action cannot be undone.`}
        onConfirm={confirmDelete}
        onCancel={() => {
          setShowDeleteConfirm(false)
          setSelectedLease(null)
        }}
      />

      <ConfirmDialog 
        open={showRenewModal}
        title="Renew Lease"
        description={`Renew lease #${selectedLease?.id}`}
        onConfirm={handleRenew}
        onCancel={() => {
          setShowRenewModal(false)
          setSelectedLease(null)
        }}
      >
        <div style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>New End Date:</label>
            <input
              type="date"
              className="input"
              value={renewForm.new_end_date}
              onChange={(e) => setRenewForm({...renewForm, new_end_date: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>New Rent Amount (optional):</label>
            <input
              className="input"
              value={renewForm.new_rent_amount}
              onChange={(e) => setRenewForm({...renewForm, new_rent_amount: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Notes (optional):</label>
            <textarea
              className="input"
              value={renewForm.notes}
              onChange={(e) => setRenewForm({...renewForm, notes: e.target.value})}
              style={{ width: '100%' }}
              rows={3}
            />
          </div>
        </div>
      </ConfirmDialog>

      <ConfirmDialog 
        open={showTerminateModal}
        title="Terminate Lease"
        description={`Terminate lease #${selectedLease?.id}`}
        onConfirm={handleTerminate}
        onCancel={() => {
          setShowTerminateModal(false)
          setSelectedLease(null)
        }}
      >
        <div style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Termination Date:</label>
            <input
              type="date"
              className="input"
              value={terminateForm.termination_date}
              onChange={(e) => setTerminateForm({...terminateForm, termination_date: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Reason (optional):</label>
            <input
              className="input"
              value={terminateForm.reason}
              onChange={(e) => setTerminateForm({...terminateForm, reason: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Notes (optional):</label>
            <textarea
              className="input"
              value={terminateForm.notes}
              onChange={(e) => setTerminateForm({...terminateForm, notes: e.target.value})}
              style={{ width: '100%' }}
              rows={3}
            />
          </div>
        </div>
      </ConfirmDialog>
    </div>
  )
}

export default LeasesManagement