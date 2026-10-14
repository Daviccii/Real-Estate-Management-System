import React, { useCallback, useEffect, useState } from 'react'
import { getMyPayments } from '../../services/tenant'
import {
  MpesaConfig,
  MpesaTransaction,
  isLiveMpesaTransaction,
  mpesaService,
} from '../../services/mpesa'
import { MpesaPaymentModal } from '../../components/MpesaPaymentModal'
import { MpesaStatusBadge } from '../../components/MpesaStatusBadge'
import { Payment } from '../../types'

const PAYABLE_STATUSES = ['pending', 'partially_paid', 'overdue']

// Mirrors the backend MPESA_DUPLICATE_WINDOW_SECONDS: only an attempt started
// within this window blocks a new prompt. An older live row is history — the
// server would accept a fresh request, so the UI must not strand the tenant
// on "Check payment" forever.
const DUPLICATE_WINDOW_MS = 5 * 60 * 1000

const statusBadgeClass = (status: string): string => {
  if (['paid', 'completed', 'succeeded'].includes(status)) return 'bg-emerald-100 text-emerald-800'
  if (['pending', 'partially_paid'].includes(status)) return 'bg-amber-100 text-amber-800'
  if (['overdue', 'failed', 'cancelled', 'timed_out', 'expired'].includes(status)) return 'bg-red-100 text-red-800'
  return 'bg-slate-100 text-slate-600'
}

const formatKsh = (value: string | number): string => {
  const n = typeof value === 'number' ? value : parseFloat(value || '0')
  return Number.isFinite(n) ? n.toLocaleString() : String(value)
}

export const TenantPayments: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([])
  const [transactions, setTransactions] = useState<MpesaTransaction[]>([])
  const [mpesaConfig, setMpesaConfig] = useState<MpesaConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedReceipt, setSelectedReceipt] = useState<Payment | null>(null)
  const [payTarget, setPayTarget] = useState<{ payment: Payment; txn?: MpesaTransaction } | null>(null)

  const load = useCallback(async () => {
    try {
      const rows = await getMyPayments()
      setPayments(rows)
    } finally {
      setLoading(false)
    }
    try {
      const config = await mpesaService.getConfig()
      setMpesaConfig(config)
      if (config.configured) {
        setTransactions(await mpesaService.listTransactions({ limit: 20 }))
      }
    } catch {
      // M-Pesa UI is optional: hide the controls when config cannot be read.
      setMpesaConfig(null)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const handlePrint = () => {
    window.print()
  }

  const liveTxnForPayment = (paymentId: number) =>
    transactions.find((t) => {
      if (t.payment_id !== paymentId || !isLiveMpesaTransaction(t)) return false
      if (!t.initiated_at) return true
      return Date.now() - new Date(t.initiated_at).getTime() < DUPLICATE_WINDOW_MS
    })

  const appliedTxnForPayment = (paymentId: number) =>
    transactions.find((t) => t.payment_id === paymentId && t.status === 'succeeded' && t.applied_to_payment)

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading your payment records...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="tenant-eyebrow">Resident finance</span>
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
                {payments.map((p) => {
                  const liveTxn = liveTxnForPayment(p.id)
                  const outstanding = p.outstanding_amount
                  const balance = outstanding !== undefined ? parseFloat(outstanding) : null
                  const obligation = parseFloat(p.amount || '0')
                  const showBalance =
                    balance !== null && Number.isFinite(obligation) && balance > 0 && balance < obligation
                  const payable = mpesaConfig?.configured && PAYABLE_STATUSES.includes(p.status)
                  return (
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
                        KSh {formatKsh(p.amount || '0')}
                        {showBalance && (
                          <div className="text-xs text-amber-700 font-medium">
                            Balance: KSh {formatKsh(balance)}
                          </div>
                        )}
                      </td>
                      <td className="py-3.5 px-5 text-xs text-slate-500">
                        {p.payment_method || 'M-Pesa / Bank'}
                      </td>
                      <td className="py-3.5 px-5">
                        <span className={`px-2.5 py-1 text-xs font-semibold rounded-full uppercase tracking-wider ${statusBadgeClass(p.status)}`}>
                          {p.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3.5 px-5 text-right">
                        <div className="inline-flex items-center gap-2">
                          {payable && (
                            <button
                              onClick={() => setPayTarget({ payment: p, txn: liveTxn })}
                              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                                liveTxn
                                  ? 'bg-amber-500 hover:bg-amber-600 text-white'
                                  : 'bg-emerald-500 hover:bg-emerald-600 text-white'
                              }`}
                            >
                              {liveTxn ? '⏳ Check payment' : '📱 Pay with M-Pesa'}
                            </button>
                          )}
                          <button
                            onClick={() => setSelectedReceipt(p)}
                            className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium transition"
                          >
                            Receipt View
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {transactions.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <h2 className="font-bold text-slate-800">M-Pesa Payment Attempts</h2>
            <span className="text-xs text-slate-400 font-medium">Confirmed only after Safaricom's callback</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50/80 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                  <th className="py-3 px-5">Reference</th>
                  <th className="py-3 px-5">Amount</th>
                  <th className="py-3 px-5">Phone</th>
                  <th className="py-3 px-5">Status</th>
                  <th className="py-3 px-5">M-Pesa Receipt</th>
                  <th className="py-3 px-5">Started</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {transactions.slice(0, 8).map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50/50 transition">
                    <td className="py-3 px-5 font-mono text-xs font-semibold text-slate-800">{t.reference}</td>
                    <td className="py-3 px-5 font-semibold text-slate-800">KSh {formatKsh(t.amount)}</td>
                    <td className="py-3 px-5 text-xs text-slate-500 font-mono">{t.phone_number}</td>
                    <td className="py-3 px-5">
                      <MpesaStatusBadge status={t.status} />
                    </td>
                    <td className="py-3 px-5 font-mono text-xs text-slate-600">{t.mpesa_receipt_number || '—'}</td>
                    <td className="py-3 px-5 text-xs text-slate-500">
                      {t.initiated_at ? new Date(t.initiated_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pay with M-Pesa */}
      {payTarget && (
        <MpesaPaymentModal
          payment={payTarget.payment}
          initialTransaction={payTarget.txn || null}
          onClose={() => setPayTarget(null)}
          onSettled={() => {
            void load()
          }}
        />
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
                  <span className="text-xl font-bold text-emerald-700">KSh {formatKsh(selectedReceipt.amount || '0')}</span>
                </div>
                <div className="text-xs text-slate-400 mt-1">Payment Method: {selectedReceipt.payment_method || 'Electronic Transfer / M-Pesa'}</div>
                {appliedTxnForPayment(selectedReceipt.id)?.mpesa_receipt_number && (
                  <div className="text-xs text-slate-400 mt-1">
                    M-Pesa Receipt:{' '}
                    <span className="font-mono font-semibold text-slate-700">
                      {appliedTxnForPayment(selectedReceipt.id)?.mpesa_receipt_number}
                    </span>
                  </div>
                )}
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
