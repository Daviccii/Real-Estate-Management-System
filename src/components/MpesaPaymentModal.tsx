import React, { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError } from '../services/api'
import {
  MpesaTransaction,
  isLiveMpesaTransaction,
  mpesaStatusLabel,
  mpesaService,
} from '../services/mpesa'
import type { Payment } from '../types'

// Bounded status refresh: the UI polls the authoritative server record — never
// the STK acceptance response — and always stops (terminal state, attempt cap,
// or unmount) so a forgotten tab cannot poll forever.
const POLL_INTERVAL_MS = 3000
const MAX_POLLS = 40 // ~2 minutes
const MAX_POLL_ERRORS = 5

type Phase = 'form' | 'waiting' | 'success' | 'failed' | 'unknown'

interface MpesaPaymentModalProps {
  payment: Payment
  initialTransaction?: MpesaTransaction | null
  onClose: () => void
  onSettled: () => void
}

const formatKsh = (value: string | number): string => {
  const n = typeof value === 'number' ? value : parseFloat(value || '0')
  return Number.isFinite(n) ? n.toLocaleString() : String(value)
}

const isValidKenyanPhone = (value: string): boolean => {
  const compact = value.replace(/[\s()-]/g, '')
  return /^(?:\+?254|0)[17]\d{8}$/.test(compact)
}

export const MpesaPaymentModal: React.FC<MpesaPaymentModalProps> = ({
  payment,
  initialTransaction = null,
  onClose,
  onSettled,
}) => {
  const outstanding = payment.outstanding_amount || payment.amount || '0'

  const [phase, setPhase] = useState<Phase>(initialTransaction ? 'waiting' : 'form')
  const [phone, setPhone] = useState('')
  const [amount, setAmount] = useState(outstanding)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [txn, setTxn] = useState<MpesaTransaction | null>(initialTransaction)
  const [notice, setNotice] = useState<string | null>(null)

  const pollTimer = useRef<number | null>(null)
  const pollAttempts = useRef(0)
  const pollErrors = useRef(0)
  const pollInFlight = useRef(false)

  const stopPolling = useCallback(() => {
    if (pollTimer.current !== null) {
      window.clearInterval(pollTimer.current)
      pollTimer.current = null
    }
  }, [])

  useEffect(() => stopPolling, [stopPolling])

  const applyTransactionResult = useCallback(
    (latest: MpesaTransaction) => {
      setTxn(latest)
      if (latest.status === 'succeeded') {
        stopPolling()
        setPhase('success')
        onSettled()
        return true
      }
      if (['failed', 'cancelled', 'timed_out', 'expired'].includes(latest.status)) {
        stopPolling()
        setPhase('failed')
        onSettled()
        return true
      }
      return false
    },
    [onSettled, stopPolling],
  )

  const pollOnce = useCallback(
    async (transactionId: number) => {
      if (pollInFlight.current) return
      pollInFlight.current = true
      try {
        const latest = await mpesaService.getTransaction(transactionId)
        pollErrors.current = 0
        applyTransactionResult(latest)
      } catch {
        pollErrors.current += 1
        if (pollErrors.current >= MAX_POLL_ERRORS) {
          stopPolling()
          setPhase('unknown')
          setNotice('We lost contact while checking the payment status. Use "Check status" to verify before retrying.')
        }
      } finally {
        pollInFlight.current = false
      }
    },
    [applyTransactionResult, stopPolling],
  )

  const startPolling = useCallback(
    (transactionId: number) => {
      stopPolling()
      pollAttempts.current = 0
      pollErrors.current = 0
      pollTimer.current = window.setInterval(() => {
        pollAttempts.current += 1
        if (pollAttempts.current > MAX_POLLS) {
          stopPolling()
          setPhase('unknown')
          setNotice('Safaricom has not confirmed this payment yet. Do not resend — use "Check status" to verify it.')
          return
        }
        void pollOnce(transactionId)
      }, POLL_INTERVAL_MS)
    },
    [pollOnce, stopPolling],
  )

  useEffect(() => {
    if (initialTransaction && isLiveMpesaTransaction(initialTransaction)) {
      startPolling(initialTransaction.id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!isValidKenyanPhone(phone)) {
      setError('Enter a valid Safaricom number, e.g. 0712 345 678 or 2547 1234 5678.')
      return
    }
    const parsedAmount = Number(amount)
    if (!Number.isFinite(parsedAmount) || !Number.isInteger(parsedAmount) || parsedAmount < 1) {
      setError('Enter a whole-shilling amount of at least KSh 1 (no cents).')
      return
    }
    if (parsedAmount > Number(payment.outstanding_amount || payment.amount || '0')) {
      setError('The amount cannot be more than the outstanding balance.')
      return
    }

    setSubmitting(true)
    try {
      const created = await mpesaService.initiate({
        payment_id: payment.id,
        phone_number: phone.trim(),
        amount: String(parsedAmount),
      })
      setTxn(created)
      setPhase('waiting')
      onSettled()
      startPolling(created.id)
    } catch (err) {
      if (err instanceof ApiError) {
        const detail = err.data?.detail
        // 409 duplicate: a prompt for this obligation is already live — adopt
        // it and watch instead of sending a second PIN prompt.
        const existing = detail?.transaction as MpesaTransaction | undefined
        if (err.status === 409 && existing) {
          setTxn(existing)
          setNotice('An M-Pesa request for this rent bill is already in progress.')
          setPhase('waiting')
          onSettled()
          startPolling(existing.id)
        } else if (err.status === 502 && detail?.transaction) {
          // The 502 carries the stored attempt: when it is already terminal
          // (e.g. OAuth rejected before submission) reflect that honestly;
          // only a genuinely live attempt shows the unconfirmed state.
          const attempted = detail.transaction as MpesaTransaction
          if (!applyTransactionResult(attempted)) {
            setPhase('unknown')
            setNotice(detail?.message || 'We could not confirm whether the M-Pesa prompt was delivered.')
          }
        } else {
          setError(typeof detail === 'string' ? detail : detail?.message || err.message)
        }
      } else {
        setError('The payment could not be started. Please try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleCheckStatus = async () => {
    if (!txn || submitting) return
    setSubmitting(true)
    setError(null)
    try {
      const latest = await mpesaService.reconcile(txn.id)
      const reachedTerminal = applyTransactionResult(latest)
      if (!reachedTerminal) {
        setPhase('waiting')
        setNotice('Safaricom is still processing this payment. Keep this window open — we will keep checking.')
        startPolling(latest.id)
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not check the payment status.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleClose = () => {
    stopPolling()
    onClose()
  }

  const waitingForPin = phase === 'waiting' && txn && (txn.status === 'pending' || txn.status === 'awaiting_callback')

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-start justify-between">
          <div>
            <div className="text-lg font-black text-teal-700 tracking-tight">Pay with M-Pesa</div>
            <div className="text-xs text-slate-400 mt-0.5">
              {payment.property_name || 'Rent bill'} · {payment.reference || `PAY-${payment.id}`}
            </div>
          </div>
          <button onClick={handleClose} className="text-slate-400 hover:text-slate-600 font-bold text-xl" aria-label="Close">
            &times;
          </button>
        </div>

        <div className="p-5 space-y-4">
          <div className="bg-slate-50 rounded-xl p-4">
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">Rent bill</span>
              <span className="font-semibold text-slate-800">KSh {formatKsh(payment.amount || '0')}</span>
            </div>
            <div className="flex justify-between text-sm mt-1">
              <span className="text-slate-500">Outstanding balance</span>
              <span className="font-bold text-slate-800">KSh {formatKsh(outstanding)}</span>
            </div>
          </div>

          {phase === 'form' && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1" htmlFor="mpesa-phone">
                  M-Pesa phone number
                </label>
                <input
                  id="mpesa-phone"
                  className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm"
                  placeholder="0712 345 678"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  inputMode="tel"
                  autoComplete="tel"
                />
                <p className="text-xs text-slate-400 mt-1">
                  Safaricom will show a PIN prompt on this phone. The PIN is entered only on your handset — never here.
                </p>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1" htmlFor="mpesa-amount">
                  Amount (KSh)
                </label>
                <input
                  id="mpesa-amount"
                  className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  inputMode="numeric"
                />
                <p className="text-xs text-slate-400 mt-1">Partial payments are allowed up to your outstanding balance.</p>
              </div>
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl p-3">{error}</div>
              )}
              <button
                type="submit"
                disabled={submitting}
                className="w-full px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-sm font-semibold transition disabled:opacity-50"
              >
                {submitting ? 'Sending request…' : `Send M-Pesa request · KSh ${formatKsh(amount || '0')}`}
              </button>
            </form>
          )}

          {phase === 'waiting' && (
            <div className="space-y-3 text-center py-2">
              <div className="w-12 h-12 border-4 border-emerald-100 rounded-full mx-auto mpesa-spinner" />
              <div className="font-semibold text-slate-800">
                {waitingForPin ? 'Check your phone now' : 'Confirming with Safaricom…'}
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                {waitingForPin
                  ? `Enter your M-Pesa PIN on the prompt shown on ${txn?.phone_number || 'your phone'} to pay KSh ${formatKsh(txn?.amount || amount)}.`
                  : 'We are waiting for the confirmed result — this is not a payment yet.'}
              </p>
              {notice && <p className="text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded-xl p-2">{notice}</p>}
              <p className="text-xs text-slate-400">
                Keep this window open. You can close it safely — your ledger only updates after Safaricom confirms.
              </p>
              <button
                onClick={handleClose}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold"
              >
                Close and check later
              </button>
            </div>
          )}

          {phase === 'success' && txn && (
            <div className="space-y-3 text-center py-2">
              <div className="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto text-xl font-bold">✓</div>
              <div className="font-semibold text-slate-800">Payment confirmed</div>
              <div className="text-sm text-slate-600">KSh {formatKsh(txn.amount)} received for {payment.property_name || 'your rent'}</div>
              <div className="text-xs text-slate-500">
                {txn.mpesa_receipt_number
                  ? <>M-Pesa receipt: <span className="font-mono font-semibold text-slate-700">{txn.mpesa_receipt_number}</span></>
                  : 'Safaricom confirmed this payment. The receipt number will be added to your ledger shortly.'}
              </div>
              <button
                onClick={handleClose}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold"
              >
                Done
              </button>
            </div>
          )}

          {phase === 'failed' && txn && (
            <div className="space-y-3 text-center py-2">
              <div className="w-12 h-12 bg-red-100 text-red-700 rounded-full flex items-center justify-center mx-auto text-xl font-bold">✕</div>
              <div className="font-semibold text-slate-800">
                {txn.status === 'cancelled'
                  ? 'You cancelled the M-Pesa prompt'
                  : txn.status === 'timed_out'
                  ? 'The M-Pesa prompt timed out'
                  : txn.status === 'expired'
                  ? 'The M-Pesa request expired'
                  : 'The payment was not completed'}
              </div>
              <p className="text-xs text-slate-500">
                {txn.failure_reason || txn.result_description || 'No money was taken. You can try again.'}
              </p>
              <div className="flex justify-center gap-3">
                <button
                  onClick={() => {
                    setTxn(null)
                    setNotice(null)
                    setError(null)
                    setPhase('form')
                    onSettled()
                  }}
                  className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-xs font-semibold"
                >
                  Try again
                </button>
                <button onClick={handleClose} className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold">
                  Close
                </button>
              </div>
            </div>
          )}

          {phase === 'unknown' && (
            <div className="space-y-3 text-center py-2">
              <div className="w-12 h-12 bg-amber-100 text-amber-800 rounded-full flex items-center justify-center mx-auto text-xl font-bold">?</div>
              <div className="font-semibold text-slate-800">We could not confirm the result yet</div>
              <p className="text-xs text-slate-500">
                {notice || 'Do not resend. Check the status first — if the money left your account, this record will update.'}
              </p>
              {error && <div className="bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl p-3">{error}</div>}
              <div className="flex justify-center gap-3">
                <button
                  onClick={handleCheckStatus}
                  disabled={submitting || !txn}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold disabled:opacity-50"
                >
                  {submitting ? 'Checking…' : 'Check status'}
                </button>
                <button onClick={handleClose} className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold">
                  Close
                </button>
              </div>
            </div>
          )}

          {txn && (phase === 'waiting' || phase === 'unknown') && (
            <div className="text-xs text-slate-400 border-t border-slate-100 pt-3 flex justify-between">
              <span>Ref: {txn.reference}</span>
              <span>{mpesaStatusLabel(txn.status)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default MpesaPaymentModal
