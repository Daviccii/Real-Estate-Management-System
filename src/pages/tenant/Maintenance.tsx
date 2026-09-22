import React, { useEffect, useState } from 'react'
import { getMyMaintenance, getMyTenancy } from '../../services/tenant'
import { maintenanceService } from '../../services/maintenance'
import { Maintenance, Lease } from '../../types'

export const TenantMaintenance: React.FC = () => {
  const [requests, setRequests] = useState<Maintenance[]>([])
  const [lease, setLease] = useState<Lease | null>(null)
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [title, setTitle] = useState('')
  const [category, setCategory] = useState('Plumbing')
  const [priority, setPriority] = useState('medium')
  const [description, setDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const loadData = () => {
    Promise.all([getMyMaintenance(), getMyTenancy()])
      .then(([m, l]) => {
        setRequests(m)
        setLease(l)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!lease) {
      alert('You need an active tenancy to submit a maintenance ticket.')
      return
    }
    setSubmitting(true)
    try {
      await maintenanceService.create({
        property_id: lease.property_id,
        unit_id: lease.unit_id,
        title,
        category,
        priority,
        description,
      })
      setSuccessMsg('Maintenance request submitted successfully! A manager or service contractor will be dispatched.')
      setShowModal(false)
      setTitle('')
      setDescription('')
      loadData()
    } catch (err: any) {
      alert(err.message || 'Failed to submit maintenance request')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading maintenance records...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Maintenance & Repairs</h1>
          <p className="text-slate-500 text-sm mt-1">
            Submit repair requests, track technician visits, and review work order progress.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-sm font-medium transition shadow-sm"
        >
          + Request New Repair
        </button>
      </div>

      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm">
          {successMsg}
        </div>
      )}

      {requests.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-100 text-center max-w-lg mx-auto mt-8 shadow-sm">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
            🔧
          </div>
          <h2 className="text-xl font-bold text-slate-800">No Maintenance Tickets</h2>
          <p className="text-slate-500 text-sm mt-2">
            You currently have no open or past maintenance requests. When an issue occurs in your home, report it here for fast resolution.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {requests.map((r) => (
            <div key={r.id} className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className={`px-2.5 py-1 text-xs font-semibold rounded-full uppercase tracking-wider ${
                    r.status === 'completed' || r.status === 'resolved'
                      ? 'bg-emerald-100 text-emerald-800'
                      : r.status === 'in_progress'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-amber-100 text-amber-800'
                  }`}>
                    {r.status}
                  </span>
                  <span className={`px-2 py-0.5 text-xs rounded font-medium ${
                    r.priority === 'urgent' || r.priority === 'high'
                      ? 'bg-red-50 text-red-700'
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {r.priority.toUpperCase()}
                  </span>
                </div>

                <h3 className="font-bold text-base text-slate-800">{r.title}</h3>
                <div className="text-xs text-slate-400 mt-1">{r.category || 'General Repair'} • Reported {r.created_at ? new Date(r.created_at).toLocaleDateString() : 'Recently'}</div>

                {r.description && (
                  <p className="mt-3 text-xs text-slate-600 bg-slate-50 p-3 rounded-xl leading-relaxed">
                    {r.description}
                  </p>
                )}

                {r.notes && (
                  <div className="mt-3 p-3 bg-teal-50/50 border border-teal-100 rounded-xl text-xs text-teal-900">
                    <span className="font-semibold block mb-0.5">Technician / Manager Update:</span>
                    {r.notes}
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-400 flex justify-between items-center">
                <span>Ref #{r.id}</span>
                <span>{r.resolved_at ? `Resolved on ${new Date(r.resolved_at).toLocaleDateString()}` : 'In queue'}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* New Maintenance Request Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <div className="flex justify-between items-center pb-4 border-b border-slate-100">
              <h3 className="font-bold text-lg text-slate-800">Report a Maintenance Issue</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600 font-bold text-xl">
                &times;
              </button>
            </div>

            <form onSubmit={handleSubmit} className="py-4 space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Issue Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Leaking bathroom sink tap"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="Plumbing">Plumbing</option>
                    <option value="Electrical">Electrical</option>
                    <option value="HVAC / AC">HVAC / Heating</option>
                    <option value="Appliance">Appliance</option>
                    <option value="Carpentry / Locksmith">Carpentry / Locksmith</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Urgency Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="low">Low (Standard)</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Emergency / Urgent</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Detailed Description *</label>
                <textarea
                  required
                  rows={4}
                  placeholder="Describe where the issue is located, how long it has been occurring, and any access instructions for the technician..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="pt-4 border-t border-slate-100 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-semibold shadow transition"
                >
                  {submitting ? 'Submitting...' : 'Submit Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
export default TenantMaintenance
