import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAgentWorkspace, AgentWorkspaceData } from '../../services/agent'
import { useAuth } from '../../contexts/AuthContext'

export const AgentDashboard: React.FC = () => {
  const { user } = useAuth()
  const [data, setData] = useState<AgentWorkspaceData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAgentWorkspace()
      .then(setData)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading Agent workspace...</div>
  }

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 rounded-2xl p-6 text-white shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="inline-block px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-xs font-semibold uppercase tracking-wider mb-2">
              Real Estate Agent Command Center
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Agent Workspace: {user?.full_name || 'Agent'}</h1>
            <p className="text-blue-100/80 text-sm mt-1">
              Active CRM leads, tour appointments, listing syndication, and commission earnings.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/agent/leads"
              className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-sm font-medium transition shadow"
            >
              CRM Pipeline Kanban
            </Link>
            <Link
              to="/agent/viewings"
              className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-xl text-sm font-medium backdrop-blur transition"
            >
              Tour Schedule
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total CRM Leads</div>
          <div className="text-2xl font-bold text-slate-800 mt-2">{data?.total_leads || 0}</div>
          <div className="text-xs text-blue-600 font-medium mt-1">
            <Link to="/agent/leads">Manage Pipeline &rarr;</Link>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Active Listings</div>
          <div className="text-2xl font-bold text-slate-800 mt-2">{data?.active_listings || 0}</div>
          <div className="text-xs text-slate-500 mt-1">
            <Link to="/agent/listings" className="text-blue-600 hover:underline">View listings</Link>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Upcoming Tours</div>
          <div className="text-2xl font-bold text-indigo-600 mt-2">{data?.upcoming_viewings || 0}</div>
          <div className="text-xs text-slate-500 mt-1">
            <Link to="/agent/viewings" className="text-blue-600 hover:underline">View appointments</Link>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Pending Apps</div>
          <div className="text-2xl font-bold text-amber-600 mt-2">{data?.pending_applications || 0}</div>
          <div className="text-xs text-slate-500 mt-1">
            <Link to="/agent/applications" className="text-blue-600 hover:underline">Review queue</Link>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Commissions Earned</div>
          <div className="text-2xl font-bold text-emerald-600 mt-2">
            KSh {(data?.total_commissions_earned || 0).toLocaleString()}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            <Link to="/agent/commissions" className="text-blue-600 hover:underline">Ledger</Link>
          </div>
        </div>
      </div>

      {/* Quick Access Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-base text-slate-800 mb-2">Lead Pipeline Kanban Board</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Track client inquiries from first contact through private viewing, rental application, and closing with automated commission tracking.
            </p>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100">
            <Link to="/agent/leads" className="block text-center py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold transition">
              Open CRM Pipeline &rarr;
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-base text-slate-800 mb-2">Client Tour & Viewing Manager</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Automated 30-minute viewing slots with anti-collision scheduling. Approve, reschedule, or log viewing feedback from prospective tenants.
            </p>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100">
            <Link to="/agent/viewings" className="block text-center py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold transition">
              Manage Viewings Schedule &rarr;
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
export default AgentDashboard
