import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from './api'
import { getAnalyticsDashboard } from './analytics'

vi.mock('./api', () => ({
  api: { request: vi.fn() },
}))

describe('getAnalyticsDashboard', () => {
  beforeEach(() => {
    vi.mocked(api.request).mockResolvedValue({ months: 6 })
  })

  it('requests the dashboard endpoint with the month window', async () => {
    const result = await getAnalyticsDashboard(6)

    expect(api.request).toHaveBeenCalledWith('/analytics/dashboard?months=6')
    expect(result).toEqual({ months: 6 })
  })

  it('passes wider windows through unchanged', async () => {
    await getAnalyticsDashboard(12)

    expect(api.request).toHaveBeenLastCalledWith('/analytics/dashboard?months=12')
  })
})
