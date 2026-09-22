import React, { useEffect, useState } from 'react'
import { getOwnerProperties, assignPropertyStaff } from '../../services/owner'
import { Property } from '../../types'

export const OwnerProperties: React.FC = () => {
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedProp, setSelectedProp] = useState<Property | null>(null)
  const [managerId, setManagerId] = useState<string>('')
  const [agentId, setAgentId] = useState<string>('')
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  const loadProperties = () => {
    getOwnerProperties()
      .then(setProperties)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadProperties()
  }, [])

  const handleOpenAssign = (p: Property) => {
    setSelectedProp(p)
    setManagerId(p.manager_id ? String(p.manager_id) : '')
    setAgentId(p.agent_id ? String(p.agent_id) : '')
  }

  const handleSaveAssign = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedProp) return
    setSaving(true)
    try {
      await assignPropertyStaff(selectedProp.id, {
        manager_id: managerId ? parseInt(managerId) : null,
        agent_id: agentId ? parseInt(agentId) : null,
      })
      setMsg('Staff assigned successfully!')
      setSelectedProp(null)
      loadProperties()
    } catch (err: any) {
      alert(err.message || 'Failed to update assignment')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading your properties...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">My Properties & Asset Management</h1>
          <p className="text-slate-500 text-sm mt-1">
            Assign dedicated property managers, marketing agents, and monitor unit operations.
          </p>
        </div>
      </div>

      {msg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm">
          {msg}
        </div>
      )}

      {properties.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-100 text-center max-w-lg mx-auto mt-8 shadow-sm">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
            🏢
          </div>
          <h2 className="text-xl font-bold text-slate-800">No Properties Registered</h2>
          <p className="text-slate-500 text-sm mt-2">
            Properties owned by your profile will be listed here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {properties.map((p) => (
            <div key={p.id} className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-slate-100 text-slate-700 uppercase tracking-wider">
                    {p.status}
                  </span>
                  {p.is_verified && (
                    <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-xs font-bold rounded-full">
                      ✓ Verified Asset
                    </span>
                  )}
                </div>

                <h3 className="font-bold text-lg text-slate-800">{p.name}</h3>
                <p className="text-xs text-slate-400 mt-0.5">{p.address || p.city || 'Nairobi'} • {p.property_type || 'Residential'}</p>

                <div className="mt-4 p-3 bg-slate-50 rounded-xl space-y-1.5 text-xs text-slate-600">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Total Units:</span>
                    <span className="font-medium text-slate-700">{p.units_count || 1}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Assigned Manager:</span>
                    <span className="font-medium text-slate-700">{p.manager_id ? `Manager #${p.manager_id}` : 'Unassigned'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Listing Agent:</span>
                    <span className="font-medium text-slate-700">{p.agent_id ? `Agent #${p.agent_id}` : 'Unassigned'}</span>
                  </div>
                </div>
              </div>

              <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
                <span className="font-bold text-sm text-slate-800">{p.price_label || `KSh ${p.price || 0}`}</span>
                <button
                  onClick={() => handleOpenAssign(p)}
                  className="px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-xl text-xs font-semibold transition"
                >
                  Assign Staff &rarr;
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Staff Assignment Modal */}
      {selectedProp && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex justify-between items-center pb-4 border-b border-slate-100">
              <h3 className="font-bold text-lg text-slate-800">Assign Staff for {selectedProp.name}</h3>
              <button onClick={() => setSelectedProp(null)} className="text-slate-400 hover:text-slate-600 font-bold text-xl">
                &times;
              </button>
            </div>

            <form onSubmit={handleSaveAssign} className="py-4 space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Property Manager User ID</label>
                <input
                  type="number"
                  placeholder="Enter User ID of Manager (or leave blank to remove)"
                  value={managerId}
                  onChange={(e) => setManagerId(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Listing Agent User ID</label>
                <input
                  type="number"
                  placeholder="Enter User ID of Agent (or leave blank to remove)"
                  value={agentId}
                  onChange={(e) => setAgentId(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="pt-4 border-t border-slate-100 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setSelectedProp(null)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow transition"
                >
                  {saving ? 'Saving...' : 'Save Assignment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
export default OwnerProperties
