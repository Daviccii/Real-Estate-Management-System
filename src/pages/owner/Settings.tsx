import React, { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { submitVerification } from '../../services/verification'

export const OwnerSettings: React.FC = () => {
  const { user } = useAuth()
  const [docUrl, setDocUrl] = useState('')
  const [businessName, setBusinessName] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)

  const handleVerifyOwnership = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!docUrl.trim()) return
    setSubmitting(true)
    try {
      await submitVerification({
        verification_type: 'ownership',
        document_url: docUrl,
        business_name: businessName || undefined,
      })
      setStatusMsg('Title deed / Ownership verification submitted to PropNoxa Trust Registry!')
      setDocUrl('')
      setBusinessName('')
    } catch (err: any) {
      alert(err.message || 'Failed to submit ownership verification')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Owner Profile & Portfolio Settings</h1>
        <p className="text-slate-500 text-sm mt-1">Configure investor profile and title deed ownership badges.</p>
      </div>

      {statusMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm">
          {statusMsg}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-4">
          <h2 className="font-bold text-base text-slate-800 border-b border-slate-100 pb-3">Landlord Profile</h2>
          <div className="space-y-3 text-sm">
            <div>
              <span className="text-xs text-slate-400 block">Name</span>
              <span className="font-semibold text-slate-800">{user?.full_name || 'Property Owner'}</span>
            </div>
            <div>
              <span className="text-xs text-slate-400 block">Email</span>
              <span className="font-semibold text-slate-800">{user?.email}</span>
            </div>
            <div>
              <span className="text-xs text-slate-400 block">Account Roles</span>
              <span className="inline-block px-2.5 py-0.5 bg-indigo-100 text-indigo-800 rounded-full text-xs font-bold uppercase mt-1">
                {user?.role}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-4">
          <h2 className="font-bold text-base text-slate-800 border-b border-slate-100 pb-3">Submit Property Deed / Ownership Verification</h2>
          <form onSubmit={handleVerifyOwnership} className="space-y-4 text-sm">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Company / Holding Entity Name (Optional)</label>
              <input
                type="text"
                placeholder="e.g. Apex Holdings Ltd"
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Title Deed / Proof of Ownership URL *</label>
              <input
                type="url"
                required
                placeholder="https://storage.propnoxa.com/deeds/title-doc.pdf"
                value={docUrl}
                onChange={(e) => setDocUrl(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow transition"
            >
              {submitting ? 'Submitting...' : 'Submit Ownership Verification'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
export default OwnerSettings
