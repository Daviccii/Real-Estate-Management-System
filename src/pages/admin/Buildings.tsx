import React, { useEffect, useState } from 'react'
import { getBuildings, createBuilding, deleteBuilding } from '../../services/building'
import { getProperties } from '../../services/property'
import { Building, Property } from '../../types'

export const AdminBuildings: React.FC = () => {
  const [buildings, setBuildings] = useState<Building[]>([])
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  // Form state
  const [propertyId, setPropertyId] = useState<number | ''>('')
  const [name, setName] = useState('')
  const [totalFloors, setTotalFloors] = useState<number>(4)
  const [unitsCount, setUnitsCount] = useState<number>(16)
  const [yearBuilt, setYearBuilt] = useState<number>(2023)
  const [amenities, setAmenities] = useState('High-speed lifts, CCTV security, backup generator, rooftop terrace')
  const [description, setDescription] = useState('')

  const loadData = async () => {
    setLoading(true)
    try {
      const [bData, pData] = await Promise.all([
        getBuildings(),
        getProperties()
      ])
      setBuildings(bData)
      setProperties(pData)
      if (pData.length > 0 && propertyId === '') {
        setPropertyId(pData[0].id)
      }
    } catch (err: any) {
      console.error('Failed to load buildings data', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!propertyId || !name.trim()) return
    setSubmitting(true)
    try {
      await createBuilding({
        property_id: Number(propertyId),
        name,
        total_floors: Number(totalFloors),
        units_count: Number(unitsCount),
        year_built: Number(yearBuilt),
        amenities,
        description
      })
      setShowModal(false)
      setName('')
      setDescription('')
      await loadData()
    } catch (err: any) {
      alert(err.message || 'Failed to create building')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to remove this building/block record?')) return
    try {
      await deleteBuilding(id)
      await loadData()
    } catch (err: any) {
      alert(err.message || 'Failed to delete building')
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-6 text-white shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="inline-block px-3 py-1 bg-indigo-500/20 text-indigo-300 rounded-full text-xs font-semibold uppercase tracking-wider mb-2">
              Multi-Unit Complexes & Estates
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Buildings & Block Management</h1>
            <p className="text-indigo-100/80 text-sm mt-1">
              Structure residential towers, commercial wings, floor levels, and unit clusters across managed properties.
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold shadow transition flex items-center gap-2 self-start md:self-auto"
          >
            <span>+</span> Add Building / Block
          </button>
        </div>
      </div>

      {/* Buildings Table */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-12 text-center text-slate-400 text-sm">Loading buildings registry...</div>
        ) : buildings.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-sm">
            No building blocks registered yet. Click "Add Building / Block" to define multi-unit structures.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-100 text-slate-400 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Building / Block Name</th>
                  <th className="py-3 px-4">Parent Property</th>
                  <th className="py-3 px-4">Floors</th>
                  <th className="py-3 px-4">Units Count</th>
                  <th className="py-3 px-4">Year Built</th>
                  <th className="py-3 px-4">Amenities</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {buildings.map((b) => (
                  <tr key={b.id} className="hover:bg-slate-50/50 transition">
                    <td className="py-3 px-4 font-bold text-slate-800 text-sm">{b.name}</td>
                    <td className="py-3 px-4 font-medium text-slate-600">
                      {b.property_title || `Property #${b.property_id}`}
                    </td>
                    <td className="py-3 px-4 text-slate-600">{b.total_floors || '—'} Floors</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-full font-semibold bg-indigo-50 text-indigo-700">
                        {b.units_count || 0} Units
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-600">{b.year_built || '—'}</td>
                    <td className="py-3 px-4 text-slate-500 max-w-xs truncate">{b.amenities || '—'}</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleDelete(b.id)}
                        className="text-rose-600 hover:text-rose-800 font-semibold text-xs"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="font-bold text-lg text-slate-800">Register New Building / Block</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600 font-bold">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Parent Property *</label>
                <select
                  required
                  value={propertyId}
                  onChange={(e) => setPropertyId(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {properties.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.title} ({p.city || 'N/A'})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Building / Block Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Tower A / Block B / Executive Wing"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Total Floors</label>
                  <input
                    type="number"
                    value={totalFloors}
                    onChange={(e) => setTotalFloors(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Units Count</label>
                  <input
                    type="number"
                    value={unitsCount}
                    onChange={(e) => setUnitsCount(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Year Built</label>
                  <input
                    type="number"
                    value={yearBuilt}
                    onChange={(e) => setYearBuilt(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Building Amenities</label>
                <input
                  type="text"
                  value={amenities}
                  onChange={(e) => setAmenities(e.target.value)}
                  placeholder="e.g. Elevators, CCTV, Gym, Rooftop lounge"
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Additional architectural or access notes..."
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow transition"
                >
                  {submitting ? 'Creating...' : 'Register Building'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default AdminBuildings
