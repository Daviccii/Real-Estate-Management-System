import React, { useEffect, useState } from 'react'
import { adminService } from '../../services/admin'
import type { AdminInquiry } from '../../services/admin'
import { useToast } from '../../components/ToastProvider'

const InquiriesManagement: React.FC = () => {
  const [inquiries, setInquiries] = useState<AdminInquiry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('')
  const { addToast } = useToast()

  useEffect(() => {
    loadInquiries()
  }, [statusFilter])

  const loadInquiries = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: any = {}
      if (statusFilter) params.status = statusFilter
      const data = await adminService.getInquiries(params)
      setInquiries(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load inquiries')
    } finally {
      setLoading(false)
    }
  }

  const handleStatusUpdate = async (inquiryId: number, newStatus: string) => {
    if (!newStatus) return
    
    try {
      await adminService.updateInquiryStatus(inquiryId, newStatus)
      addToast({ 
        message: 'Inquiry status updated successfully', 
        type: 'success' 
      })
      loadInquiries() // Reload the inquiries list
    } catch (error: any) {
      addToast({ 
        message: error?.message || 'Failed to update inquiry status', 
        type: 'error' 
      })
    }
  }

  const getStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'var(--warning)',
      in_progress: 'var(--primary)',
      resolved: 'var(--success)',
      closed: 'var(--muted)'
    }
    return colors[status] || 'var(--muted)'
  }

  if (loading) {
    return (
      <div className="page">
        <h1>Inquiry Management</h1>
        <div className="empty">Loading inquiries…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <h1>Inquiry Management</h1>
        <div className="card" style={{ color: 'var(--danger)' }}>
          Failed to load inquiries: {error}
          <button className="button" onClick={loadInquiries} style={{ marginTop: 12 }}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <h1>Inquiry Management</h1>
      
      {/* Filters */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="admin-filters">
          <select
            className="input"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ minWidth: 150 }}
          >
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      {/* Inquiries Table */}
      {inquiries.length === 0 ? (
        <div className="empty">
          {statusFilter ? 'No inquiries match your filters' : 'No inquiries found'}
        </div>
      ) : (
        <div className="card admin-table-container">
          <table className="admin-table">
            <thead>
              <tr style={{ borderBottom: '2px solid #f1f5f9' }}>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>ID</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>User ID</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Property ID</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Status</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Created</th>
                <th style={{ textAlign: 'right', padding: 12, fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {inquiries.map((inquiry) => (
                <tr key={inquiry.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td data-label="ID" style={{ padding: 12 }}>#{inquiry.id}</td>
                  <td data-label="User ID" style={{ padding: 12 }}>#{inquiry.user_id}</td>
                  <td data-label="Property ID" style={{ padding: 12 }}>#{inquiry.property_id}</td>
                  <td data-label="Status" style={{ padding: 12 }}>
                    <span style={{ 
                      color: 'white',
                      background: getStatusBadgeColor(inquiry.status),
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: 12,
                      fontWeight: 600
                    }}>
                      {inquiry.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </td>
                  <td data-label="Created" style={{ padding: 12, fontSize: 12 }}>
                    {inquiry.created_at ? new Date(inquiry.created_at).toLocaleDateString() : 'N/A'}
                  </td>
                  <td data-label="Actions" style={{ padding: 12, textAlign: 'right' }}>
                    <select
                      className="input"
                      style={{ padding: '4px 8px', fontSize: 12, minWidth: 100 }}
                      onChange={(e) => handleStatusUpdate(inquiry.id, e.target.value)}
                    >
                      <option value="">Change Status</option>
                      <option value="pending">Pending</option>
                      <option value="in_progress">In Progress</option>
                      <option value="resolved">Resolved</option>
                      <option value="closed">Closed</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default InquiriesManagement