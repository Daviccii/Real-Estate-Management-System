import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getWorkOrders } from '../../services/serviceMarketplace'
import { MaintenanceWorkOrder } from '../../types'
import { useAuth } from '../../contexts/AuthContext'

export const ProviderDashboard: React.FC = () => {
  const { user } = useAuth()
  const [workOrders, setWorkOrders] = useState<MaintenanceWorkOrder[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getWorkOrders()
      .then(setWorkOrders)
      .finally(() => setLoading(false))
  }, [])

  const activeOrders = workOrders.filter((w) => w.status === 'assigned' || w.status === 'in_progress')
  const completedOrders = workOrders.filter((w) => w.status === 'completed' || w.status === 'verified')

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading contractor dispatch board...</div>
  }

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-amber-900 via-orange-950 to-slate-900 rounded-2xl p-6 text-white shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="inline-block px-3 py-1 bg-amber-500/20 text-amber-300 rounded-full text-xs font-semibold uppercase tracking-wider mb-2">
              Contractor & Service Marketplace
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Contractor Hub: {user?.full_name || 'Service Partner'}</h1>
            <p className="text-amber-100/80 text-sm mt-1">
              Field repair dispatches, competitive job quotes, before/after site inspection logs, and billing.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/provider/work-orders"
              className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-xl text-sm font-medium transition shadow"
            >
              Active Work Orders
            </Link>
            <Link
              to="/provider/quotes"
              className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-xl text-sm font-medium backdrop-blur transition"
            >
              Quote Requests
            </Link>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Active Work Orders</div>
          <div className="text-2xl font-bold text-amber-600 mt-2">{activeOrders.length}</div>
          <div className="text-xs text-slate-500 mt-1">Assigned & In-Progress tasks</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Completed Jobs</div>
          <div className="text-2xl font-bold text-emerald-600 mt-2">{completedOrders.length}</div>
          <div className="text-xs text-slate-500 mt-1">Verified work completions</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Dispatches</div>
          <div className="text-2xl font-bold text-slate-800 mt-2">{workOrders.length}</div>
          <div className="text-xs text-slate-500 mt-1">
            <Link to="/provider/work-orders" className="text-amber-600 hover:underline">
              View all orders &rarr;
            </Link>
          </div>
        </div>
      </div>

      {/* Active Work Orders */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-bold text-slate-800">Assigned Field Tasks</h2>
          <Link to="/provider/work-orders" className="text-xs font-semibold text-amber-600 hover:underline">
            View All &rarr;
          </Link>
        </div>

        {activeOrders.length === 0 ? (
          <div className="py-8 text-center text-slate-400 text-sm">
            No active work orders pending execution.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {activeOrders.map((wo) => (
              <div key={wo.id} className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-amber-100 text-amber-800">
                      {wo.status.replace('_', ' ')}
                    </span>
                    <h3 className="font-bold text-base text-slate-800">{wo.request_title || `Work Order #${wo.id}`}</h3>
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    Property: {wo.property_name || `Property #${wo.property_id}`} • Scheduled: {wo.scheduled_date || 'ASAP'}
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="font-bold text-sm text-slate-800">
                    {wo.approved_budget ? `KSh ${wo.approved_budget}` : 'Budget approved'}
                  </div>
                  <Link
                    to="/provider/work-orders"
                    className="px-3 py-1.5 bg-slate-900 text-white rounded-xl text-xs font-medium hover:bg-slate-800 transition"
                  >
                    Open Task
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
export default ProviderDashboard
