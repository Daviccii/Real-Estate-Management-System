import React, { useEffect, useState } from 'react'
import { getOwnerProperties } from '../../services/owner'
import { unitService } from '../../services/unit'
import { Unit, Property } from '../../types'

export const OwnerUnits: React.FC = () => {
  const [properties, setProperties] = useState<Property[]>([])
  const [selectedPropertyId, setSelectedPropertyId] = useState<number | null>(null)
  const [units, setUnits] = useState<Unit[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getOwnerProperties()
      .then((props) => {
        setProperties(props)
        if (props.length > 0) {
          setSelectedPropertyId(props[0].id)
        }
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (selectedPropertyId) {
      unitService.list(selectedPropertyId).then(setUnits)
    }
  }, [selectedPropertyId])

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading units...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Unit Inventory & Availability</h1>
          <p className="text-slate-500 text-sm mt-1">
            Door-by-door unit tracking, rent prices, and occupancy states.
          </p>
        </div>
        {properties.length > 0 && (
          <div>
            <select
              value={selectedPropertyId || ''}
              onChange={(e) => setSelectedPropertyId(Number(e.target.value))}
              className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {properties.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {units.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-100 text-center max-w-lg mx-auto mt-8 shadow-sm">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
            🚪
          </div>
          <h2 className="text-xl font-bold text-slate-800">No Units Configured</h2>
          <p className="text-slate-500 text-sm mt-2">
            No specific units have been added to this property yet.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {units.map((u) => (
            <div key={u.id} className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold text-base text-slate-800">Unit {u.unit_number}</span>
                <span className={`px-2 py-0.5 text-xs rounded-full font-bold uppercase ${
                  u.status === 'occupied' ? 'bg-blue-100 text-blue-800' : 'bg-emerald-100 text-emerald-800'
                }`}>
                  {u.status}
                </span>
              </div>
              <div className="text-xs text-slate-500">{u.unit_type || 'Apartment'} • {u.bedrooms || 0} Bed / {u.bathrooms || 0} Bath</div>
              <div className="mt-3 pt-3 border-t border-slate-50 flex justify-between items-center">
                <span className="text-xs text-slate-400">Target Rent</span>
                <span className="font-bold text-sm text-emerald-700">KSh {u.rent || 'N/A'}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
export default OwnerUnits
