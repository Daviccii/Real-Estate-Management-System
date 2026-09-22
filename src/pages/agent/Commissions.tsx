import React, { useEffect, useState } from 'react'
import { getAgentCommissions } from '../../services/agent'
import { Lead } from '../../types'

export const AgentCommissions: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([])
  const [totalCommission, setTotalCommission] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAgentCommissions()
      .then((res) => {
        setLeads(res.leads || [])
        setTotalCommission(res.total_commission || 0)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading commission ledger...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Agent Commission & Earnings Ledger</h1>
          <p className="text-slate-500 text-sm mt-1">
            Track closed deal commissions, agent fees, and payment disbursement status.
          </p>
        </div>
        <button
          onClick={() => window.print()}
          className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-sm font-medium transition shadow-sm"
        >
          🖨️ Print Earnings Statement
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Commissions Realized</div>
          <div className="text-3xl font-black text-emerald-600 mt-2">
            KSh {totalCommission.toLocaleString()}
          </div>
          <div className="text-xs text-slate-500 mt-1">From closed tenant placement deals</div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Closed Deals Count</div>
          <div className="text-3xl font-black text-blue-700 mt-2">{leads.length}</div>
          <div className="text-xs text-slate-500 mt-1">Successfully signed lease conversions</div>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-bold text-slate-800">Deal Commission Breakdown</h2>
          <span className="text-xs text-slate-400 font-medium">{leads.length} closed deal(s)</span>
        </div>

        {leads.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-sm">
            No closed deals with recorded commissions yet. Move leads in your CRM to "Closed Deal" to generate commissions.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50/80 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                  <th className="py-3 px-5">Lead / Client</th>
                  <th className="py-3 px-5">Property</th>
                  <th className="py-3 px-5">Date Closed</th>
                  <th className="py-3 px-5">Commission Earned</th>
                  <th className="py-3 px-5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {leads.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-50/50 transition">
                    <td className="py-3.5 px-5 font-bold text-slate-800">
                      {l.prospect_name || `Lead #${l.id}`}
                    </td>
                    <td className="py-3.5 px-5 text-slate-600">
                      {l.property_name || 'Listing'}
                    </td>
                    <td className="py-3.5 px-5 text-xs text-slate-500">
                      {new Date(l.updated_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-5 font-bold text-emerald-700">
                      KSh {parseFloat(l.commission_amount || '25000').toLocaleString()}
                    </td>
                    <td className="py-3.5 px-5">
                      <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 uppercase">
                        Approved
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
export default AgentCommissions
