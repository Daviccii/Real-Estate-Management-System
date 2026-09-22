import React, { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { submitVerification } from '../../services/verification'

export const TenantProfile: React.FC = () => {
  const { user } = useAuth()
  const [idType, setIdType] = useState('National ID')
  const [idNumber, setIdNumber] = useState('')
  const [docUrl, setDocUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!docUrl.trim()) return
    setSubmitting(true)
    try {
      await submitVerification({
        verification_type: 'identity',
        id_type: idType,
        id_number: idNumber,
        document_url: docUrl,
      })
      setStatusMsg('Identity document submitted for verification! Our security desk will review it shortly.')
      setIdNumber('')
      setDocUrl('')
    } catch (err: any) {
      alert(err.message || 'Failed to submit verification')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">My Profile & Security Verification</h1>
        <p className="text-slate-500 text-sm mt-1">Manage personal contact details and verified tenant trust badges.</p>
      </div>

      {statusMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm">
          {statusMsg}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* User Account Info */}
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-4">
          <h2 className="font-bold text-base text-slate-800 border-b border-slate-100 pb-3">Account Information</h2>
          <div className="space-y-3 text-sm">
            <div>
              <span className="text-xs text-slate-400 block">Full Name</span>
              <span className="font-semibold text-slate-800">{user?.full_name || 'Resident'}</span>
            </div>
            <div>
              <span className="text-xs text-slate-400 block">Email Address</span>
              <span className="font-semibold text-slate-800">{user?.email}</span>
            </div>
            <div>
              <span className="text-xs text-slate-400 block">Platform Role</span>
              <span className="inline-block px-2.5 py-0.5 bg-teal-100 text-teal-800 rounded-full text-xs font-bold uppercase mt-1">
                {user?.role}
              </span>
            </div>
            <div>
              <span className="text-xs text-slate-400 block">Verification Status</span>
              <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold uppercase mt-1 ${
                user?.is_verified ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
              }`}>
                {user?.is_verified ? 'Verified Resident' : 'Unverified'}
              </span>
            </div>
          </div>
        </div>

        {/* Verification Document Upload */}
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-4">
          <h2 className="font-bold text-base text-slate-800 border-b border-slate-100 pb-3">Submit Identity for Verification</h2>
          <form onSubmit={handleVerify} className="space-y-4 text-sm">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">ID Document Type</label>
              <select
                value={idType}
                onChange={(e) => setIdType(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="National ID">National ID Card</option>
                <option value="Passport">Passport</option>
                <option value="Alien Card / Work Permit">Alien Card / Work Permit</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">ID Number</label>
              <input
                type="text"
                placeholder="e.g. 12345678"
                value={idNumber}
                onChange={(e) => setIdNumber(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Document File URL / Link *</label>
              <input
                type="url"
                required
                placeholder="https://storage.propnoxa.com/docs/my-id.pdf"
                value={docUrl}
                onChange={(e) => setDocUrl(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
              <span className="text-[10px] text-slate-400 mt-1 block">
                Securely encrypted and accessible exclusively to platform compliance officers.
              </span>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-semibold shadow transition"
            >
              {submitting ? 'Submitting...' : 'Submit Verification Request'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
export default TenantProfile
