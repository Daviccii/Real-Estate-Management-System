import React, { useEffect, useState } from 'react'
import { getMyViewings, updateViewingStatus } from '../../services/viewing'
import { Viewing } from '../../types'

export const AgentViewings: React.FC = () => {
  const [viewings, setViewings] = useState<Viewing[]>([])
  const [loading, setLoading] = useState(true)
  const [actionViewing, setActionViewing] = useState<Viewing | null>(null)
  const [newStatus, setNewStatus] = useState<'confirmed' | 'completed' | 'cancelled'>('confirmed')
  const [feedback, setFeedback] = useState('')
  const [saving, setSaving] = useState(false)

  const loadViewings = () => {
    getMyViewings()
      .then(setViewings)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadViewings()
  }, [])

  const handleStatusUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!actionViewing) return
    setSaving(true)
    try {
      await updateViewingStatus(actionViewing.id, {
        status: newStatus,
        feedback: feedback || undefined,
      })
      setActionViewing(null)
      loadViewings()
    } catch (err: any) {
      alert(err.message || 'Failed to update viewing status')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading tour schedule...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Property Tours & Viewings Schedule</h1>
          <p className="text-slate-500 text-sm mt-1">
            Confirmed and requested client walkthroughs with calendar anti-collision checks.
          </p>
        </div>
      </div>

      {viewings.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-100 text-center max-w-lg mx-auto mt-8 shadow-sm">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
            📅
          </div>
          <h2 className="text-xl font-bold text-slate-800">No Scheduled Viewings</h2>
          <p className="text-slate-500 text-sm mt-2">
            When clients book viewing slots on your listings, appointments will appear here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {viewings.map((v) => (
            <div key={v.id} className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className={`px-2.5 py-1 text-xs font-semibold rounded-full uppercase ${
                    v.status === 'confirmed' ? 'bg-emerald-100 text-emerald-800' :
                    v.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                    v.status === 'cancelled' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'
                  }`}>
                    {v.status}
                  </span>
                  <span className="text-xs font-bold text-slate-500">{v.viewing_date}</span>
                </div>

                <h3 className="font-bold text-lg text-slate-800">{v.property_name || `Property #${v.property_id}`}</h3>
                <div className="text-xs text-slate-500 mt-1">
                  ⏰ {v.start_time} - {v.end_time}
                </div>

                <div className="mt-4 p-3 bg-slate-50 rounded-xl text-xs space-y-1">
                  <div>
                    <span className="text-slate-400">Prospect:</span>{' '}
                    <span className="font-semibold text-slate-700">{v.prospect_name || `User #${v.prospect_id}`}</span>
                  </div>
                  {v.notes && (
                    <div className="text-slate-500 italic mt-1">"{v.notes}"</div>
                  )}
                </div>

                {v.feedback && (
                  <div className="mt-3 p-3 bg-teal-50 border border-teal-100 rounded-xl text-xs text-teal-900">
                    <span className="font-semibold block mb-0.5">Tour Feedback:</span>
                    {v.feedback}
                  </div>
                )}
              </div>

              <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-end gap-2">
                <button
                  onClick={() => {
                    setActionViewing(v)
                    setNewStatus('confirmed')
                    setFeedback('')
                  }}
                  className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold transition shadow-xs"
                >
                  Update Tour Status &rarr;
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Viewing Action Modal */}
      {actionViewing && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex justify-between items-center pb-4 border-b border-slate-100">
              <h3 className="font-bold text-lg text-slate-800">Update Tour Appointment</h3>
              <button onClick={() => setActionViewing(null)} className="text-slate-400 hover:text-slate-600 font-bold text-xl">
                &times;
              </button>
            </div>

            <form onSubmit={handleStatusUpdate} className="py-4 space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Tour Status</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value as any)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="confirmed">Confirm Appointment</option>
                  <option value="completed">Completed Tour</option>
                  <option value="cancelled">Cancel Appointment</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Client Feedback & Next Steps</label>
                <textarea
                  rows={3}
                  placeholder="e.g. Client loved the balcony view, planning to submit application..."
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="pt-4 border-t border-slate-100 flex justify-end gap-3">
                <button type="button" onClick={() => setActionViewing(null)} className="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl text-xs font-semibold">
                  Cancel
                </button>
                <button type="submit" disabled={saving} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow">
                  {saving ? 'Saving...' : 'Save Update'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
export default AgentViewings
