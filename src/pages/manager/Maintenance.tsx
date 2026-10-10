import React, { useEffect, useState } from 'react'
import { managerService } from '../../services/manager'
import type { ManagerMaintenance } from '../../services/manager'
import {
  acceptQuote,
  getQuotesForRequest,
  getWorkOrders,
  submitWorkOrderReview,
} from '../../services/serviceMarketplace'
import type { MaintenanceQuote, MaintenanceWorkOrder } from '../../types'
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

  const [showQuotesModal, setShowQuotesModal] = useState(false)
  const [quotes, setQuotes] = useState<MaintenanceQuote[]>([])
  const [workOrders, setWorkOrders] = useState<MaintenanceWorkOrder[]>([])
  const [quotesLoading, setQuotesLoading] = useState(false)
  const [quotesError, setQuotesError] = useState<string | null>(null)
  const [acceptingQuoteId, setAcceptingQuoteId] = useState<number | null>(null)
  const [reviewOrder, setReviewOrder] = useState<MaintenanceWorkOrder | null>(null)
  const [reviewScore, setReviewScore] = useState(5)
  const [reviewComment, setReviewComment] = useState('')
  const [submittingReview, setSubmittingReview] = useState(false)

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

  const loadQuotesAndOrders = async (requestId: number) => {
    setQuotesLoading(true)
    setQuotesError(null)
    try {
      const [quoteRows, orderRows] = await Promise.all([
        getQuotesForRequest(requestId),
        getWorkOrders(undefined, requestId),
      ])
      setQuotes(quoteRows)
      setWorkOrders(orderRows)
    } catch (err: any) {
      setQuotesError(err?.message || 'Failed to load quotes and work orders')
    } finally {
      setQuotesLoading(false)
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

  const openQuotesModal = (item: ManagerMaintenance) => {
    setSelectedMaintenance(item)
    setShowQuotesModal(true)
    setReviewOrder(null)
    void loadQuotesAndOrders(item.id)
  }

  const handleAcceptQuote = async (quote: MaintenanceQuote) => {
    setAcceptingQuoteId(quote.id)
    try {
      await acceptQuote(quote.id)
      addToast({ message: `Quote from ${quote.provider_name || 'provider'} accepted — work order created`, type: 'success' })
      if (selectedMaintenance) await loadQuotesAndOrders(selectedMaintenance.id)
      loadMaintenance()
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to accept quote', type: 'error' })
    } finally {
      setAcceptingQuoteId(null)
    }
  }

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reviewOrder) return
    setSubmittingReview(true)
    try {
      await submitWorkOrderReview(reviewOrder.id, reviewScore, reviewComment.trim() || undefined)
      addToast({ message: 'Provider review submitted — profile rating updated', type: 'success' })
      setReviewOrder(null)
      setReviewScore(5)
      setReviewComment('')
      if (selectedMaintenance) await loadQuotesAndOrders(selectedMaintenance.id)
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to submit review', type: 'error' })
    } finally {
      setSubmittingReview(false)
    }
  }

  if (loading) return <div className="empty">Loading maintenance requests…</div>
  if (error) return <div className="empty error">{error}</div>

  return (
    <div className="management-container">
      <div className="management-header">
        <span className="manager-eyebrow">Service coordination</span>
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
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
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
                      <button
                        onClick={() => openQuotesModal(item)}
                        className="button small secondary"
                      >
                        Quotes &amp; Work Orders
                      </button>
                    </div>
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

      {/* Quotes & Work Orders Modal */}
      {showQuotesModal && selectedMaintenance && (
        <div className="modal-overlay" onClick={() => { setShowQuotesModal(false); setReviewOrder(null) }}>
          <div className="modal-content" style={{ maxWidth: 760 }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2 style={{ margin: 0 }}>Quotes &amp; Work Orders</h2>
                <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
                  Ticket #{selectedMaintenance.id} · {selectedMaintenance.title}
                </div>
              </div>
              <button
                onClick={() => { setShowQuotesModal(false); setReviewOrder(null) }}
                className="close-button"
                aria-label="Close"
              >
                ✕
              </button>
            </div>

            {quotesLoading && <div className="empty">Loading quotes…</div>}
            {quotesError && <div className="empty error">{quotesError}</div>}

            {!quotesLoading && !quotesError && (
              <>
                <h3 style={{ fontSize: 14, margin: '6px 0 8px' }}>Provider Quotes</h3>
                {quotes.length === 0 ? (
                  <div className="empty" style={{ padding: '12px 0' }}>
                    No quotes yet. Providers see this ticket on the marketplace job board.
                  </div>
                ) : (
                  <div className="table-container">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Provider</th>
                          <th>Amount</th>
                          <th>Hours</th>
                          <th>Scope</th>
                          <th>Status</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {quotes.map((quote) => (
                          <tr key={quote.id}>
                            <td>{quote.provider_name || `Provider #${quote.provider_id}`}</td>
                            <td>KSh {quote.quoted_amount}</td>
                            <td>{quote.estimated_hours ?? '—'}</td>
                            <td style={{ maxWidth: 220 }}>
                              <div style={{ fontSize: 12, color: 'var(--muted)' }}>{quote.scope_description}</div>
                            </td>
                            <td>
                              <span className={`badge status-${quote.status}`}>{quote.status}</span>
                            </td>
                            <td>
                              {quote.status === 'pending' ? (
                                <button
                                  className="button small"
                                  disabled={acceptingQuoteId === quote.id}
                                  onClick={() => handleAcceptQuote(quote)}
                                >
                                  {acceptingQuoteId === quote.id ? 'Accepting…' : 'Accept & Dispatch'}
                                </button>
                              ) : (
                                <span style={{ fontSize: 12, color: 'var(--muted)' }}>—</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                <h3 style={{ fontSize: 14, margin: '18px 0 8px' }}>Work Orders</h3>
                {workOrders.length === 0 ? (
                  <div className="empty" style={{ padding: '12px 0' }}>
                    No work orders yet. Accept a quote to dispatch one.
                  </div>
                ) : (
                  <div className="table-container">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Provider</th>
                          <th>Status</th>
                          <th>Scheduled</th>
                          <th>Rating</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {workOrders.map((order) => (
                          <tr key={order.id}>
                            <td>{order.provider_company || `Provider #${order.provider_id}`}</td>
                            <td>
                              <span className={`badge status-${order.status}`}>{order.status.replace('_', ' ')}</span>
                            </td>
                            <td>
                              {order.scheduled_date ? new Date(order.scheduled_date).toLocaleDateString() : 'ASAP'}
                            </td>
                            <td>
                              {order.has_review ? (
                                <span title={`${order.review_score} out of 5`} style={{ color: '#d97706', letterSpacing: 1 }}>
                                  {'★'.repeat(order.review_score || 0)}{'☆'.repeat(5 - (order.review_score || 0))}
                                </span>
                              ) : (
                                <span style={{ fontSize: 12, color: 'var(--muted)' }}>Not rated</span>
                              )}
                            </td>
                            <td>
                              {order.can_review ? (
                                <button
                                  className="button small"
                                  onClick={() => {
                                    setReviewOrder(order)
                                    setReviewScore(5)
                                    setReviewComment('')
                                  }}
                                >
                                  Rate Provider
                                </button>
                              ) : (
                                <span style={{ fontSize: 12, color: 'var(--muted)' }}>
                                  {order.has_review ? 'Reviewed' : order.status === 'assigned' ? 'Awaiting execution' : 'Awaiting completion'}
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {reviewOrder && (
                  <form onSubmit={handleSubmitReview} style={{ marginTop: 18, borderTop: '1px solid var(--border, #e5e7eb)', paddingTop: 14 }}>
                    <h3 style={{ fontSize: 14, margin: '0 0 10px' }}>
                      Rate {reviewOrder.provider_company || `Provider #${reviewOrder.provider_id}`} (Order #{reviewOrder.id})
                    </h3>

                    <div className="form-group">
                      <label htmlFor="reviewScore">Score</label>
                      <select
                        id="reviewScore"
                        className="input"
                        value={reviewScore}
                        onChange={(e) => setReviewScore(Number(e.target.value))}
                      >
                        <option value={5}>★★★★★ — Excellent</option>
                        <option value={4}>★★★★☆ — Good</option>
                        <option value={3}>★★★☆☆ — Fair</option>
                        <option value={2}>★★☆☆☆ — Poor</option>
                        <option value={1}>★☆☆☆☆ — Very poor</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label htmlFor="reviewComment">Comment (optional)</label>
                      <textarea
                        id="reviewComment"
                        className="input"
                        rows={3}
                        maxLength={1000}
                        placeholder="Punctuality, workmanship, cleanliness, communication…"
                        value={reviewComment}
                        onChange={(e) => setReviewComment(e.target.value)}
                      />
                    </div>

                    <div className="modal-footer">
                      <button type="button" className="button secondary" onClick={() => setReviewOrder(null)}>
                        Cancel
                      </button>
                      <button type="submit" className="button" disabled={submittingReview}>
                        {submittingReview ? 'Submitting…' : 'Submit Review'}
                      </button>
                    </div>
                  </form>
                )}
              </>
            )}
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
