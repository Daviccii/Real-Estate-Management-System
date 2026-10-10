import React from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import AnalyticsDashboard from './AnalyticsDashboard'
import { useAuth } from '../contexts/AuthContext'
import { getAnalyticsDashboard } from '../services/analytics'
import type { AnalyticsEnvelope } from '../services/analytics'

vi.mock('../contexts/AuthContext')
vi.mock('../services/analytics', () => ({
  getAnalyticsDashboard: vi.fn(),
}))

const envelope = (overrides: Partial<AnalyticsEnvelope> = {}): AnalyticsEnvelope => ({
  generated_at: '2026-10-10T09:00:00',
  months: 6,
  period: { start: '2026-05-01T00:00:00', end: '2026-10-31T23:59:59' },
  kpis: {
    properties: 2,
    total_units: 8,
    occupied_units: 6,
    vacant_units: 2,
    occupancy_rate: 75,
    active_leases: 6,
    leases_expiring_soon: 1,
    open_maintenance: 2,
    overdue_payments: 1,
    period_expected: 100000,
    period_collected: 80000,
    period_collection_rate: 80,
    period_expenses: 12000,
    period_net: 68000,
  },
  series: {
    financial: [
      { month: '2026-05', income: 0, expenses: 0, net: 0 },
      { month: '2026-06', income: 40000, expenses: 2000, net: 38000 },
    ],
    payments: [{ month: '2026-05', expected: 50000, collected: 45000, outstanding: 5000 }],
    maintenance: [{ month: '2026-05', requests: 3, resolved: 2, cost: 1500 }],
  },
  distributions: {
    units_by_status: { occupied: 6, vacant: 2 },
    leases_by_status: { active: 6 },
    properties_by_city: [{ city: 'Nairobi', count: 2 }],
    maintenance_by_category: [{ category: 'Plumbing', requests: 2, open: 1, cost: 1500 }],
  },
  top_properties: [
    {
      property_id: 1,
      name: 'Alpha Court',
      city: 'Nairobi',
      units: 4,
      occupied: 3,
      occupancy_rate: 75,
      collected: 45000,
      outstanding: 5000,
    },
  ],
  ...overrides,
})

const emptyEnvelope = (): AnalyticsEnvelope =>
  envelope({
    series: {
      financial: [{ month: '2026-05', income: 0, expenses: 0, net: 0 }],
      payments: [{ month: '2026-05', expected: 0, collected: 0, outstanding: 0 }],
      maintenance: [{ month: '2026-05', requests: 0, resolved: 0, cost: 0 }],
    },
    distributions: {
      units_by_status: {},
      leases_by_status: {},
      properties_by_city: [],
      maintenance_by_category: [],
    },
    top_properties: [],
  })

describe('AnalyticsDashboard', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({ user: { id: 1, role: 'admin' } } as any)
    vi.mocked(getAnalyticsDashboard).mockResolvedValue(envelope())
  })

  it('loads the default range and renders role-specific KPIs and charts', async () => {
    render(<AnalyticsDashboard />)

    expect(await screen.findByText('Platform Analytics')).toBeInTheDocument()
    expect(getAnalyticsDashboard).toHaveBeenCalledWith(6)
    expect(screen.getByRole('button', { name: '6 months' })).toHaveAttribute('aria-pressed', 'true')

    expect(screen.getByRole('region', { name: 'Net position' })).toHaveTextContent('KSh 68,000')
    expect(screen.getByRole('region', { name: 'Collected in period' })).toHaveTextContent(
      'KSh 80,000',
    )
    expect(screen.getAllByText('75%').length).toBeGreaterThanOrEqual(2)

    expect(
      screen.getByRole('img', { name: 'Monthly income, expenses and net position' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('img', { name: 'Monthly collected and outstanding rent' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Units by status' })).toBeInTheDocument()
    expect(
      screen.getByRole('img', { name: 'Monthly maintenance requests and resolutions' }),
    ).toBeInTheDocument()

    expect(screen.getByText('Alpha Court')).toBeInTheDocument()
    expect(screen.getAllByText('Nairobi').length).toBeGreaterThanOrEqual(2)
    expect(screen.getByText('Plumbing')).toBeInTheDocument()
  })

  it('refetches when another time range is selected', async () => {
    render(<AnalyticsDashboard />)
    await screen.findByText('Platform Analytics')

    fireEvent.click(screen.getByRole('button', { name: '12 months' }))

    await waitFor(() => expect(getAnalyticsDashboard).toHaveBeenLastCalledWith(12))
    expect(screen.getByRole('button', { name: '12 months' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('falls back to the manager heading for manager users', async () => {
    vi.mocked(useAuth).mockReturnValue({ user: { id: 2, role: 'manager' } } as any)

    render(<AnalyticsDashboard />)

    expect(await screen.findByText('Operations Analytics')).toBeInTheDocument()
    expect(screen.queryByText('Platform Analytics')).not.toBeInTheDocument()
  })

  it('renders honest empty states for sparse portfolios', async () => {
    vi.mocked(getAnalyticsDashboard).mockResolvedValue(emptyEnvelope())

    render(<AnalyticsDashboard />)

    expect(await screen.findByText('No maintenance in this period')).toBeInTheDocument()
    expect(screen.getAllByText('No properties in scope')).toHaveLength(2)
    expect(screen.getAllByText('No data for this period')).toHaveLength(4)
  })

  it('surfaces load failures to the user', async () => {
    vi.mocked(getAnalyticsDashboard).mockRejectedValue(new Error('boom'))

    render(<AnalyticsDashboard />)

    expect(await screen.findByText('boom')).toBeInTheDocument()
  })
})
