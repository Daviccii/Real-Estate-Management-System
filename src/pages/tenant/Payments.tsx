import React, { useEffect, useState } from 'react'
import { getMyPayments } from '../../services/tenant'
import { Payment } from '../../types'

export const TenantPayments: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedReceipt, setSelectedReceipt] = useState<Payment | null>(null)

  useEffect(() => {
    getMyPayments()
      .then(setPayments)
      .finally(() => setLoading(false))
  }, [])

  const handlePrint = () => {
    window.print()
  }

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading your payment records...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Rent & Utility Payments</h1>
          <p className="text-slate-500 text-sm mt-1">
            Official transaction ledger, digital invoices, and verified payment receipts.
          </p>
        </div>
      </div>

      {payments.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-100 text-center max-w-lg mx-auto mt-8 shadow-sm">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
            💳
          </div>
          <h2 className="text-xl font-bold text-slate-800">No Payment History Found</h2>
          <p className="text-slate-500 text-sm mt-2">
            Invoices and automated receipts will show up here once you have an active tenancy and scheduled rent cycles.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <h2 className="font-bold text-slate-800">Transaction History</h2>
            <span className="text-xs text-slate-400 font-medium">{payments.length} record(s)</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50/80 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                  <th className="py-3 px-5">Receipt Ref</th>
                  <th className="py-3 px-5">Property / Unit</th>
                  <th className="py-3 px-5">Due Date</th>
                  <th className="py-3 px-5">Amount</th>
                  <th className="py-3 px-5">Method</th>
                  <th className="py-3 px-5">Status</th>
                  <th className="py-3 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {payments.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/50 transition">
                    <td className="py-3.5 px-5 font-mono text-xs font-semibold text-slate-800">
                      {p.reference || `REC-${p.id.toString().padStart(6, '0')}`}
                    </td>
                    <td className="py-3.5 px-5">
                      <div className="font-medium text-slate-800">{p.property_name || 'Home Residence'}</div>
                      <div className="text-xs text-slate-400">Unit: {p.unit_number || 'N/A'}</div>
                    </td>
                    <td className="py-3.5 px-5 text-slate-500 text-xs">
                      {p.due_date ? new Date(p.due_date).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="py-3.5 px-5 font-semibold text-slate-800">
                      KSh {parseFloat(p.amount || '0').toLocaleString()}
                    </td>
                    <td className="py-3.5 px-5 text-xs text-slate-500">
                      {p.payment_method || 'M-Pesa / Bank'}
                    </td>
                    <td className="py-3.5 px-5">
                      <span className={`px-2.5 py-1 text-xs font-semibold rounded-full uppercase tracking-wider ${
                        p.status === 'paid' || p.status === 'completed'
                          ? 'bg-emerald-100 text-emerald-800'
                          : p.status === 'pending'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {p.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-5 text-right">
                      <button
                        onClick={() => setSelectedReceipt(p)}
                        className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium transition"
                      >
                        Receipt View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Printable Digital Receipt Modal */}
      {selectedReceipt && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-8 shadow-2xl printable-receipt">
            <div className="flex justify-between items-start pb-6 border-b border-slate-100">
              <div>
                <div className="text-xl font-black text-teal-700 tracking-tight">PropNoxa Ecosystem</div>
                <div className="text-xs text-slate-400 mt-0.5">Official Rent Payment Receipt</div>
              </div>
              <button
                onClick={() => setSelectedReceipt(null)}
                className="text-slate-400 hover:text-slate-600 font-bold text-xl no-print"
              >
                &times;
              </button>
            </div>

            <div className="py-6 space-y-4 text-sm">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Receipt Ref:</span>
                <span className="font-mono font-bold text-slate-800">{selectedReceipt.reference || `REC-${selectedReceipt.id.toString().padStart(6, '0')}`}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Date Issued:</span>
                <span className="text-slate-700">{selectedReceipt.payment_date || new Date().toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Property:</span>
                <span className="font-medium text-slate-800">{selectedReceipt.property_name || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Unit:</span>
                <span className="font-medium text-slate-800">{selectedReceipt.unit_number || 'N/A'}</span>
              </div>

              <div className="bg-slate-50 p-4 rounded-xl my-4">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-slate-600">Total Amount Paid</span>
                  <span className="text-xl font-bold text-emerald-700">KSh {parseFloat(selectedReceipt.amount || '0').toLocaleString()}</span>
                </div>
                <div className="text-xs text-slate-400 mt-1">Payment Method: {selectedReceipt.payment_method || 'Electronic Transfer / M-Pesa'}</div>
              </div>

              <div className="text-center text-xs text-slate-400 pt-4 border-t border-slate-100">
                Verified digital transaction registered on PropNoxa platform. Thank you for your payment.
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex justify-end gap-3 no-print">
              <button
                onClick={handlePrint}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold transition"
              >
                🖨️ Print / Save PDF
              </button>
              <button
                onClick={() => setSelectedReceipt(null)}
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
export default TenantPayments
