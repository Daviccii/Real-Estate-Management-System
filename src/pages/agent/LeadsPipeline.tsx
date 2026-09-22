import React, { useEffect, useState } from 'react'
import { getLeads, createLead, updateLeadStage } from '../../services/lead'
import { Lead } from '../../types'

const STAGES: { id: Lead['stage']; label: string; color: string }[] = [
  { id: 'new', label: 'New Inquiries', color: 'border-slate-300 bg-slate-50' },
  { id: 'contacted', label: 'Contacted', color: 'border-blue-300 bg-blue-50/50' },
  { id: 'interested', label: 'Interested', color: 'border-indigo-300 bg-indigo-50/50' },
  { id: 'viewing', label: 'Tour Scheduled', color: 'border-purple-300 bg-purple-50/50' },
  { id: 'applied', label: 'Applied', color: 'border-amber-300 bg-amber-50/50' },
  { id: 'approved', label: 'Approved', color: 'border-teal-300 bg-teal-50/50' },
  { id: 'closed', label: 'Closed Deal', color: 'border-emerald-300 bg-emerald-50/50' },
  { id: 'lost', label: 'Lost / Inactive', color: 'border-red-300 bg-red-50/50' },
]

export const AgentLeadsPipeline: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [prospectName, setProspectName] = useState('')
  const [prospectEmail, setProspectEmail] = useState('')
  const [prospectPhone, setProspectPhone] = useState('')
  const [budget, setBudget] = useState('')
  const [notes, setNotes] = useState('')
  const [creating, setCreating] = useState(false)

  const loadLeads = () => {
    getLeads()
      .then(setLeads)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadLeads()
  }, [])

  const handleStageChange = async (leadId: number, nextStage: Lead['stage']) => {
    try {
      await updateLeadStage(leadId, { stage: nextStage })
      setLeads((prev) =>
        prev.map((l) => (l.id === leadId ? { ...l, stage: nextStage } : l))
      )
    } catch (err: any) {
      alert(err.message || 'Failed to update lead stage')
    }
  }

  const handleCreateLead = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!prospectName.trim()) return
    setCreating(true)
    try {
      const created = await createLead({
        prospect_name: prospectName,
        prospect_email: prospectEmail || undefined,
        prospect_phone: prospectPhone || undefined,
        estimated_budget: budget || undefined,
        notes: notes || undefined,
        stage: 'new',
      })
      setLeads((prev) => [created, ...prev])
      setShowModal(false)
      setProspectName('')
      setProspectEmail('')
      setProspectPhone('')
      setBudget('')
      setNotes('')
    } catch (err: any) {
      alert(err.message || 'Failed to create lead')
    } finally {
      setCreating(false)
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading CRM Pipeline...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Agent CRM & Deal Pipeline</h1>
          <p className="text-slate-500 text-sm mt-1">
            Track prospective client journeys from initial inquiry to lease execution and commission payout.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-medium transition shadow-sm"
        >
          + Add Prospective Lead
        </button>
      </div>

      {/* Kanban Columns */}
      <div className="flex gap-4 overflow-x-auto pb-6">
        {STAGES.map((col) => {
          const colLeads = leads.filter((l) => l.stage === col.id)
          return (
            <div
              key={col.id}
              className="flex-shrink-0 w-72 bg-slate-100/70 rounded-2xl p-4 flex flex-col justify-between max-h-[75vh]"
            >
              <div>
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200">
                  <span className="font-bold text-xs uppercase text-slate-700 tracking-wider">
                    {col.label}
                  </span>
                  <span className="text-xs font-bold px-2 py-0.5 bg-white text-slate-600 rounded-full shadow-xs">
                    {colLeads.length}
                  </span>
                </div>

                <div className="space-y-3 overflow-y-auto max-h-[60vh] pr-1">
                  {colLeads.map((lead) => (
                    <div
                      key={lead.id}
                      className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs hover:shadow-md transition space-y-2"
                    >
                      <div className="font-bold text-sm text-slate-800">{lead.prospect_name || 'Anonymous Client'}</div>
                      <div className="text-xs text-slate-500 space-y-0.5">
                        {lead.prospect_phone && <div>📞 {lead.prospect_phone}</div>}
                        {lead.prospect_email && <div>✉️ {lead.prospect_email}</div>}
                        {lead.estimated_budget && (
                          <div className="font-semibold text-emerald-700">💰 Budget: KSh {lead.estimated_budget}</div>
                        )}
                        {lead.property_name && (
                          <div className="text-[11px] text-blue-600 truncate">🏠 {lead.property_name}</div>
                        )}
                      </div>

                      {lead.notes && (
                        <p className="text-[11px] text-slate-400 bg-slate-50 p-2 rounded-lg line-clamp-2">
                          {lead.notes}
                        </p>
                      )}

                      {/* Stage Selector */}
                      <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
                        <span className="text-[10px] text-slate-400">Move:</span>
                        <select
                          value={lead.stage}
                          onChange={(e) => handleStageChange(lead.id, e.target.value as any)}
                          className="text-[11px] bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 font-medium text-slate-700 focus:outline-none"
                        >
                          {STAGES.map((s) => (
                            <option key={s.id} value={s.id}>
                              {s.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  ))}

                  {colLeads.length === 0 && (
                    <div className="py-8 text-center text-xs text-slate-400">No leads in this stage</div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Add Lead Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex justify-between items-center pb-4 border-b border-slate-100">
              <h3 className="font-bold text-lg text-slate-800">Add New CRM Lead</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600 font-bold text-xl">
                &times;
              </button>
            </div>

            <form onSubmit={handleCreateLead} className="py-4 space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Prospect Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. John Doe"
                  value={prospectName}
                  onChange={(e) => setProspectName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Email</label>
                  <input
                    type="email"
                    placeholder="client@email.com"
                    value={prospectEmail}
                    onChange={(e) => setProspectEmail(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Phone</label>
                  <input
                    type="tel"
                    placeholder="+254 700 000000"
                    value={prospectPhone}
                    onChange={(e) => setProspectPhone(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Estimated Budget (KSh)</label>
                <input
                  type="text"
                  placeholder="e.g. 60000"
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Client Preferences / Notes</label>
                <textarea
                  rows={3}
                  placeholder="Looking for 2-bedroom with gym, moving next month..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                  disabled={creating}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow transition"
                >
                  {creating ? 'Adding Lead...' : 'Create Lead'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
export default AgentLeadsPipeline
