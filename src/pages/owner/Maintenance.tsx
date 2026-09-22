import React, { useEffect, useState } from 'react'
import { getOwnerMaintenance } from '../../services/owner'
import { Maintenance } from '../../types'

export const OwnerMaintenance: React.FC = () => {
  const [tickets, setTickets] = useState<Maintenance[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getOwnerMaintenance()
      .then(setTickets)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading maintenance oversight...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Maintenance Oversight & Work Orders</h1>
        <p className="text-slate-500 text-sm mt-1">
          Monitor repairs, contractor dispatch, and asset depreciation across your portfolio.
        </p>
      </div>

      {tickets.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-100 text-center max-w-lg mx-auto mt-8 shadow-sm">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
            🛠️
          </div>
          <h2 className="text-xl font-bold text-slate-800">All Systems Operational</h2>
          <p className="text-slate-500 text-sm mt-2">
            No open maintenance tickets found for your properties.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {tickets.map((t) => (
            <div key={t.id} className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className={`px-2.5 py-1 text-xs font-semibold rounded-full uppercase ${
                    t.status === 'completed' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                  }`}>
                    {t.status}
                  </span>
                  <span className="text-xs text-slate-400">Ref #{t.id}</span>
                </div>
                <h3 className="font-bold text-base text-slate-800">{t.title}</h3>
                <div className="text-xs text-slate-400 mt-1">{t.property_name || 'Property'} • Unit {t.unit_number || 'N/A'}</div>

                {t.description && (
                  <p className="mt-3 text-xs text-slate-600 bg-slate-50 p-3 rounded-xl">
                    {t.description}
                  </p>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex justify-between items-center text-xs text-slate-500">
                <span>Priority: <strong className="capitalize">{t.priority}</strong></span>
                <span>{t.cost ? `Cost: KSh ${t.cost}` : 'Cost: Pending quote'}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
export default OwnerMaintenance
