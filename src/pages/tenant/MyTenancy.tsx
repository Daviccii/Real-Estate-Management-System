import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMyTenancy } from '../../services/tenant'
import { Lease } from '../../types'

export const MyTenancy: React.FC = () => {
  const [lease, setLease] = useState<Lease | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMyTenancy()
      .then(setLease)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading your tenancy details...</div>
  }

  if (!lease) {
    return (
      <div className="bg-white rounded-2xl p-8 border border-slate-100 text-center max-w-lg mx-auto mt-8 shadow-sm">
        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
          🏠
        </div>
        <h2 className="text-xl font-bold text-slate-800">No Active Tenancy Found</h2>
        <p className="text-slate-500 text-sm mt-2">
          You are not currently linked to an active lease. Once your rental application is approved and executed, your lease and tenancy details will appear here.
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <Link to="/rent" className="px-4 py-2 bg-teal-600 text-white rounded-xl text-sm font-medium hover:bg-teal-700 transition">
            Explore Rentals
          </Link>
          <Link to="/tenant/applications" className="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl text-sm font-medium hover:bg-slate-200 transition">
            My Applications
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">My Tenancy & Lease Agreement</h1>
          <p className="text-slate-500 text-sm mt-1">Official lease term records, rent schedule, and unit details.</p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/tenant/payments" className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700 transition">
            Make Rent Payment
          </Link>
          <Link to="/tenant/maintenance" className="px-4 py-2 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 transition">
            Request Repair
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main Details Card */}
        <div className="md:col-span-2 bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-100 text-emerald-800 rounded-full uppercase tracking-wider">
                {lease.status}
              </span>
              <h2 className="text-xl font-bold text-slate-800 mt-2">{lease.property_name || 'Property Residence'}</h2>
              <p className="text-slate-500 text-sm">Unit: {lease.unit_number || 'N/A'}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div className="p-4 bg-slate-50 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Monthly Rent</span>
              <div className="text-lg font-bold text-emerald-700 mt-1">KSh {lease.rent_amount}</div>
              <span className="text-xs text-slate-400">Due by {lease.payment_due_date || '5'}th of every month</span>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Security Deposit</span>
              <div className="text-lg font-bold text-slate-800 mt-1">KSh {lease.deposit || '0'}</div>
              <span className="text-xs text-slate-400">Held in escrow account</span>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Lease Start Date</span>
              <div className="text-base font-semibold text-slate-800 mt-1">{lease.start_date}</div>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl">
              <span className="text-xs text-slate-400 font-medium">Lease End Date</span>
              <div className="text-base font-semibold text-slate-800 mt-1">{lease.end_date}</div>
            </div>
          </div>

          {lease.notes && (
            <div className="p-4 bg-amber-50/50 border border-amber-100 rounded-xl text-sm">
              <span className="font-semibold text-amber-900 block mb-1">Lease Terms & Special Conditions:</span>
              <p className="text-amber-800/90">{lease.notes}</p>
            </div>
          )}
        </div>

        {/* Quick Contacts & Actions */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
            <h3 className="font-semibold text-slate-800 mb-4">Property Management Contact</h3>
            <div className="space-y-3 text-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center font-bold">
                  PM
                </div>
                <div>
                  <div className="font-medium text-slate-800">Property Manager Desk</div>
                  <div className="text-xs text-slate-500">Available Mon-Fri 8AM - 5PM</div>
                </div>
              </div>
              <div className="pt-2">
                <Link to="/tenant/messages" className="block text-center w-full py-2 bg-teal-50 hover:bg-teal-100 text-teal-700 rounded-xl text-xs font-semibold transition">
                  Send Direct Message
                </Link>
              </div>
            </div>
          </div>

          <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-md">
            <h3 className="font-semibold text-base mb-2">Notice of Renewal / Move-out</h3>
            <p className="text-xs text-slate-300 mb-4">
              Need to request early termination, lease extension, or schedule a pre-move-out inspection?
            </p>
            <Link to="/tenant/messages" className="inline-block px-3.5 py-1.5 bg-white/10 hover:bg-white/20 text-white text-xs font-medium rounded-lg backdrop-blur transition">
              Submit Lease Inquiry
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
export default MyTenancy
