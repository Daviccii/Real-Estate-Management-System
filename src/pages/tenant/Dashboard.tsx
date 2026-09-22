import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getTenantDashboard, TenantDashboardData } from '../../services/tenant'
import { useAuth } from '../../contexts/AuthContext'

export const TenantDashboard: React.FC = () => {
  const { user } = useAuth()
  const [data, setData] = useState<TenantDashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getTenantDashboard()
      .then(setData)
      .catch((err) => setError(err.message || 'Failed to load tenant dashboard'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading your tenant dashboard...</div>
  }

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-teal-700 via-emerald-800 to-slate-900 rounded-2xl p-6 text-white shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="inline-block px-3 py-1 bg-emerald-500/20 text-emerald-300 rounded-full text-xs font-semibold uppercase tracking-wider mb-2">
              Tenant Resident Portal
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Welcome back, {user?.full_name || 'Resident'}</h1>
            <p className="text-emerald-100/80 text-sm mt-1">
              Manage your current home, rent payments, maintenance requests, and rental applications in one place.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/tenant/maintenance"
              className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-sm font-medium transition shadow"
            >
              + Request Maintenance
            </Link>
            <Link
              to="/tenant/payments"
              className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-xl text-sm font-medium backdrop-blur transition"
            >
              Pay Rent
            </Link>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Current Home</div>
          <div className="text-xl font-bold text-slate-800 mt-2 truncate">
            {data?.active_lease ? (data.active_lease.property_name || 'Active Lease') : 'No Active Lease'}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {data?.active_lease ? `Unit ${data.active_lease.unit_number || 'N/A'}` : 'Browse available listings to apply'}
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Pending Rent Due</div>
          <div className="text-xl font-bold text-slate-800 mt-2">
            {data?.pending_payments && data.pending_payments.length > 0
              ? `KSh ${data.pending_payments.reduce((acc, p) => acc + (parseFloat(p.amount) || 0), 0).toLocaleString()}`
              : 'KSh 0'}
          </div>
          <div className="text-xs text-emerald-600 font-medium mt-1">
            {data?.pending_payments?.length ? `${data.pending_payments.length} pending bill(s)` : 'All bills settled'}
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Active Maintenance</div>
          <div className="text-xl font-bold text-slate-800 mt-2">
            {data?.active_maintenance?.length || 0}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {data?.active_maintenance?.length ? 'Requests in progress' : 'No open repairs'}
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Rental Applications</div>
          <div className="text-xl font-bold text-slate-800 mt-2">
            {data?.applications?.length || 0}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            <Link to="/tenant/applications" className="text-teal-600 hover:underline">
              View application status &rarr;
            </Link>
          </div>
        </div>
      </div>

      {/* Tenancy & Payment Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Tenancy Summary */}
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-800">My Tenancy & Lease</h3>
              <Link to="/tenant/my-tenancy" className="text-xs text-teal-600 font-medium hover:underline">
                View Full Details
              </Link>
            </div>
            {data?.active_lease ? (
              <div className="space-y-3">
                <div className="flex justify-between py-2 border-b border-slate-50 text-sm">
                  <span className="text-slate-500">Property:</span>
                  <span className="font-medium text-slate-800">{data.active_lease.property_name || 'Residence'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-slate-50 text-sm">
                  <span className="text-slate-500">Unit Number:</span>
                  <span className="font-medium text-slate-800">{data.active_lease.unit_number || 'N/A'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-slate-50 text-sm">
                  <span className="text-slate-500">Monthly Rent:</span>
                  <span className="font-semibold text-emerald-600">KSh {data.active_lease.rent_amount}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-slate-50 text-sm">
                  <span className="text-slate-500">Lease Period:</span>
                  <span className="text-slate-700">{data.active_lease.start_date} to {data.active_lease.end_date}</span>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-400 text-sm">
                You do not have an active tenancy lease on record.
                <div className="mt-3">
                  <Link to="/rent" className="text-xs bg-slate-900 text-white px-3 py-1.5 rounded-lg font-medium">
                    Explore Rental Listings
                  </Link>
                </div>
              </div>
            )}
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100 flex gap-2">
            <Link to="/tenant/documents" className="flex-1 text-center py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-medium rounded-xl transition">
              Lease Agreement PDF
            </Link>
            <Link to="/tenant/messages" className="flex-1 text-center py-2 bg-teal-50 hover:bg-teal-100 text-teal-700 text-xs font-medium rounded-xl transition">
              Message Landlord
            </Link>
          </div>
        </div>

        {/* Recent Maintenance & Inquiries */}
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-800">Recent Maintenance Requests</h3>
              <Link to="/tenant/maintenance" className="text-xs text-teal-600 font-medium hover:underline">
                View All
              </Link>
            </div>
            {data?.active_maintenance && data.active_maintenance.length > 0 ? (
              <div className="divide-y divide-slate-100">
                {data.active_maintenance.slice(0, 3).map((m) => (
                  <div key={m.id} className="py-3 flex items-center justify-between">
                    <div>
                      <div className="font-medium text-sm text-slate-800">{m.title}</div>
                      <div className="text-xs text-slate-400 mt-0.5">Priority: {m.priority} • {m.category || 'General'}</div>
                    </div>
                    <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${
                      m.status === 'completed' ? 'bg-emerald-100 text-emerald-700' :
                      m.status === 'in_progress' ? 'bg-blue-100 text-blue-700' : 'bg-amber-100 text-amber-700'
                    }`}>
                      {m.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-slate-400 text-sm">
                No active maintenance requests. Everything in your home is running smoothly.
              </div>
            )}
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100">
            <Link
              to="/tenant/maintenance"
              className="block w-full text-center py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium rounded-xl transition"
            >
              Report a New Issue
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
export default TenantDashboard
