import React, { useState } from 'react'
import { submitQuote } from '../../services/serviceMarketplace'

export const ProviderQuotes: React.FC = () => {
  const [requestId, setRequestId] = useState('')
  const [quotedAmount, setQuotedAmount] = useState('')
  const [estimatedHours, setEstimatedHours] = useState('')
  const [scopeDescription, setScopeDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!requestId || !quotedAmount || !scopeDescription.trim()) return
    setSubmitting(true)
    try {
      await submitQuote({
        request_id: parseInt(requestId),
        quoted_amount: quotedAmount,
        estimated_hours: estimatedHours ? parseInt(estimatedHours) : undefined,
        scope_description: scopeDescription,
      })
      setMsg('Quote successfully submitted to property manager/owner!')
      setRequestId('')
      setQuotedAmount('')
      setEstimatedHours('')
      setScopeDescription('')
    } catch (err: any) {
      alert(err.message || 'Failed to submit quote')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Job Quotes & Marketplace Bids</h1>
        <p className="text-slate-500 text-sm mt-1">
          Submit competitive repair estimates, material costs, and labor hours for property maintenance tickets.
        </p>
      </div>

      {msg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm">
          {msg}
        </div>
      )}

      <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
        <h2 className="font-bold text-base text-slate-800 mb-4 pb-3 border-b border-slate-100">Submit New Job Estimate</h2>
        <form onSubmit={handleSubmit} className="space-y-4 text-sm">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Maintenance Request ID *</label>
              <input
                type="number"
                required
                placeholder="e.g. 4"
                value={requestId}
                onChange={(e) => setRequestId(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Total Quoted Amount (KSh) *</label>
              <input
                type="text"
                required
                placeholder="e.g. 15000"
                value={quotedAmount}
                onChange={(e) => setQuotedAmount(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Estimated Labor Hours</label>
              <input
                type="number"
                placeholder="e.g. 4"
                value={estimatedHours}
                onChange={(e) => setEstimatedHours(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Scope of Work & Materials Breakdown *</label>
            <textarea
              required
              rows={4}
              placeholder="Detail replacement parts (e.g., pipes, fittings), labor breakdown, and warranty period..."
              value={scopeDescription}
              onChange={(e) => setScopeDescription(e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>

          <div className="pt-3 flex justify-end">
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold shadow transition"
            >
              {submitting ? 'Submitting Quote...' : 'Submit Quote to Manager'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
export default ProviderQuotes
