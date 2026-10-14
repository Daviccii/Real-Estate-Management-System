import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  MpesaTransaction,
  isAwaitingCallback,
  isLiveMpesaTransaction,
  mpesaService,
  mpesaStatusLabel,
} from './mpesa'
import { setToken } from './token'

const jsonResponse = (body: unknown, status = 200) =>
  new Response(typeof body === 'string' ? body : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })

const txn: MpesaTransaction = {
  id: 7,
  reference: 'MPX-ABCD1234',
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
}

describe('mpesaService', () => {
  beforeEach(() => {
    setToken(null)
  })

  it('reads the config from the versioned endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({ configured: true, environment: 'sandbox', production_enabled: false, missing: [] }),
    )
    vi.stubGlobal('fetch', fetchMock)

    const config = await mpesaService.getConfig()

    expect(config.configured).toBe(true)
    expect(fetchMock.mock.calls[0][0]).toMatch(/\/api\/v1\/mpesa\/config$/)
  })

  it('posts an STK push request as JSON', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(txn))
    vi.stubGlobal('fetch', fetchMock)

    await mpesaService.initiate({ payment_id: 3, phone_number: '0712345678', amount: '1200' })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toMatch(/\/api\/v1\/mpesa\/stk-push$/)
    expect(options.method).toBe('POST')
    expect((options.headers as Headers).get('Content-Type')).toBe('application/json')
    expect(JSON.parse(options.body)).toEqual({ payment_id: 3, phone_number: '0712345678', amount: '1200' })
  })

  it('builds transaction list query params', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse([txn]))
    vi.stubGlobal('fetch', fetchMock)

    await mpesaService.listTransactions({ limit: 20, payment_id: 3, status: 'succeeded' })

    const url = fetchMock.mock.calls[0][0] as string
    expect(url).toMatch(/\/api\/v1\/mpesa\/transactions\?/)
    expect(url).toContain('limit=20')
    expect(url).toContain('payment_id=3')
    expect(url).toContain('status=succeeded')
  })

  it('fetches a single transaction and reconciles it', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(txn))
      .mockResolvedValueOnce(jsonResponse({ ...txn, status: 'succeeded' }))
    vi.stubGlobal('fetch', fetchMock)

    await mpesaService.getTransaction(7)
    const reconciled = await mpesaService.reconcile(7)

    expect(fetchMock.mock.calls[0][0]).toMatch(/\/api\/v1\/mpesa\/transactions\/7$/)
    expect(fetchMock.mock.calls[1][0]).toMatch(/\/api\/v1\/mpesa\/transactions\/7\/reconcile$/)
    expect(fetchMock.mock.calls[1][1].method).toBe('POST')
    expect(reconciled.status).toBe('succeeded')
  })

  it('surfaces backend error messages', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      jsonResponse({ detail: { message: 'Too many M-Pesa requests. Please wait a little before trying again.' } }, 429),
    ))

    await expect(mpesaService.initiate({ payment_id: 3, phone_number: '0712345678', amount: '100' }))
      .rejects.toThrow(/Too many M-Pesa requests/)
  })
})

describe('status helpers', () => {
  it('classifies live vs terminal transactions', () => {
    expect(isLiveMpesaTransaction({ status: 'pending' })).toBe(true)
    expect(isLiveMpesaTransaction({ status: 'awaiting_callback' })).toBe(true)
    expect(isLiveMpesaTransaction({ status: 'unknown' })).toBe(true)
    expect(isLiveMpesaTransaction({ status: 'succeeded' })).toBe(false)
    expect(isLiveMpesaTransaction({ status: 'failed' })).toBe(false)
  })

  it('treats only pending/awaiting_callback as waiting-for-PIN', () => {
    expect(isAwaitingCallback({ status: 'pending' })).toBe(true)
    expect(isAwaitingCallback({ status: 'awaiting_callback' })).toBe(true)
    expect(isAwaitingCallback({ status: 'unknown' })).toBe(false)
    expect(isAwaitingCallback({ status: 'succeeded' })).toBe(false)
  })

  it('renders human labels for every status', () => {
    expect(mpesaStatusLabel('awaiting_callback')).toBe('Awaiting PIN')
    expect(mpesaStatusLabel('succeeded')).toBe('Paid')
    expect(mpesaStatusLabel('cancelled')).toBe('Cancelled')
    expect(mpesaStatusLabel('timed_out')).toBe('Timed out')
    expect(mpesaStatusLabel('expired')).toBe('Expired')
    expect(mpesaStatusLabel('failed')).toBe('Failed')
    expect(mpesaStatusLabel('unknown')).toBe('Needs checking')
  })
})
