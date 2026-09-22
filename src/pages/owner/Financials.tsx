import React, { useEffect, useState } from 'react'
import { getOwnerFinancialLedger } from '../../services/owner'
import { Payment } from '../../types'

export const OwnerFinancials: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([])
  const [totalCollected, setTotalCollected] = useState(0)
  const [totalPending, setTotalPending] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getOwnerFinancialLedger()
      .then((res) => {
        setPayments(res.payments || [])
        setTotalCollected(res.total_collected || 0)
        setTotalPending(res.total_pending || 0)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading your financial ledger...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Financial Ledger & Revenue Yield</h1>
          <p className="text-slate-500 text-sm mt-1">
            Real-time rent collection tracking, tenant payments, and cash flow reconciliation.
          </p>
        </div>
        <button
          onClick={() => window.print()}
          className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-sm font-medium transition shadow-sm"
        >
          🖨️ Export / Print Financial Statement
        </button>
      </div>

      {/* Financial KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Revenue Realized</div>
          <div className="text-2xl font-bold text-emerald-600 mt-2">
            KSh {totalCollected.toLocaleString()}
          </div>
          <div className="text-xs text-slate-500 mt-1">Paid rent transactions</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Outstanding / Pending Rent</div>
          <div className="text-2xl font-bold text-amber-600 mt-2">
            KSh {totalPending.toLocaleString()}
          </div>
          <div className="text-xs text-slate-500 mt-1">Awaiting tenant remittance</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Recorded Invoices</div>
          <div className="text-2xl font-bold text-slate-800 mt-2">{payments.length}</div>
          <div className="text-xs text-slate-500 mt-1">Audited billing cycles</div>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-bold text-slate-800">Rent Payments & Collections</h2>
          <span className="text-xs text-slate-400 font-medium">{payments.length} transaction(s)</span>
        </div>

        {payments.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-sm">
            No financial transactions recorded for your properties yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50/80 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                  <th className="py-3 px-5">Ref / ID</th>
                  <th className="py-3 px-5">Property</th>
                  <th className="py-3 px-5">Tenant</th>
                  <th className="py-3 px-5">Due Date</th>
                  <th className="py-3 px-5">Amount</th>
                  <th className="py-3 px-5">Method</th>
                  <th className="py-3 px-5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {payments.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/50 transition">
                    <td className="py-3.5 px-5 font-mono text-xs font-semibold text-slate-800">
                      {p.reference || `REC-${p.id.toString().padStart(6, '0')}`}
                    </td>
                    <td className="py-3.5 px-5 font-medium text-slate-800">
                      {p.property_name || 'Holding'}
                    </td>
                    <td className="py-3.5 px-5 text-xs text-slate-600">
                      {p.tenant_name || `Tenant #${p.tenant_id}`}
                    </td>
                    <td className="py-3.5 px-5 text-xs text-slate-500">
                      {p.due_date ? new Date(p.due_date).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="py-3.5 px-5 font-bold text-slate-800">
                      KSh {parseFloat(p.amount || '0').toLocaleString()}
                    </td>
                    <td className="py-3.5 px-5 text-xs text-slate-500">
                      {p.payment_method || 'Electronic'}
                    </td>
                    <td className="py-3.5 px-5">
                      <span className={`px-2.5 py-1 text-xs font-semibold rounded-full uppercase ${
                        p.status === 'paid' || p.status === 'completed'
                          ? 'bg-emerald-100 text-emerald-800'
                          : p.status === 'pending'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {p.status}
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
export default OwnerFinancials
