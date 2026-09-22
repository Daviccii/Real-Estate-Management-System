import React, { useEffect, useState } from 'react'
import { getWorkOrders, updateWorkOrderStatus } from '../../services/serviceMarketplace'
import { MaintenanceWorkOrder } from '../../types'

export const ProviderWorkOrders: React.FC = () => {
  const [workOrders, setWorkOrders] = useState<MaintenanceWorkOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedOrder, setSelectedOrder] = useState<MaintenanceWorkOrder | null>(null)
  const [newStatus, setNewStatus] = useState('in_progress')
  const [completionNotes, setCompletionNotes] = useState('')
  const [updating, setUpdating] = useState(false)

  const loadWorkOrders = () => {
    getWorkOrders()
      .then(setWorkOrders)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadWorkOrders()
  }, [])

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedOrder) return
    setUpdating(true)
    try {
      await updateWorkOrderStatus(selectedOrder.id, newStatus, completionNotes || undefined)
      setSelectedOrder(null)
      loadWorkOrders()
    } catch (err: any) {
      alert(err.message || 'Failed to update work order')
    } finally {
      setUpdating(false)
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading work orders...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Field Work Orders & Job Execution</h1>
          <p className="text-slate-500 text-sm mt-1">
            Assigned repair dispatches, on-site status updates, and completion documentation.
          </p>
        </div>
      </div>

      {workOrders.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-100 text-center max-w-lg mx-auto mt-8 shadow-sm">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
            🧰
          </div>
          <h2 className="text-xl font-bold text-slate-800">No Dispatched Work Orders</h2>
          <p className="text-slate-500 text-sm mt-2">
            When landlords or managers accept your quotes or dispatch maintenance jobs, they will appear here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workOrders.map((wo) => (
            <div key={wo.id} className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className={`px-2.5 py-1 text-xs font-semibold rounded-full uppercase ${
                    wo.status === 'completed' || wo.status === 'verified'
                      ? 'bg-emerald-100 text-emerald-800'
                      : wo.status === 'in_progress'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-amber-100 text-amber-800'
                  }`}>
                    {wo.status.replace('_', ' ')}
                  </span>
                  <span className="text-xs text-slate-400">Order #{wo.id}</span>
                </div>

                <h3 className="font-bold text-lg text-slate-800">{wo.request_title || `Work Order #${wo.id}`}</h3>
                <div className="text-xs text-slate-500 mt-1">
                  Property: {wo.property_name || `Property #${wo.property_id}`}
                </div>

                <div className="mt-4 p-3.5 bg-slate-50 rounded-xl space-y-1 text-xs text-slate-600">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Scheduled Date:</span>
                    <span className="font-medium text-slate-700">{wo.scheduled_date || 'ASAP'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Approved Budget:</span>
                    <span className="font-bold text-emerald-700">KSh {wo.approved_budget || '0'}</span>
                  </div>
                </div>

                {wo.notes && (
                  <p className="mt-3 text-xs text-slate-600 bg-slate-50 p-2.5 rounded-xl">
                    <span className="font-semibold block mb-0.5">Instructions:</span>
                    {wo.notes}
                  </p>
                )}

                {wo.completion_notes && (
                  <div className="mt-3 p-3 bg-emerald-50 border border-emerald-100 rounded-xl text-xs text-emerald-900">
                    <span className="font-semibold block mb-0.5">Completion Notes:</span>
                    {wo.completion_notes}
                  </div>
                )}
              </div>

              <div className="mt-5 pt-4 border-t border-slate-100 flex justify-end">
                <button
                  onClick={() => {
                    setSelectedOrder(wo)
                    setNewStatus(wo.status === 'assigned' ? 'in_progress' : 'completed')
                    setCompletionNotes(wo.completion_notes || '')
                  }}
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold transition shadow-sm"
                >
                  Update Job Status &rarr;
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Work Order Update Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex justify-between items-center pb-4 border-b border-slate-100">
              <h3 className="font-bold text-lg text-slate-800">Update Job #{selectedOrder.id}</h3>
              <button onClick={() => setSelectedOrder(null)} className="text-slate-400 hover:text-slate-600 font-bold text-xl">
                &times;
              </button>
            </div>

            <form onSubmit={handleUpdate} className="py-4 space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Execution Status</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                >
                  <option value="assigned">Assigned / Queued</option>
                  <option value="in_progress">In Progress (Technician On-Site)</option>
                  <option value="completed">Completed (Work Finished)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Completion Notes / Diagnostics</label>
                <textarea
                  rows={4}
                  placeholder="Describe parts replaced, tests conducted, and recommendations..."
                  value={completionNotes}
                  onChange={(e) => setCompletionNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>

              <div className="pt-4 border-t border-slate-100 flex justify-end gap-3">
                <button type="button" onClick={() => setSelectedOrder(null)} className="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl text-xs font-semibold">
                  Cancel
                </button>
                <button type="submit" disabled={updating} className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold shadow">
                  {updating ? 'Saving...' : 'Submit Job Update'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
export default ProviderWorkOrders
