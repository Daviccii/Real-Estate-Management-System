import React, { useEffect, useState } from 'react'
import { getOwnerProperties } from '../../services/owner'
import { leaseService } from '../../services/lease'
import { Lease, Property } from '../../types'

export const OwnerTenants: React.FC = () => {
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
    return <div className="p-8 text-center text-slate-500">Loading resident directory...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Resident & Tenant Directory</h1>
        <p className="text-slate-500 text-sm mt-1">
          Active tenants occupying units across your investment properties.
        </p>
      </div>

      {leases.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-100 text-center max-w-lg mx-auto mt-8 shadow-sm">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
            👥
          </div>
          <h2 className="text-xl font-bold text-slate-800">No Active Tenants</h2>
          <p className="text-slate-500 text-sm mt-2">
            Tenants with active leases in your properties will be listed here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {leases.map((l) => (
            <div key={l.id} className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-lg flex-shrink-0">
                {(l.tenant_name || 'T')[0]}
              </div>
              <div className="overflow-hidden">
                <h3 className="font-bold text-base text-slate-800 truncate">{l.tenant_name || `Tenant #${l.tenant_id}`}</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {properties.find((p) => p.id === l.property_id)?.name || 'Property'} • Unit {l.unit_number || 'N/A'}
                </p>
                <div className="mt-2 text-xs font-semibold text-emerald-700">
                  Rent: KSh {parseFloat(l.rent_amount || '0').toLocaleString()}/mo
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
export default OwnerTenants
