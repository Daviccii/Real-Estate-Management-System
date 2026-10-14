import { api } from './api'

export interface MpesaConfig {
  configured: boolean
  environment: string
  production_enabled: boolean
  missing: string[]
}

export interface MpesaTransaction {
  id: number
  reference: string
  payment_id: number
  tenant_id: number
  lease_id: number
  property_id: number
  unit_id: number
  landlord_id?: number | null
  company_id?: number | null
  amount: string
  currency: string
  channel: string
  phone_number: string // masked server-side, e.g. 2547****678
  status: string
  result_code?: number | null
  result_description?: string | null
  failure_reason?: string | null
  merchant_request_id?: string | null
  checkout_request_id?: string | null
  mpesa_receipt_number?: string | null
  applied_to_payment: boolean
  callback_attempts: number
  initiated_at?: string | null
  callback_received_at?: string | null
  completed_at?: string | null
  reconciled_at?: string | null
  created_at?: string | null
  updated_at?: string | null
  property_name?: string | null
  unit_number?: string | null
  tenant_name?: string | null
}

export interface MpesaStkPushPayload {
  payment_id: number
  phone_number: string
  amount: string
}

export interface MpesaListParams {
  skip?: number
  limit?: number
  status?: string
  payment_id?: number
}

export interface MpesaRefundCreate {
  amount: string
  reason: string
  reversal_reference?: string
}

export interface MpesaRefund {
  id: number
  mpesa_transaction_id: number
  payment_id?: number | null
  amount: string
  currency: string
  reason: string
  reversal_reference?: string | null
  status: string
  recorded_by?: number | null
  created_at: string
  updated_at?: string | null
}

export interface MpesaRefundResult {
  refund: MpesaRefund
  transaction: MpesaTransaction
}

export const LIVE_MPESA_STATUSES = ['pending', 'awaiting_callback', 'unknown'] as const
export const TERMINAL_MPESA_STATUSES = ['succeeded', 'failed', 'cancelled', 'timed_out', 'expired'] as const

export function isLiveMpesaTransaction(txn: Pick<MpesaTransaction, 'status'>): boolean {
  return (LIVE_MPESA_STATUSES as readonly string[]).includes(txn.status)
}

// A live attempt means "waiting for the tenant to finish on their phone" —
// the UI must never treat the STK acceptance response as proof of payment.
export function isAwaitingCallback(txn: Pick<MpesaTransaction, 'status'>): boolean {
  return txn.status === 'pending' || txn.status === 'awaiting_callback'
}

export function mpesaStatusLabel(status: string): string {
  switch (status) {
    case 'pending':
    case 'awaiting_callback':
      return 'Awaiting PIN'
    case 'succeeded':
      return 'Paid'
    case 'cancelled':
      return 'Cancelled'
    case 'timed_out':
      return 'Timed out'
    case 'expired':
      return 'Expired'
    case 'failed':
      return 'Failed'
    case 'unknown':
      return 'Needs checking'
    default:
      return status
  }
}

export const mpesaService = {
  getConfig: async (): Promise<MpesaConfig> => {
    return api.request<MpesaConfig>('/mpesa/config')
  },

  initiate: async (payload: MpesaStkPushPayload): Promise<MpesaTransaction> => {
    return api.request<MpesaTransaction>('/mpesa/stk-push', {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    })
  },

  listTransactions: async (params?: MpesaListParams): Promise<MpesaTransaction[]> => {
    const queryParams = new URLSearchParams()
    if (params?.skip) queryParams.append('skip', params.skip.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.status) queryParams.append('status', params.status)
    if (params?.payment_id) queryParams.append('payment_id', params.payment_id.toString())
    return api.request<MpesaTransaction[]>(`/mpesa/transactions?${queryParams}`)
  },

  getTransaction: async (transactionId: number): Promise<MpesaTransaction> => {
    return api.request<MpesaTransaction>(`/mpesa/transactions/${transactionId}`)
  },

  reconcile: async (transactionId: number): Promise<MpesaTransaction> => {
    return api.request<MpesaTransaction>(`/mpesa/transactions/${transactionId}/reconcile`, {
      method: 'POST',
    })
  },

  createRefund: async (transactionId: number, payload: MpesaRefundCreate): Promise<MpesaRefundResult> => {
    return api.request<MpesaRefundResult>(`/mpesa/transactions/${transactionId}/refunds`, {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    })
  },
}
