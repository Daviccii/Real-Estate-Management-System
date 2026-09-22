import React, { useEffect, useState } from 'react'
import { getAgentListings } from '../../services/agent'
import { getPropertyApplications } from '../../services/application'
import { Property, RentalApplication } from '../../types'

export const AgentApplications: React.FC = () => {
  const [listings, setListings] = useState<Property[]>([])
  const [selectedPropertyId, setSelectedPropertyId] = useState<number | null>(null)
  const [applications, setApplications] = useState<RentalApplication[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAgentListings()
      .then((props) => {
        setListings(props)
        if (props.length > 0) {
          setSelectedPropertyId(props[0].id)
        }
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (selectedPropertyId) {
      getPropertyApplications(selectedPropertyId).then(setApplications)
    }
  }, [selectedPropertyId])

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading candidate applications...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Rental Application Review Queue</h1>
          <p className="text-slate-500 text-sm mt-1">
            Review incoming tenant dossiers for your syndicated marketing listings.
          </p>
        </div>
        {listings.length > 0 && (
          <div>
            <select
              value={selectedPropertyId || ''}
              onChange={(e) => setSelectedPropertyId(Number(e.target.value))}
              className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {listings.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {applications.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-100 text-center max-w-lg mx-auto mt-8 shadow-sm">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
            📝
          </div>
          <h2 className="text-xl font-bold text-slate-800">No Applications on this Listing</h2>
          <p className="text-slate-500 text-sm mt-2">
            Prospective tenants submitting rental applications for this listing will appear here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {applications.map((app) => (
            <div key={app.id} className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="px-2.5 py-1 text-xs font-semibold rounded-full uppercase bg-blue-100 text-blue-800">
                    {app.status}
                  </span>
                  <span className="text-xs text-slate-400">
                    {new Date(app.created_at).toLocaleDateString()}
                  </span>
                </div>

                <h3 className="font-bold text-lg text-slate-800">{app.applicant_name || `Applicant #${app.applicant_id}`}</h3>
                <div className="text-xs text-slate-500 mt-0.5">{app.applicant_email || 'Verified account'}</div>

                <div className="mt-4 p-3 bg-slate-50 rounded-xl text-xs space-y-1 text-slate-600">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Employer:</span>
                    <span className="font-medium text-slate-700">{app.employer_name || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Income:</span>
                    <span className="font-semibold text-emerald-700">{app.monthly_income ? `KSh ${app.monthly_income}` : 'N/A'}</span>
                  </div>
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-100 text-xs text-slate-400 flex justify-between items-center">
                <span>Application #{app.id}</span>
                <span className="text-blue-600 font-semibold">Under Screening</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
export default AgentApplications
