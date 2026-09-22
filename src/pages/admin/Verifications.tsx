import React, { useEffect, useState } from 'react'
import { getPendingVerifications, reviewVerification } from '../../services/verification'
import { VerificationRecord } from '../../types'

export const AdminVerifications: React.FC = () => {
  const [verifications, setVerifications] = useState<VerificationRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [filterType, setFilterType] = useState<string>('all')
  const [selectedVerification, setSelectedVerification] = useState<VerificationRecord | null>(null)
  const [reviewNotes, setReviewNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [actionSuccess, setActionSuccess] = useState<string | null>(null)

  const loadData = async () => {
    setLoading(true)
    try {
      const data = await getPendingVerifications()
      setVerifications(data)
    } catch (err: any) {
      console.error('Failed to load pending verifications', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleReview = async (status: 'approved' | 'rejected') => {
    if (!selectedVerification) return
    setSubmitting(true)
    try {
      await reviewVerification(selectedVerification.id, {
        status,
        review_notes: reviewNotes || undefined
      })
      setActionSuccess(`Verification #${selectedVerification.id} successfully marked as ${status}.`)
      setSelectedVerification(null)
      setReviewNotes('')
      await loadData()
    } catch (err: any) {
      alert(err.message || 'Failed to review verification')
    } finally {
      setSubmitting(false)
    }
  }

  const filtered = verifications.filter((v) => {
    if (filterType === 'all') return true
    return v.verification_type === filterType
  })

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-blue-900 via-indigo-950 to-slate-900 rounded-2xl p-6 text-white shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="inline-block px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-xs font-semibold uppercase tracking-wider mb-2">
              Trust & Safety Compliance
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Accreditation & Verification Review Queue</h1>
            <p className="text-blue-100/80 text-sm mt-1">
              Verify government national IDs, property title deeds, EARB broker licenses, and contractor NCA registrations.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-4 py-2 bg-white/10 rounded-xl text-sm font-semibold backdrop-blur">
              {verifications.length} Pending Actions
            </span>
          </div>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm flex items-center justify-between">
          <span>{actionSuccess}</span>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-600 hover:text-emerald-800 text-xs font-bold">
            Dismiss
          </button>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-3">
        {[
          { id: 'all', label: 'All Pending' },
          { id: 'identity', label: 'Tenant / National ID' },
          { id: 'ownership', label: 'Landlord Title Deeds' },
          { id: 'agency_license', label: 'EARB Agent Licenses' },
          { id: 'contractor_license', label: 'Contractor Trade Certs' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilterType(tab.id)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition ${
              filterType === tab.id
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Verifications List */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-12 text-center text-slate-400 text-sm">Loading verification records...</div>
        ) : filtered.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-sm">
            No pending verifications matching "{filterType}". All user credentials up to date!
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {filtered.map((record) => (
              <div key={record.id} className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-50/50 transition">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-blue-100 text-blue-800">
                      {record.verification_type.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-slate-400">Record #{record.id}</span>
                    <span className="text-xs text-slate-400">• {new Date(record.created_at).toLocaleString()}</span>
                  </div>

                  <h3 className="font-bold text-base text-slate-800">
                    Applicant: {record.user_name || `User #${record.user_id}`} ({record.user_email || 'No email'})
                  </h3>

                  <div className="text-xs text-slate-600 flex flex-wrap gap-x-4 gap-y-1">
                    {record.id_type && <span>ID Type: <strong>{record.id_type}</strong></span>}
                    {record.id_number && <span>ID Number: <strong>{record.id_number}</strong></span>}
                    {record.business_name && <span>Business / Firm: <strong>{record.business_name}</strong></span>}
                    {record.license_number && <span>License / Reg: <strong>{record.license_number}</strong></span>}
                    {record.property_id && <span>Linked Property ID: <strong>#{record.property_id}</strong></span>}
                  </div>

                  <div className="pt-1">
                    <a
                      href={record.document_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline"
                    >
                      <span>📄 View Submitted Document / Certificate</span>
                      <span>&rarr;</span>
                    </a>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => {
                      setSelectedVerification(record)
                      setReviewNotes('')
                    }}
                    className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold shadow transition"
                  >
                    Review & Decide
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Review Modal */}
      {selectedVerification && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="font-bold text-lg text-slate-800">Review Verification Record #{selectedVerification.id}</h3>
              <button
                onClick={() => setSelectedVerification(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl space-y-2 text-xs text-slate-700">
              <div><strong>User:</strong> {selectedVerification.user_name} ({selectedVerification.user_email})</div>
              <div><strong>Type:</strong> {selectedVerification.verification_type.replace('_', ' ')}</div>
              {selectedVerification.id_number && <div><strong>ID Number:</strong> {selectedVerification.id_number}</div>}
              {selectedVerification.license_number && <div><strong>License / Reg:</strong> {selectedVerification.license_number}</div>}
              {selectedVerification.business_name && <div><strong>Firm:</strong> {selectedVerification.business_name}</div>}
              <div>
                <strong>Document Link:</strong>{' '}
                <a href={selectedVerification.document_url} target="_blank" rel="noreferrer" className="text-blue-600 underline">
                  {selectedVerification.document_url}
                </a>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Decision Notes / Auditor Feedback
              </label>
              <textarea
                rows={3}
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="e.g. Title deed verified against Ministry of Lands registry. Approved."
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setSelectedVerification(null)}
                className="px-4 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={submitting}
                onClick={() => handleReview('rejected')}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-semibold transition"
              >
                {submitting ? 'Processing...' : 'Reject Verification'}
              </button>
              <button
                type="button"
                disabled={submitting}
                onClick={() => handleReview('approved')}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow transition"
              >
                {submitting ? 'Processing...' : 'Approve & Grant Badge'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AdminVerifications
