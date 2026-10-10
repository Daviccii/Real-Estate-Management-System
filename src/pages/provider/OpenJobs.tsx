import React, { useEffect, useState } from 'react'

import { getOpenRequests, submitQuote } from '../../services/serviceMarketplace'
import type { OpenMaintenanceRequest, Paginated } from '../../types'

const JOB_CATEGORIES = [
  'plumbing',
  'electrical',
  'hvac',
  'carpentry',
  'painting',
  'masonry',
  'roofing',
  'cleaning',
  'security',
  'appliance',
  'general',
]

export const ProviderOpenJobs: React.FC = () => {
  const [inputs, setInputs] = useState({ q: '', city: '' })
  const [category, setCategory] = useState('')
  const [applied, setApplied] = useState({ q: '', city: '' })
  const [page, setPage] = useState(1)

  const [result, setResult] = useState<Paginated<OpenMaintenanceRequest> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const [selectedJob, setSelectedJob] = useState<OpenMaintenanceRequest | null>(null)
  const [quotedAmount, setQuotedAmount] = useState('')
  const [estimatedHours, setEstimatedHours] = useState('')
  const [scopeDescription, setScopeDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getOpenRequests({
      q: applied.q || undefined,
      city: applied.city || undefined,
      category: category || undefined,
      page,
      page_size: 12,
    })
      .then((response) => {
        if (!cancelled) setResult(response)
      })
      .catch((err: any) => {
        if (!cancelled) setError(err?.message || 'Failed to load open jobs')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [applied, category, page, refreshKey])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setApplied({ q: inputs.q.trim(), city: inputs.city.trim() })
    setPage(1)
  }

  const openQuoteModal = (job: OpenMaintenanceRequest) => {
    setSelectedJob(job)
    setQuotedAmount('')
    setEstimatedHours('')
    setScopeDescription('')
  }

  const handleSubmitQuote = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedJob || !quotedAmount || !scopeDescription.trim()) return
    setSubmitting(true)
    try {
      await submitQuote({
        request_id: selectedJob.id,
        quoted_amount: quotedAmount,
        estimated_hours: estimatedHours ? parseInt(estimatedHours, 10) : undefined,
        scope_description: scopeDescription.trim(),
      })
      setSuccessMsg(`Quote submitted for "${selectedJob.title}". The property manager will review it shortly.`)
      setSelectedJob(null)
      setRefreshKey((key) => key + 1)
    } catch (err: any) {
      alert(err.message || 'Failed to submit quote')
    } finally {
      setSubmitting(false)
    }
  }

  const totalPages = result ? Math.max(1, Math.ceil(result.total / result.page_size)) : 1

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="provider-eyebrow">Marketplace opportunities</span>
          <h1 className="text-2xl font-bold text-slate-800">Open Job Board</h1>
          <p className="text-slate-500 text-sm mt-1">
            Browse maintenance tickets across the platform, filter by trade and location, and submit competitive quotes.
          </p>
        </div>
      </div>

      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm">
          {successMsg}
        </div>
      )}

      <form
        onSubmit={handleSearch}
        className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm flex flex-col sm:flex-row gap-3 sm:items-center"
      >
        <input
          type="text"
          value={inputs.q}
          onChange={(e) => setInputs((prev) => ({ ...prev, q: e.target.value }))}
          placeholder="Search job title or description…"
          aria-label="Search open jobs"
          className="flex-1 px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
        />
        <input
          type="text"
          value={inputs.city}
          onChange={(e) => setInputs((prev) => ({ ...prev, city: e.target.value }))}
          placeholder="City"
          aria-label="Filter by city"
          className="w-full sm:w-36 px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
        />
        <select
          value={category}
          onChange={(e) => {
            setCategory(e.target.value)
            setPage(1)
          }}
          aria-label="Filter by trade category"
          className="w-full sm:w-44 px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
        >
          <option value="">All trades</option>
          {JOB_CATEGORIES.map((cat) => (
            <option key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</option>
          ))}
        </select>
        <button
          type="submit"
          className="px-5 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold shadow transition"
        >
          Search Jobs
        </button>
      </form>

      {loading && <div className="p-8 text-center text-slate-500">Loading open jobs…</div>}
      {error && <div className="p-8 text-center text-red-600">{error}</div>}

      {!loading && !error && result && (
        <>
          <div className="text-xs text-slate-400">
            {result.total} open job{result.total === 1 ? '' : 's'} available
          </div>

          {result.items.length === 0 ? (
            <div className="bg-white rounded-2xl p-8 border border-slate-100 text-center max-w-lg mx-auto mt-4 shadow-sm">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                🔍
              </div>
              <h2 className="text-xl font-bold text-slate-800">No Open Jobs Match</h2>
              <p className="text-slate-500 text-sm mt-2">
                Try widening your trade filter or clearing the search text. New tickets appear here as they are reported.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {result.items.map((job) => (
                <div key={job.id} className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <span className="px-2.5 py-1 text-xs font-semibold rounded-full uppercase bg-amber-100 text-amber-800">
                        {job.category || 'General'}
                      </span>
                      <span className="text-xs text-slate-400">Ticket #{job.id}</span>
                    </div>

                    <h3 className="font-bold text-lg text-slate-800">{job.title}</h3>
                    <div className="text-xs text-slate-500 mt-1">
                      {[job.city, job.county].filter(Boolean).join(', ') || 'Location undisclosed'}
                      {job.property_type ? ` · ${job.property_type}` : ''}
                    </div>

                    {job.description && (
                      <p className="mt-3 text-xs text-slate-600 bg-slate-50 p-2.5 rounded-xl">{job.description}</p>
                    )}

                    <div className="mt-4 p-3.5 bg-slate-50 rounded-xl space-y-1 text-xs text-slate-600">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Priority:</span>
                        <span className="font-medium text-slate-700 uppercase">{job.priority || 'Normal'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Quotes so far:</span>
                        <span className="font-medium text-slate-700">{job.quotes_count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Reported:</span>
                        <span className="font-medium text-slate-700">
                          {job.created_at ? new Date(job.created_at).toLocaleDateString() : '—'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-5 pt-4 border-t border-slate-100 flex justify-end">
                    {job.my_quote_id ? (
                      <span className="px-3 py-2 bg-emerald-50 border border-emerald-100 text-emerald-800 rounded-xl text-xs font-semibold">
                        ✓ Quote sent — KSh {job.my_quote_amount} ({job.my_quote_status})
                      </span>
                    ) : (
                      <button
                        onClick={() => openQuoteModal(job)}
                        className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold transition shadow-sm"
                      >
                        Submit Quote &rarr;
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 pt-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl text-xs font-semibold disabled:opacity-40"
              >
                ← Prev
              </button>
              <span className="text-xs text-slate-500">Page {page} of {totalPages}</span>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl text-xs font-semibold disabled:opacity-40"
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}

      {selectedJob && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <div className="flex justify-between items-center pb-4 border-b border-slate-100">
              <div>
                <h3 className="font-bold text-lg text-slate-800">Submit Quote</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Ticket #{selectedJob.id} · {selectedJob.title}
                </p>
              </div>
              <button
                onClick={() => setSelectedJob(null)}
                className="text-slate-400 hover:text-slate-600 font-bold text-xl"
                aria-label="Close"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleSubmitQuote} className="py-4 space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="quoteAmount" className="block text-xs font-semibold text-slate-700 mb-1">Total Quoted Amount (KSh) *</label>
                  <input
                    id="quoteAmount"
                    type="text"
                    required
                    value={quotedAmount}
                    onChange={(e) => setQuotedAmount(e.target.value)}
                    placeholder="e.g. 15000"
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                </div>
                <div>
                  <label htmlFor="quoteHours" className="block text-xs font-semibold text-slate-700 mb-1">Estimated Labor Hours</label>
                  <input
                    id="quoteHours"
                    type="number"
                    value={estimatedHours}
                    onChange={(e) => setEstimatedHours(e.target.value)}
                    placeholder="e.g. 4"
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="quoteScope" className="block text-xs font-semibold text-slate-700 mb-1">Scope of Work & Materials Breakdown *</label>
                <textarea
                  id="quoteScope"
                  required
                  rows={4}
                  value={scopeDescription}
                  onChange={(e) => setScopeDescription(e.target.value)}
                  placeholder="Detail replacement parts, labor breakdown, and warranty period…"
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>

              <div className="pt-4 border-t border-slate-100 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setSelectedJob(null)}
                  className="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold shadow"
                >
                  {submitting ? 'Submitting…' : 'Send Quote to Manager'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProviderOpenJobs
