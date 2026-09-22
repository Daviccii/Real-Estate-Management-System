import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMyApplications } from '../../services/application'
import { RentalApplication } from '../../types'

export const TenantApplications: React.FC = () => {
  const [applications, setApplications] = useState<RentalApplication[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedApp, setSelectedApp] = useState<RentalApplication | null>(null)

  useEffect(() => {
    getMyApplications()
      .then(setApplications)
      .finally(() => setLoading(false))
  }, [])

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-emerald-100 text-emerald-800'
      case 'rejected':
        return 'bg-red-100 text-red-800'
      case 'under_review':
        return 'bg-blue-100 text-blue-800'
      case 'info_required':
        return 'bg-amber-100 text-amber-800'
      default:
        return 'bg-slate-100 text-slate-700'
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading your rental applications...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">My Rental Applications</h1>
          <p className="text-slate-500 text-sm mt-1">
            Track status, uploaded verification documents, and landlord review decisions in real time.
          </p>
        </div>
        <Link
          to="/rent"
          className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-sm font-medium transition shadow-sm"
        >
          + Find More Rentals
        </Link>
      </div>

      {applications.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-100 text-center max-w-lg mx-auto mt-8 shadow-sm">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
            📝
          </div>
          <h2 className="text-xl font-bold text-slate-800">No Rental Applications Yet</h2>
          <p className="text-slate-500 text-sm mt-2">
            When you apply for a property or unit on PropNoxa, your digital application workflow and screening updates will appear here.
          </p>
          <div className="mt-6">
            <Link to="/rent" className="px-4 py-2 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 transition">
              Browse Available Properties
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {applications.map((app) => (
            <div
              key={app.id}
              className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm flex flex-col justify-between hover:shadow-md transition"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className={`px-2.5 py-1 text-xs font-semibold rounded-full uppercase tracking-wider ${getStatusBadge(app.status)}`}>
                    {app.status.replace('_', ' ')}
                  </span>
                  <span className="text-xs text-slate-400">
                    {new Date(app.created_at).toLocaleDateString()}
                  </span>
                </div>
                <h3 className="font-bold text-lg text-slate-800">{app.property_name || `Property #${app.property_id}`}</h3>
                {app.unit_number && (
                  <p className="text-xs font-medium text-slate-500 mt-0.5">Unit {app.unit_number}</p>
                )}

                <div className="mt-4 space-y-2 text-xs text-slate-600 bg-slate-50 p-3 rounded-xl">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Employment:</span>
                    <span className="font-medium text-slate-700">{app.job_title || 'N/A'} ({app.employment_status || 'N/A'})</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Declared Income:</span>
                    <span className="font-medium text-slate-700">{app.monthly_income ? `KSh ${app.monthly_income}` : 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Move-in Target:</span>
                    <span className="font-medium text-slate-700">
                      {app.desired_move_in_date ? new Date(app.desired_move_in_date).toLocaleDateString() : 'Immediate'}
                    </span>
                  </div>
                </div>

                {app.review_notes && (
                  <div className="mt-3 p-3 bg-blue-50 border border-blue-100 rounded-xl text-xs text-blue-900">
                    <span className="font-semibold block mb-0.5">Reviewer Feedback:</span>
                    {app.review_notes}
                  </div>
                )}
              </div>

              <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
                <button
                  onClick={() => setSelectedApp(app)}
                  className="text-xs font-semibold text-teal-600 hover:text-teal-700"
                >
                  View Full Application &rarr;
                </button>
                {app.status === 'approved' && (
                  <Link
                    to="/tenant/my-tenancy"
                    className="px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700 transition"
                  >
                    View Tenancy
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Application Detail Modal */}
      {selectedApp && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="flex justify-between items-center pb-4 border-b border-slate-100">
              <h3 className="font-bold text-lg text-slate-800">Application Details #{selectedApp.id}</h3>
              <button
                onClick={() => setSelectedApp(null)}
                className="text-slate-400 hover:text-slate-600 font-bold text-xl"
              >
                &times;
              </button>
            </div>

            <div className="py-4 space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-3 bg-slate-50 p-4 rounded-xl">
                <div>
                  <span className="text-xs text-slate-400 block">Property</span>
                  <span className="font-semibold text-slate-800">{selectedApp.property_name || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block">Status</span>
                  <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold uppercase ${getStatusBadge(selectedApp.status)}`}>
                    {selectedApp.status}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block">Employer</span>
                  <span className="font-medium text-slate-700">{selectedApp.employer_name || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block">Monthly Income</span>
                  <span className="font-medium text-slate-700">{selectedApp.monthly_income || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block">Occupants</span>
                  <span className="font-medium text-slate-700">{selectedApp.occupants_count || 1}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block">Pets</span>
                  <span className="font-medium text-slate-700">{selectedApp.has_pets || 'None'}</span>
                </div>
              </div>

              {selectedApp.emergency_contact_name && (
                <div className="p-3 bg-slate-50 rounded-xl text-xs">
                  <span className="font-semibold text-slate-700 block mb-1">Emergency Contact:</span>
                  <div>{selectedApp.emergency_contact_name} ({selectedApp.emergency_contact_phone || 'No phone'})</div>
                </div>
              )}

              {selectedApp.review_notes && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900">
                  <span className="font-semibold block mb-1">Management Review Note:</span>
                  <div>{selectedApp.review_notes}</div>
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => setSelectedApp(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
export default TenantApplications
