import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { getReport, downloadReportCsv } from './reports'
import { api } from './api'
import { getToken } from './token'

vi.mock('./api', () => ({
  api: { request: vi.fn() },
}))

vi.mock('./token', () => ({
  getToken: vi.fn(),
}))

const clickedAnchors: HTMLAnchorElement[] = []

beforeEach(() => {
  clickedAnchors.length = 0
  vi.mocked(getToken).mockReturnValue('token-123')

  const createObjectURL = vi.fn(() => 'blob:mock-url')
  const revokeObjectURL = vi.fn()
  vi.stubGlobal('URL', {
    ...globalThis.URL,
    createObjectURL,
    revokeObjectURL,
  })

  const createElement = document.createElement.bind(document)
  vi.spyOn(document, 'createElement').mockImplementation((tagName: string, options?: ElementCreationOptions) => {
    const element = createElement(tagName, options)
    if (tagName === 'a') {
      const anchor = element as HTMLAnchorElement
      anchor.click = vi.fn()
      clickedAnchors.push(anchor)
    }
    return element
  })
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('getReport', () => {
  it('requests the report path with the query parameters', async () => {
    vi.mocked(api.request).mockResolvedValue({ report_type: 'payments', rows: [] })

    const result = await getReport('payments', { date_from: '2026-01-01', property_id: 3 })

    expect(api.request).toHaveBeenCalledWith('/reports/payments?date_from=2026-01-01&property_id=3')
    expect(result).toEqual({ report_type: 'payments', rows: [] })
  })

  it('omits empty parameters', async () => {
    vi.mocked(api.request).mockResolvedValue({ report_type: 'occupancy', rows: [] })

    await getReport('occupancy', { date_from: '', date_to: undefined, property_id: undefined })

    expect(api.request).toHaveBeenCalledWith('/reports/occupancy')
  })

  it('returns no query string when params are absent', async () => {
    vi.mocked(api.request).mockResolvedValue({ report_type: 'financial', rows: [] })

    await getReport('financial')

    expect(api.request).toHaveBeenCalledWith('/reports/financial')
  })
})

describe('downloadReportCsv', () => {
  it('fetches the CSV endpoint with a bearer token and a format param', async () => {
    const blob = new Blob(['report'], { type: 'text/csv' })
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      blob: vi.fn().mockResolvedValue(blob),
      status: 200,
    })
    vi.stubGlobal('fetch', fetchMock)

    await downloadReportCsv('maintenance', { date_from: '2026-01-01' })

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toContain('/api/v1/reports/maintenance')
    expect(url).toContain('date_from=2026-01-01')
    expect(url).toContain('format=csv')
    expect((init as RequestInit).headers).toMatchObject({ Authorization: 'Bearer token-123' })
    expect(clickedAnchors).toHaveLength(1)
    expect(clickedAnchors[0].click).toHaveBeenCalled()
    expect(clickedAnchors[0].download).toMatch(/^propnoxa_maintenance_report_\d{8}\.csv$/)
  })

  it('throws when the download fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: false, status: 403, blob: vi.fn() }),
    )

    await expect(downloadReportCsv('financial')).rejects.toThrow('Could not download the report')
    expect(clickedAnchors).toHaveLength(0)
  })
})
