import React, { useEffect, useState } from 'react'
import { getOwnerProperties } from '../../services/owner'
import { getPropertyApplications, updateApplicationStatus, convertToLease } from '../../services/application'
import { Property, RentalApplication } from '../../types'

export const OwnerApplications: React.FC = () => {
  const [properties, setProperties] = useState<Property[]>([])
  const [selectedPropertyId, setSelectedPropertyId] = useState<number | null>(null)
  const [applications, setApplications] = useState<RentalApplication[]>([])
  const [loading, setLoading] = useState(true)
  const [actionModal, setActionModal] = useState<{ app: RentalApplication; type: 'review' | 'lease' } | null>(null)
  const [reviewStatus, setReviewStatus] = useState<'approved' | 'rejected' | 'under_review'>('approved')
  const [reviewNotes, setReviewNotes] = useState('')
  const [leaseStart, setLeaseStart] = useState('')
  const [leaseEnd, setLeaseEnd] = useState('')
  const [leaseRent, setLeaseRent] = useState('')
  const [processing, setProcessing] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  useEffect(() => {
    getOwnerProperties()
      .then((props) => {
        setProperties(props)
        if (props.length > 0) {
          setSelectedPropertyId(props[0].id)
        }
      })
      .finally(() => setLoading(false))
  }, [])

  const loadApps = (propId: number) => {
    getPropertyApplications(propId).then(setApplications)
  }

  useEffect(() => {
    if (selectedPropertyId) {
      loadApps(selectedPropertyId)
    }
  }, [selectedPropertyId])

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!actionModal) return
    setProcessing(true)
    try {
      await updateApplicationStatus(actionModal.app.id, {
        status: reviewStatus,
        review_notes: reviewNotes,
      })
      setMsg(`Application marked as ${reviewStatus}!`)
      setActionModal(null)
      if (selectedPropertyId) loadApps(selectedPropertyId)
    } catch (err: any) {
      alert(err.message || 'Failed to review application')
    } finally {
      setProcessing(false)
    }
  }

  const handleConvertSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!actionModal) return
    setProcessing(true)
    try {
      await convertToLease(actionModal.app.id, {
        start_date: leaseStart,
        end_date: leaseEnd,
        rent_amount: leaseRent,
      })
      setMsg('Rental application successfully converted to active Lease!')
      setActionModal(null)
      if (selectedPropertyId) loadApps(selectedPropertyId)
    } catch (err: any) {
      alert(err.message || 'Failed to convert to lease')
    } finally {
      setProcessing(false)
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading incoming applications...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Rental Applications & Screening</h1>
          <p className="text-slate-500 text-sm mt-1">
            Review applicant backgrounds, income declarations, and convert approved candidates into leases.
          </p>
        </div>
        {properties.length > 0 && (
          <div>
            <select
              value={selectedPropertyId || ''}
              onChange={(e) => setSelectedPropertyId(Number(e.target.value))}
              className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {properties.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {msg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm">
          {msg}
        </div>
      )}

      {applications.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-100 text-center max-w-lg mx-auto mt-8 shadow-sm">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
            📋
          </div>
          <h2 className="text-xl font-bold text-slate-800">No Applications for this Property</h2>
          <p className="text-slate-500 text-sm mt-2">
            Prospective tenants submitting rental applications will appear here for your review and lease execution.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {applications.map((app) => (
            <div key={app.id} className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className={`px-2.5 py-1 text-xs font-semibold rounded-full uppercase ${
                    app.status === 'approved' ? 'bg-emerald-100 text-emerald-800' :
                    app.status === 'rejected' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'
                  }`}>
                    {app.status}
                  </span>
                  <span className="text-xs text-slate-400">
                    {new Date(app.created_at).toLocaleDateString()}
                  </span>
                </div>

                <h3 className="font-bold text-lg text-slate-800">{app.applicant_name || `Applicant #${app.applicant_id}`}</h3>
                <div className="text-xs text-slate-500 mt-0.5">{app.applicant_email || 'Verified user'}</div>

                <div className="mt-4 p-3.5 bg-slate-50 rounded-xl space-y-1.5 text-xs text-slate-600">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Employer:</span>
                    <span className="font-medium text-slate-700">{app.employer_name || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Monthly Income:</span>
                    <span className="font-semibold text-emerald-700">{app.monthly_income ? `KSh ${app.monthly_income}` : 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Occupants:</span>
                    <span className="font-medium text-slate-700">{app.occupants_count || 1}</span>
                  </div>
                </div>

                {app.review_notes && (
                  <div className="mt-3 p-3 bg-blue-50 border border-blue-100 rounded-xl text-xs text-blue-900">
                    <span className="font-semibold block mb-0.5">Notes:</span>
                    {app.review_notes}
                  </div>
                )}
              </div>

              <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between gap-2">
                <button
                  onClick={() => {
                    setActionModal({ app, type: 'review' })
                    setReviewStatus('approved')
                    setReviewNotes('')
                  }}
                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
                >
                  Review
                </button>

                {app.status === 'approved' && (
                  <button
                    onClick={() => {
                      setActionModal({ app, type: 'lease' })
                      setLeaseStart(new Date().toISOString().split('T')[0])
                      setLeaseEnd(new Date(Date.now() + 365 * 86400000).toISOString().split('T')[0])
                      setLeaseRent(app.monthly_income || '45000')
                    }}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold transition shadow-sm"
                  >
                    Convert to Lease &rarr;
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Review & Conversion Modal */}
      {actionModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex justify-between items-center pb-4 border-b border-slate-100">
              <h3 className="font-bold text-lg text-slate-800">
                {actionModal.type === 'review' ? 'Review Rental Application' : 'Execute Lease Agreement'}
              </h3>
              <button onClick={() => setActionModal(null)} className="text-slate-400 hover:text-slate-600 font-bold text-xl">
                &times;
              </button>
            </div>

            {actionModal.type === 'review' ? (
              <form onSubmit={handleReviewSubmit} className="py-4 space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Decision Status</label>
                  <select
                    value={reviewStatus}
                    onChange={(e) => setReviewStatus(e.target.value as any)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="approved">Approve Application</option>
                    <option value="rejected">Reject Application</option>
                    <option value="under_review">Under Review / Background Check</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Review Notes / Reason</label>
                  <textarea
                    rows={3}
                    placeholder="Provide comments or conditions for the applicant..."
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div className="pt-4 border-t border-slate-100 flex justify-end gap-3">
                  <button type="button" onClick={() => setActionModal(null)} className="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl text-xs font-semibold">
                    Cancel
                  </button>
                  <button type="submit" disabled={processing} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold">
                    {processing ? 'Saving...' : 'Submit Decision'}
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleConvertSubmit} className="py-4 space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Agreed Monthly Rent (KSh) *</label>
                  <input
                    type="text"
                    required
                    value={leaseRent}
                    onChange={(e) => setLeaseRent(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Start Date *</label>
                    <input
                      type="date"
                      required
                      value={leaseStart}
                      onChange={(e) => setLeaseStart(e.target.value)}
                      className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">End Date *</label>
                    <input
                      type="date"
                      required
                      value={leaseEnd}
                      onChange={(e) => setLeaseEnd(e.target.value)}
                      className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>
                <div className="pt-4 border-t border-slate-100 flex justify-end gap-3">
                  <button type="button" onClick={() => setActionModal(null)} className="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl text-xs font-semibold">
                    Cancel
                  </button>
                  <button type="submit" disabled={processing} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold">
                    {processing ? 'Creating Lease...' : 'Execute Active Lease'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
export default OwnerApplications
