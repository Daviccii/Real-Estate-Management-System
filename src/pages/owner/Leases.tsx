import React, { useEffect, useState } from 'react'
import { getOwnerProperties } from '../../services/owner'
import { leaseService } from '../../services/lease'
import { Lease, Property } from '../../types'

export const OwnerLeases: React.FC = () => {
  const [leases, setLeases] = useState<Lease[]>([])
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([leaseService.list(), getOwnerProperties()])
      .then(([allLeases, props]) => {
        setProperties(props)
        const propIds = new Set(props.map((p) => p.id))
        const ownerLeases = allLeases.filter((l) => propIds.has(l.property_id))
        setLeases(ownerLeases)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading active leases...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Lease Portfolio Management</h1>
          <p className="text-slate-500 text-sm mt-1">
            Active tenancies, expiration schedules, rent amounts, and security deposits.
          </p>
        </div>
      </div>

      {leases.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-100 text-center max-w-lg mx-auto mt-8 shadow-sm">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
            📜
          </div>
          <h2 className="text-xl font-bold text-slate-800">No Leases Found</h2>
          <p className="text-slate-500 text-sm mt-2">
            Once applications are approved and converted, active leases will appear here.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <h2 className="font-bold text-slate-800">Executed Leases</h2>
            <span className="text-xs text-slate-400 font-medium">{leases.length} lease(s)</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50/80 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                  <th className="py-3 px-5">Lease ID</th>
                  <th className="py-3 px-5">Property</th>
                  <th className="py-3 px-5">Tenant</th>
                  <th className="py-3 px-5">Term Range</th>
                  <th className="py-3 px-5">Monthly Rent</th>
                  <th className="py-3 px-5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {leases.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-50/50 transition">
                    <td className="py-3.5 px-5 font-mono text-xs font-semibold text-slate-800">
                      #{l.id}
                    </td>
                    <td className="py-3.5 px-5 font-medium text-slate-800">
                      {properties.find((p) => p.id === l.property_id)?.name || `Property #${l.property_id}`}
                    </td>
                    <td className="py-3.5 px-5 text-xs text-slate-600">
                      {l.tenant_name || `Tenant #${l.tenant_id}`}
                    </td>
                    <td className="py-3.5 px-5 text-xs text-slate-500">
                      {l.start_date} &rarr; {l.end_date}
                    </td>
                    <td className="py-3.5 px-5 font-bold text-emerald-700">
                      KSh {parseFloat(l.rent_amount || '0').toLocaleString()}
                    </td>
                    <td className="py-3.5 px-5">
                      <span className={`px-2.5 py-1 text-xs font-semibold rounded-full uppercase ${
                        l.status === 'active' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'
                      }`}>
                        {l.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
export default OwnerLeases
