import React from 'react'
import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import TenantPayments from './Payments'
import { getMyPayments } from '../../services/tenant'
import { MpesaTransaction, mpesaService } from '../../services/mpesa'
import { ApiError } from '../../services/api'

vi.mock('../../services/tenant', () => ({ getMyPayments: vi.fn() }))

vi.mock('../../services/mpesa', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../services/mpesa')>()
  return {
    ...actual,
    mpesaService: {
      getConfig: vi.fn(),
      initiate: vi.fn(),
      listTransactions: vi.fn(),
      getTransaction: vi.fn(),
      reconcile: vi.fn(),
    },
  }
})

const pendingPayment = {
  id: 3,
  tenant_id: 12,
  lease_id: 4,
  property_id: 2,
  unit_id: 9,
  amount: '1200',
  due_date: '2026-10-05',
  status: 'pending',
  payment_method: null,
  reference: 'PAY-000003',
  property_name: 'Kilimani Heights',
  unit_number: 'B4',
  outstanding_amount: '1200.00',
}

const liveTxn = (overrides: Partial<MpesaTransaction> = {}): MpesaTransaction => ({
  id: 77,
  reference: 'MPX-LIVE01',
  payment_id: 3,
  tenant_id: 12,
  lease_id: 4,
  property_id: 2,
  unit_id: 9,
  amount: '1200.00',
  currency: 'KES',
  channel: 'mpesa_stk',
  phone_number: '2547****678',
  status: 'awaiting_callback',
  applied_to_payment: false,
  callback_attempts: 0,
  initiated_at: new Date(Date.now() - 60_000).toISOString(),
  ...overrides,
})

const flush = async () => {
  await act(async () => {
    for (let i = 0; i < 10; i += 1) await Promise.resolve()
  })
}

describe('TenantPayments', () => {
  beforeEach(() => {
    vi.mocked(getMyPayments).mockResolvedValue([pendingPayment])
    vi.mocked(mpesaService.getConfig).mockResolvedValue({
      configured: true,
      environment: 'sandbox',
      production_enabled: false,
      missing: [],
    })
    vi.mocked(mpesaService.listTransactions).mockResolvedValue([])
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('hides M-Pesa controls entirely when the integration is not configured', async () => {
    vi.mocked(mpesaService.getConfig).mockResolvedValue({
      configured: false,
      environment: 'sandbox',
      production_enabled: false,
      missing: ['MPESA_CONSUMER_KEY'],
    })

    render(<TenantPayments />)

    await screen.findByText('Transaction History')
    expect(screen.queryByText(/Pay with M-Pesa/)).toBeNull()
  })

  it('offers a pay button for an outstanding bill and prefills the balance', async () => {
    render(<TenantPayments />)

    const payButton = await screen.findByText('📱 Pay with M-Pesa')
    fireEvent.click(payButton)

    expect(screen.getByText('Pay with M-Pesa')).toBeTruthy()
    expect(screen.getByText('Outstanding balance')).toBeTruthy()
    expect((screen.getByLabelText('Amount (KSh)') as HTMLInputElement).value).toBe('1200.00')
  })

  it('never shows success from the STK acceptance alone, then confirms only after the polled callback', async () => {
    vi.useFakeTimers()
    vi.mocked(mpesaService.initiate).mockResolvedValue(liveTxn())
    vi.mocked(mpesaService.getTransaction).mockResolvedValue(
      liveTxn({ status: 'succeeded', mpesa_receipt_number: 'SJK123ABC', applied_to_payment: true }),
    )

    render(<TenantPayments />)
    await flush()

    fireEvent.click(screen.getByText('📱 Pay with M-Pesa'))
    fireEvent.change(screen.getByLabelText('M-Pesa phone number'), { target: { value: '0712345678' } })
    fireEvent.click(screen.getByText(/Send M-Pesa request/))
    await flush()

    // STK accepted: waiting for the tenant, NOT a payment.
    expect(mpesaService.initiate).toHaveBeenCalledWith({
      payment_id: 3,
      phone_number: '0712345678',
      amount: '1200',
    })
    expect(screen.getByText('Check your phone now')).toBeTruthy()
    expect(screen.getByText(/Enter your M-Pesa PIN/)).toBeTruthy()
    expect(screen.queryByText('Payment confirmed')).toBeNull()

    // First poll returns the reconciled success from the backend.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000)
    })

    expect(screen.getByText('Payment confirmed')).toBeTruthy()
    expect(screen.getByText('SJK123ABC')).toBeTruthy()
  })

  it('stops polling on unmount', async () => {
    vi.useFakeTimers()
    vi.mocked(mpesaService.initiate).mockResolvedValue(liveTxn())
    vi.mocked(mpesaService.getTransaction).mockResolvedValue(liveTxn())

    const { unmount } = render(<TenantPayments />)
    await flush()

    fireEvent.click(screen.getByText('📱 Pay with M-Pesa'))
    fireEvent.change(screen.getByLabelText('M-Pesa phone number'), { target: { value: '0712345678' } })
    fireEvent.click(screen.getByText(/Send M-Pesa request/))
    await flush()

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000)
    })
    const callsBeforeUnmount = vi.mocked(mpesaService.getTransaction).mock.calls.length
    expect(callsBeforeUnmount).toBeGreaterThan(0)

    unmount()
    await act(async () => {
      await vi.advanceTimersByTimeAsync(30000)
    })
    expect(vi.mocked(mpesaService.getTransaction).mock.calls.length).toBe(callsBeforeUnmount)
  })

  it('shows a clear cancelled state without claiming a payment', async () => {
    vi.useFakeTimers()
    vi.mocked(mpesaService.initiate).mockResolvedValue(liveTxn())
    vi.mocked(mpesaService.getTransaction).mockResolvedValue(
      liveTxn({ status: 'cancelled', result_code: 1032, failure_reason: 'Request cancelled by user' }),
    )

    render(<TenantPayments />)
    await flush()

    fireEvent.click(screen.getByText('📱 Pay with M-Pesa'))
    fireEvent.change(screen.getByLabelText('M-Pesa phone number'), { target: { value: '0712345678' } })
    fireEvent.click(screen.getByText(/Send M-Pesa request/))
    await flush()

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000)
    })

    expect(screen.getByText('You cancelled the M-Pesa prompt')).toBeTruthy()
    expect(screen.queryByText('Payment confirmed')).toBeNull()
    expect(screen.getByText('Try again')).toBeTruthy()
  })

  it('blocks submission with an invalid phone number without calling the API', async () => {
    render(<TenantPayments />)
    await screen.findByText('📱 Pay with M-Pesa')

    fireEvent.click(screen.getByText('📱 Pay with M-Pesa'))
    fireEvent.change(screen.getByLabelText('M-Pesa phone number'), { target: { value: '0812345678' } })
    fireEvent.click(screen.getByText(/Send M-Pesa request/))

    expect(screen.getByText(/valid Safaricom number/)).toBeTruthy()
    expect(mpesaService.initiate).not.toHaveBeenCalled()
  })

  it('adopts an existing in-progress request (409) instead of sending a second prompt', async () => {
    vi.useFakeTimers()
    vi.mocked(mpesaService.initiate).mockRejectedValue(
      new ApiError('Conflict', 409, {
        detail: { message: 'A payment request for this obligation is already in progress', transaction: liveTxn() },
      }),
    )
    vi.mocked(mpesaService.getTransaction).mockResolvedValue(liveTxn())

    render(<TenantPayments />)
    await flush()

    fireEvent.click(screen.getByText('📱 Pay with M-Pesa'))
    fireEvent.change(screen.getByLabelText('M-Pesa phone number'), { target: { value: '0712345678' } })
    fireEvent.click(screen.getByText(/Send M-Pesa request/))
    await flush()

    expect(screen.getByText(/already in progress/)).toBeTruthy()
    expect(screen.getByText('Check your phone now')).toBeTruthy()
    expect(screen.queryByText('Payment confirmed')).toBeNull()
  })

  it('reflects a terminal 502 immediately instead of claiming the result is unconfirmed', async () => {
    vi.mocked(mpesaService.initiate).mockRejectedValue(
      new ApiError('Bad Gateway', 502, {
        detail: {
          message: 'Safaricom rejected the OAuth credentials (HTTP 400)',
          transaction: liveTxn({
            status: 'failed',
            failure_reason: 'Safaricom rejected the OAuth credentials (HTTP 400)',
            completed_at: '2026-10-11T10:00:05',
          }),
        },
      }),
    )

    render(<TenantPayments />)
    await flush()

    fireEvent.click(screen.getByText('📱 Pay with M-Pesa'))
    fireEvent.change(screen.getByLabelText('M-Pesa phone number'), { target: { value: '0712345678' } })
    fireEvent.click(screen.getByText(/Send M-Pesa request/))
    await flush()

    expect(screen.queryByText('Payment confirmed')).toBeNull()
    expect(screen.getByText('The payment was not completed')).toBeTruthy()
    expect(screen.getByText(/OAuth credentials/)).toBeTruthy()
    expect(screen.queryByText('We could not confirm the result yet')).toBeNull()
  })

  it('keeps the unconfirmed state when a 502 carries a genuinely live attempt', async () => {
    vi.mocked(mpesaService.initiate).mockRejectedValue(
      new ApiError('Bad Gateway', 502, {
        detail: {
          message: 'Safaricom returned HTTP 503; the outcome must be confirmed',
          transaction: liveTxn({ status: 'unknown' }),
        },
      }),
    )

    render(<TenantPayments />)
    await flush()

    fireEvent.click(screen.getByText('📱 Pay with M-Pesa'))
    fireEvent.change(screen.getByLabelText('M-Pesa phone number'), { target: { value: '0712345678' } })
    fireEvent.click(screen.getByText(/Send M-Pesa request/))
    await flush()

    expect(screen.getByText('We could not confirm the result yet')).toBeTruthy()
    expect(screen.queryByText('Payment confirmed')).toBeNull()
    expect(screen.queryByText('The payment was not completed')).toBeNull()
  })

  it('resumes tracking a live attempt from the activity list', async () => {
    vi.useFakeTimers()
    vi.mocked(mpesaService.listTransactions).mockResolvedValue([liveTxn()])
    vi.mocked(mpesaService.getTransaction).mockResolvedValue(
      liveTxn({ status: 'succeeded', mpesa_receipt_number: 'SJK999', applied_to_payment: true }),
    )

    render(<TenantPayments />)
    await flush()

    fireEvent.click(screen.getByText('⏳ Check payment'))
    await flush()

    expect(screen.getByText('Check your phone now')).toBeTruthy()
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000)
    })
    expect(screen.getByText('Payment confirmed')).toBeTruthy()
    expect(mpesaService.initiate).not.toHaveBeenCalled()
  })

  it('offers a fresh prompt when the only live attempt is older than the duplicate window', async () => {
    vi.mocked(mpesaService.listTransactions).mockResolvedValue([
      liveTxn({ initiated_at: new Date(Date.now() - 10 * 60 * 1000).toISOString() }),
    ])

    render(<TenantPayments />)
    await flush()

    expect(screen.queryByText('⏳ Check payment')).toBeNull()
    fireEvent.click(screen.getByText('📱 Pay with M-Pesa'))
    await flush()

    expect(screen.getByLabelText('M-Pesa phone number')).toBeTruthy()
    expect(mpesaService.initiate).not.toHaveBeenCalled()
  })

  it('lists M-Pesa attempts with receipts in the activity table', async () => {
    vi.mocked(mpesaService.listTransactions).mockResolvedValue([
      liveTxn({ status: 'succeeded', mpesa_receipt_number: 'SJK555XYZ', applied_to_payment: true }),
    ])

    render(<TenantPayments />)

    await screen.findByText('M-Pesa Payment Attempts')
    expect(screen.getByText('MPX-LIVE01')).toBeTruthy()
    expect(screen.getByText('SJK555XYZ')).toBeTruthy()
    expect(screen.getByText('2547****678')).toBeTruthy()
  })
})
