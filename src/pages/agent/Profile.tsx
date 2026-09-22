import React, { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { submitVerification } from '../../services/verification'

export const AgentProfile: React.FC = () => {
  const { user } = useAuth()
  const [licenseNumber, setLicenseNumber] = useState('')
  const [businessName, setBusinessName] = useState('')
  const [docUrl, setDocUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)

  const handleVerifyAgent = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!docUrl.trim()) return
    setSubmitting(true)
    try {
      await submitVerification({
        verification_type: 'agency_license',
        license_number: licenseNumber || undefined,
        business_name: businessName || undefined,
        document_url: docUrl,
      })
      setStatusMsg('Estate Agent Board / EARB practicing license submitted for verification!')
      setDocUrl('')
    } catch (err: any) {
      alert(err.message || 'Failed to submit license verification')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Agent Profile & Professional Accreditation</h1>
        <p className="text-slate-500 text-sm mt-1">Manage public agent credentials, agency affiliation, and EARB verification badge.</p>
      </div>

      {statusMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm">
          {statusMsg}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-4">
          <h2 className="font-bold text-base text-slate-800 border-b border-slate-100 pb-3">Agent Profile</h2>
          <div className="space-y-3 text-sm">
            <div>
              <span className="text-xs text-slate-400 block">Agent Name</span>
              <span className="font-semibold text-slate-800">{user?.full_name || 'Licensed Agent'}</span>
            </div>
            <div>
              <span className="text-xs text-slate-400 block">Email Address</span>
              <span className="font-semibold text-slate-800">{user?.email}</span>
            </div>
            <div>
              <span className="text-xs text-slate-400 block">Platform Verification</span>
              <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold uppercase mt-1 ${
                user?.is_verified ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
              }`}>
                {user?.is_verified ? '✓ Verified Professional Agent' : 'Verification Pending'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-4">
          <h2 className="font-bold text-base text-slate-800 border-b border-slate-100 pb-3">Submit Real Estate License / Accreditation</h2>
          <form onSubmit={handleVerifyAgent} className="space-y-4 text-sm">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Agency / Brokerage Firm Name</label>
              <input
                type="text"
                placeholder="e.g. Apex Realty Partners"
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">EARB / Professional License Number</label>
              <input
                type="text"
                placeholder="e.g. EARB/A/10492"
                value={licenseNumber}
                onChange={(e) => setLicenseNumber(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">License Certificate Document URL *</label>
              <input
                type="url"
                required
                placeholder="https://storage.propnoxa.com/licenses/earb-cert.pdf"
                value={docUrl}
                onChange={(e) => setDocUrl(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow transition"
            >
              {submitting ? 'Submitting...' : 'Submit Accreditation for Review'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
export default AgentProfile
