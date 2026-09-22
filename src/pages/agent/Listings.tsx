import React, { useEffect, useState } from 'react'
import { getAgentListings } from '../../services/agent'
import { Property } from '../../types'

export const AgentListings: React.FC = () => {
  const [listings, setListings] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAgentListings()
      .then(setListings)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading your assigned listings...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Agent Marketing Listings</h1>
          <p className="text-slate-500 text-sm mt-1">Properties assigned to you for client tours, inquiries, and lease negotiation.</p>
        </div>
      </div>

      {listings.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-100 text-center max-w-lg mx-auto mt-8 shadow-sm">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
            🏷️
          </div>
          <h2 className="text-xl font-bold text-slate-800">No Assigned Listings</h2>
          <p className="text-slate-500 text-sm mt-2">
            Property owners and administrators can assign listings directly to your agent account.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {listings.map((p) => (
            <div key={p.id} className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-50 text-blue-800 uppercase tracking-wider">
                    {p.status}
                  </span>
                  {p.is_verified && (
                    <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-xs font-bold rounded-full">
                      ✓ Verified
                    </span>
                  )}
                </div>

                <h3 className="font-bold text-lg text-slate-800">{p.name}</h3>
                <p className="text-xs text-slate-400 mt-0.5">{p.city || 'Nairobi'} • {p.property_type || 'Residential'}</p>

                <div className="mt-4 p-3 bg-slate-50 rounded-xl space-y-1 text-xs text-slate-600">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Bedrooms / Bath:</span>
                    <span className="font-medium text-slate-700">{p.bedrooms || 0} Bed / {p.bathrooms || 0} Bath</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Parking:</span>
                    <span className="font-medium text-slate-700">{p.parking_spaces || 0} Space(s)</span>
                  </div>
                </div>
              </div>

              <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
                <span className="font-bold text-sm text-slate-800">{p.price_label || `KSh ${p.price || 0}`}</span>
                <span className="text-xs text-blue-600 font-semibold">Active Syndication</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
export default AgentListings
