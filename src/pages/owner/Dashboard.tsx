import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getOwnerPortfolioSummary, getOwnerProperties, OwnerPortfolioSummary } from '../../services/owner'
import { Property } from '../../types'
import { useAuth } from '../../contexts/AuthContext'

export const OwnerDashboard: React.FC = () => {
  const { user } = useAuth()
  const [summary, setSummary] = useState<OwnerPortfolioSummary | null>(null)
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getOwnerPortfolioSummary(), getOwnerProperties()])
      .then(([s, p]) => {
        setSummary(s)
        setProperties(p)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading landlord & investor portfolio...</div>
  }

  return (
    <div className="space-y-6">
      {/* Portfolio Header */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-6 text-white shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="inline-block px-3 py-1 bg-indigo-500/20 text-indigo-300 rounded-full text-xs font-semibold uppercase tracking-wider mb-2">
              Property Owner & Asset Workspace
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Portfolio Performance: {user?.full_name || 'Owner'}</h1>
            <p className="text-slate-300 text-sm mt-1">
              Asset tracking, yield metrics, tenancy occupancy, and manager oversight across your real estate holdings.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/owner/financials"
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-medium transition shadow"
            >
              Financial Ledger & ROI
            </Link>
            <Link
              to="/owner/properties"
              className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-xl text-sm font-medium backdrop-blur transition"
            >
              Manage Properties
            </Link>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Properties Owned</div>
          <div className="text-2xl font-bold text-slate-800 mt-2">{summary?.total_properties || 0}</div>
          <div className="text-xs text-slate-500 mt-1">{summary?.total_units || 0} total units</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Portfolio Occupancy</div>
          <div className="text-2xl font-bold text-emerald-600 mt-2">{summary?.occupancy_rate || 0}%</div>
          <div className="text-xs text-slate-500 mt-1">
            {summary?.occupied_units || 0} occupied • {summary?.vacant_units || 0} vacant
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Revenue Collected</div>
          <div className="text-2xl font-bold text-indigo-700 mt-2">
            KSh {(summary?.total_revenue_collected || 0).toLocaleString()}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            Pending: KSh {(summary?.pending_payments || 0).toLocaleString()}
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Active Maintenance</div>
          <div className="text-2xl font-bold text-amber-600 mt-2">{summary?.active_maintenance || 0}</div>
          <div className="text-xs text-slate-500 mt-1">
            <Link to="/owner/maintenance" className="text-indigo-600 hover:underline">
              Inspect work orders &rarr;
            </Link>
          </div>
        </div>
      </div>

      {/* Properties List */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="font-bold text-slate-800">Your Property Holdings</h2>
            <p className="text-xs text-slate-400 mt-0.5">Assigned managers, leasing status, and unit breakdown</p>
          </div>
          <Link to="/owner/properties" className="text-xs font-semibold text-indigo-600 hover:underline">
            View All &rarr;
          </Link>
        </div>

        {properties.length === 0 ? (
          <div className="py-8 text-center text-slate-400 text-sm">
            No properties registered under your account yet.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {properties.map((p) => (
              <div key={p.id} className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/50 transition">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-slate-100 overflow-hidden flex-shrink-0 flex items-center justify-center font-bold text-slate-400">
                    {p.image_url ? (
                      <img src={p.image_url} alt={p.name} className="w-full h-full object-cover" />
                    ) : (
                      '🏢'
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-base text-slate-800">{p.name}</h3>
                      {p.is_verified && (
                        <span className="text-[10px] px-2 py-0.5 bg-emerald-100 text-emerald-800 font-bold rounded-full">
                          Verified
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      {p.address || p.city || 'Nairobi'} • {p.property_type || 'Residential'} • {p.units_count || 1} Unit(s)
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="font-bold text-sm text-slate-800">{p.price_label || `KSh ${p.price || 0}`}</div>
                    <div className="text-[11px] text-slate-400">{p.purpose === 'rent' ? 'Monthly Target' : 'Valuation'}</div>
                  </div>
                  <Link
                    to={`/owner/properties`}
                    className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
                  >
                    Manage
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
export default OwnerDashboard
