import React, { useEffect, useState } from 'react'
import { paymentService } from '../../services/payment'
import type { Payment } from '../../types'
import ConfirmDialog from '../../components/ConfirmDialog'
import { useToast } from '../../components/ToastProvider'

const PaymentsManagement: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showRecordModal, setShowRecordModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null)
  const [recordForm, setRecordForm] = useState({
    tenant_id: '',
    lease_id: '',
    property_id: '',
    unit_id: '',
    amount: '',
    due_date: '',
    payment_type: '',
    payment_method: '',
    status: 'pending',
    reference: '',
    notes: ''
  })
  const [editForm, setEditForm] = useState({
    amount: '',
    payment_date: '',
    payment_method: '',
    status: '',
    reference: '',
    notes: ''
  })
  const { addToast } = useToast()

  useEffect(() => {
    loadPayments()
  }, [statusFilter])

  const loadPayments = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: any = {}
      if (statusFilter) params.status = statusFilter
      const data = await paymentService.list(params)
      setPayments(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load payments')
    } finally {
      setLoading(false)
    }
  }

  const filteredPayments = payments.filter(payment => {
    const matchesSearch = !searchTerm || 
      payment.id.toString().includes(searchTerm) ||
      (payment.reference && payment.reference.toLowerCase().includes(searchTerm.toLowerCase()))
    return matchesSearch
  })

  const handleDeletePayment = (payment: Payment) => {
    setSelectedPayment(payment)
    setShowDeleteConfirm(true)
  }

  const handleRecordPayment = () => {
    setRecordForm({
      tenant_id: '',
      lease_id: '',
      property_id: '',
      unit_id: '',
      amount: '',
      due_date: '',
      payment_type: '',
      payment_method: '',
      status: 'pending',
      reference: '',
      notes: ''
    })
    setShowRecordModal(true)
  }

  const handleEditPayment = (payment: Payment) => {
    setSelectedPayment(payment)
    setEditForm({
      amount: payment.amount,
      payment_date: payment.payment_date || '',
      payment_method: payment.payment_method || '',
      status: payment.status,
      reference: payment.reference || '',
      notes: payment.notes || ''
    })
    setShowEditModal(true)
  }

  const confirmDelete = async () => {
    if (!selectedPayment) return
    
    try {
      await paymentService.delete(selectedPayment.id)
      addToast({ message: 'Payment deleted successfully', type: 'success' })
      setShowDeleteConfirm(false)
      setSelectedPayment(null)
      loadPayments()
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to delete payment', type: 'error' })
    }
  }

  const handleRecord = async () => {
    try {
      await paymentService.create(recordForm)
      addToast({ message: 'Payment recorded successfully', type: 'success' })
      setShowRecordModal(false)
      loadPayments()
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to record payment', type: 'error' })
    }
  }

  const handlePaymentUpdate = async () => {
    if (!selectedPayment) return
    
    try {
      await paymentService.update(selectedPayment.id, editForm)
      addToast({ message: 'Payment updated successfully', type: 'success' })
      setShowEditModal(false)
      setSelectedPayment(null)
      loadPayments()
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to update payment', type: 'error' })
    }
  }

  const getStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      paid: 'var(--success)',
      pending: 'var(--warning)',
      overdue: 'var(--danger)',
      cancelled: 'var(--muted)'
    }
    return colors[status] || 'var(--muted)'
  }

  if (loading) {
    return (
      <div className="page">
        <h1>Payment Management</h1>
        <div className="empty">Loading payments…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <h1>Payment Management</h1>
        <div className="card" style={{ color: 'var(--danger)' }}>
          Failed to load payments: {error}
          <button className="button" onClick={loadPayments} style={{ marginTop: 12 }}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1>Payment Management</h1>
        <button 
          className="button" 
          onClick={handleRecordPayment}
        >
          Record Payment
        </button>
      </div>
      
      {/* Filters */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="admin-filters">
          <input
            type="text"
            className="input"
            placeholder="Search payments..."
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
            <option value="paid">Paid</option>
            <option value="pending">Pending</option>
            <option value="overdue">Overdue</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Payments Table */}
      {filteredPayments.length === 0 ? (
        <div className="empty">
          {searchTerm || statusFilter ? 'No payments match your filters' : 'No payments found'}
        </div>
      ) : (
        <div className="card admin-table-container">
          <table className="admin-table">
            <thead>
              <tr style={{ borderBottom: '2px solid #f1f5f9' }}>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>ID</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Property</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Unit</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Amount</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Due Date</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Status</th>
                <th style={{ textAlign: 'right', padding: 12, fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredPayments.map((payment) => (
                <tr key={payment.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td data-label="ID" style={{ padding: 12 }}>#{payment.id}</td>
                  <td data-label="Property" style={{ padding: 12 }}>#{payment.property_id}</td>
                  <td data-label="Unit" style={{ padding: 12 }}>#{payment.unit_id}</td>
                  <td data-label="Amount" style={{ padding: 12 }}>{payment.amount}</td>
                  <td data-label="Due Date" style={{ padding: 12 }}>
                    {new Date(payment.due_date).toLocaleDateString()}
                  </td>
                  <td data-label="Status" style={{ padding: 12 }}>
                    <span style={{ 
                      color: 'white',
                      background: getStatusBadgeColor(payment.status),
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: 12,
                      fontWeight: 600
                    }}>
                      {payment.status.toUpperCase()}
                    </span>
                  </td>
                  <td data-label="Actions" style={{ padding: 12, textAlign: 'right' }}>
                    <div className="admin-actions">
                      <button 
                        className="button muted" 
                        style={{ padding: '4px 8px', fontSize: 12 }}
                        onClick={() => handleEditPayment(payment)}
                      >
                        Edit
                      </button>
                      <button 
                        className="button danger" 
                        style={{ padding: '4px 8px', fontSize: 12 }}
                        onClick={() => handleDeletePayment(payment)}
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
        title="Delete Payment"
        description={`Are you sure you want to delete payment #${selectedPayment?.id}? This action cannot be undone.`}
        onConfirm={confirmDelete}
        onCancel={() => {
          setShowDeleteConfirm(false)
          setSelectedPayment(null)
        }}
      />

      <ConfirmDialog 
        open={showRecordModal}
        title="Record Payment"
        description="Record a new payment"
        onConfirm={handleRecord}
        onCancel={() => {
          setShowRecordModal(false)
        }}
      >
        <div style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Tenant ID:</label>
            <input
              type="number"
              className="input"
              value={recordForm.tenant_id}
              onChange={(e) => setRecordForm({...recordForm, tenant_id: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Lease ID:</label>
            <input
              type="number"
              className="input"
              value={recordForm.lease_id}
              onChange={(e) => setRecordForm({...recordForm, lease_id: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Property ID:</label>
            <input
              type="number"
              className="input"
              value={recordForm.property_id}
              onChange={(e) => setRecordForm({...recordForm, property_id: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Unit ID:</label>
            <input
              type="number"
              className="input"
              value={recordForm.unit_id}
              onChange={(e) => setRecordForm({...recordForm, unit_id: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Amount:</label>
            <input
              className="input"
              value={recordForm.amount}
              onChange={(e) => setRecordForm({...recordForm, amount: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Due Date:</label>
            <input
              type="date"
              className="input"
              value={recordForm.due_date}
              onChange={(e) => setRecordForm({...recordForm, due_date: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Payment Type:</label>
            <input
              className="input"
              value={recordForm.payment_type}
              onChange={(e) => setRecordForm({...recordForm, payment_type: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Payment Method:</label>
            <input
              className="input"
              value={recordForm.payment_method}
              onChange={(e) => setRecordForm({...recordForm, payment_method: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Status:</label>
            <select
              className="input"
              value={recordForm.status}
              onChange={(e) => setRecordForm({...recordForm, status: e.target.value})}
              style={{ width: '100%' }}
            >
              <option value="pending">Pending</option>
              <option value="paid">Paid</option>
              <option value="overdue">Overdue</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Reference (optional):</label>
            <input
              className="input"
              value={recordForm.reference}
              onChange={(e) => setRecordForm({...recordForm, reference: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Notes (optional):</label>
            <textarea
              className="input"
              value={recordForm.notes}
              onChange={(e) => setRecordForm({...recordForm, notes: e.target.value})}
              style={{ width: '100%' }}
              rows={3}
            />
          </div>
        </div>
      </ConfirmDialog>

      <ConfirmDialog 
        open={showEditModal}
        title="Edit Payment"
        description={`Edit payment #${selectedPayment?.id}`}
        onConfirm={handlePaymentUpdate}
        onCancel={() => {
          setShowEditModal(false)
          setSelectedPayment(null)
        }}
      >
        <div style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Amount:</label>
            <input
              className="input"
              value={editForm.amount}
              onChange={(e) => setEditForm({...editForm, amount: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Payment Date:</label>
            <input
              type="date"
              className="input"
              value={editForm.payment_date}
              onChange={(e) => setEditForm({...editForm, payment_date: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Payment Method:</label>
            <input
              className="input"
              value={editForm.payment_method}
              onChange={(e) => setEditForm({...editForm, payment_method: e.target.value})}
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
              <option value="pending">Pending</option>
              <option value="paid">Paid</option>
              <option value="overdue">Overdue</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Reference (optional):</label>
            <input
              className="input"
              value={editForm.reference}
              onChange={(e) => setEditForm({...editForm, reference: e.target.value})}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 600 }}>Notes (optional):</label>
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

export default PaymentsManagement