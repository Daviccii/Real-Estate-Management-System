import React, { useEffect, useState } from 'react'
import { getMyTenancy } from '../../services/tenant'
import { getMyVerifications } from '../../services/verification'
import { Lease, VerificationRecord } from '../../types'

export const TenantDocuments: React.FC = () => {
  const [lease, setLease] = useState<Lease | null>(null)
  const [verifications, setVerifications] = useState<VerificationRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getMyTenancy(), getMyVerifications()])
      .then(([l, v]) => {
        setLease(l)
        setVerifications(v)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading your digital vault...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Document Vault & Verification Files</h1>
          <p className="text-slate-500 text-sm mt-1">Official lease agreements, verified identity credentials, and inspection reports.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Lease Agreement Document */}
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold text-lg">
              📄
            </div>
            <div>
              <h2 className="font-bold text-slate-800">Digital Tenancy Agreement</h2>
              <span className="text-xs text-slate-400">Binding legal agreement</span>
            </div>
          </div>

          {lease ? (
            <div className="space-y-3 text-sm bg-slate-50 p-4 rounded-xl">
              <div className="flex justify-between">
                <span className="text-slate-400">Property:</span>
                <span className="font-medium text-slate-700">{lease.property_name || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Unit:</span>
                <span className="font-medium text-slate-700">{lease.unit_number || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Term:</span>
                <span className="font-medium text-slate-700">{lease.start_date} to {lease.end_date}</span>
              </div>
              <div className="pt-3 border-t border-slate-200/60 flex gap-2">
                <button
                  onClick={() => window.print()}
                  className="w-full py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition"
                >
                  Download / Print PDF
                </button>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-400 py-4">No active lease agreement on record.</p>
          )}
        </div>

        {/* Identity & Background Verifications */}
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-lg">
              🛡️
            </div>
            <div>
              <h2 className="font-bold text-slate-800">Verified Credentials & ID</h2>
              <span className="text-xs text-slate-400">PropNoxa Trust Registry</span>
            </div>
          </div>

          {verifications.length === 0 ? (
            <div className="text-xs text-slate-400 py-4">
              No identity documents uploaded yet. Go to your profile or application to submit verified credentials.
            </div>
          ) : (
            <div className="divide-y divide-slate-100 text-sm">
              {verifications.map((v) => (
                <div key={v.id} className="py-3 flex items-center justify-between">
                  <div>
                    <div className="font-medium text-slate-800">{v.verification_type.replace('_', ' ').toUpperCase()}</div>
                    <div className="text-xs text-slate-400">Submitted {new Date(v.created_at).toLocaleDateString()}</div>
                  </div>
                  <span className={`px-2.5 py-1 text-xs font-semibold rounded-full uppercase ${
                    v.status === 'approved' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                  }`}>
                    {v.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
export default TenantDocuments
