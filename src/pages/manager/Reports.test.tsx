import React from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import ManagerReports from './Reports'
import { managerService } from '../../services/manager'
import { downloadReportCsv, getReport } from '../../services/reports'
import type { ReportEnvelope } from '../../services/reports'

vi.mock('../../services/manager', () => ({
  managerService: { getProperties: vi.fn() },
}))

vi.mock('../../services/reports', () => ({
  getReport: vi.fn(),
  downloadReportCsv: vi.fn(),
}))

const occupancyReport = (overrides: Partial<ReportEnvelope> = {}): ReportEnvelope => ({
  report_type: 'occupancy',
  generated_at: '2026-10-10T09:00:00',
  filters: { date_from: null, date_to: null, property_id: null },
  summary: [
    { key: 'properties', label: 'Properties', value: 1 },
    { key: 'occupancy_rate', label: 'Occupancy rate %', value: 50 },
  ],
  columns: [
    { key: 'property', label: 'Property' },
    { key: 'units', label: 'Units' },
    { key: 'occupancy_rate', label: 'Occupancy %' },
  ],
  rows: [{ property: 'Alpha Court', units: 2, occupancy_rate: 50 }],
  ...overrides,
})

describe('ManagerReports', () => {
  beforeEach(() => {
    vi.mocked(managerService.getProperties).mockResolvedValue([
      { id: 7, name: 'Alpha Court' } as any,
    ])
    vi.mocked(getReport).mockResolvedValue(occupancyReport())
    vi.mocked(downloadReportCsv).mockResolvedValue(undefined)
  })

  it('loads the occupancy report on mount', async () => {
    render(<ManagerReports />)

    // Rendered both in the property filter and in the report table.
    expect((await screen.findAllByText('Alpha Court')).length).toBeGreaterThanOrEqual(2)
    expect(getReport).toHaveBeenCalledWith('occupancy', {})
    // Summary card and table cell both render the rate.
    expect(screen.getAllByText('50%').length).toBeGreaterThanOrEqual(2)
    expect(screen.getByText('Occupancy rate %')).toBeInTheDocument()
  })

  it('switches report types via the tabs', async () => {
    render(<ManagerReports />)
    await screen.findAllByText('Alpha Court')

    vi.mocked(getReport).mockResolvedValue(
      occupancyReport({
        report_type: 'financial',
        summary: [{ key: 'net_income', label: 'Net', value: -1200.5 }],
        columns: [
          { key: 'month', label: 'Month' },
          { key: 'net', label: 'Net' },
        ],
        rows: [{ month: '2026-10', net: -1200.5 }],
      }),
    )

    fireEvent.click(screen.getByRole('tab', { name: 'Financial' }))

    expect(await screen.findByText('2026-10')).toBeInTheDocument()
    expect(getReport).toHaveBeenLastCalledWith('financial', {})
    expect(screen.getAllByText('-1,200.5').length).toBeGreaterThan(0)
  })

  it('passes the filters to the API and the CSV export', async () => {
    render(<ManagerReports />)
    await screen.findAllByText('Alpha Court')

    fireEvent.change(screen.getByLabelText('From date'), { target: { value: '2026-01-01' } })
    fireEvent.change(screen.getByLabelText('To date'), { target: { value: '2026-03-31' } })
    fireEvent.change(screen.getByLabelText('Property filter'), { target: { value: '7' } })

    const expectedParams = {
      date_from: '2026-01-01',
      date_to: '2026-03-31T23:59:59',
      property_id: 7,
    }
    await waitFor(() => expect(getReport).toHaveBeenLastCalledWith('occupancy', expectedParams))

    fireEvent.click(screen.getByRole('button', { name: /download csv/i }))
    await waitFor(() => expect(downloadReportCsv).toHaveBeenCalledWith('occupancy', expectedParams))
  })

  it('shows the empty state when the report has no rows', async () => {
    vi.mocked(getReport).mockResolvedValue(occupancyReport({ rows: [] }))

    render(<ManagerReports />)

    expect(await screen.findByText(/no data for the selected filters/i)).toBeInTheDocument()
  })

  it('surfaces failures to the user', async () => {
    vi.mocked(getReport).mockRejectedValue(new Error('boom'))

    render(<ManagerReports />)

    expect(await screen.findByText('boom')).toBeInTheDocument()
  })

  it('flags download failures without losing the preview', async () => {
    vi.mocked(downloadReportCsv).mockRejectedValue(new Error('Could not download the report'))

    render(<ManagerReports />)
    await screen.findAllByText('Alpha Court')

    fireEvent.click(screen.getByRole('button', { name: /download csv/i }))

    expect(await screen.findByText('Could not download the report')).toBeInTheDocument()
    expect(screen.getAllByText('Alpha Court').length).toBeGreaterThanOrEqual(2)
  })
})
