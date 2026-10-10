import React from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import ProviderOpenJobs from './OpenJobs'
import { getOpenRequests, submitQuote } from '../../services/serviceMarketplace'
import type { OpenMaintenanceRequest, Paginated } from '../../types'

vi.mock('../../services/serviceMarketplace', () => ({
  getOpenRequests: vi.fn(),
  submitQuote: vi.fn(),
}))

const job = (overrides: Partial<OpenMaintenanceRequest> = {}): OpenMaintenanceRequest => ({
  id: 11,
  title: 'Burst pipe in kitchen',
  description: 'Water spraying under the sink.',
  category: 'plumbing',
  priority: 'high',
  status: 'open',
  city: 'Nairobi',
  county: 'Nairobi',
  property_type: 'Apartment',
  created_at: '2026-10-01T09:00:00',
  quotes_count: 2,
  my_quote_id: null,
  my_quote_status: null,
  my_quote_amount: null,
  ...overrides,
})

const jobPage = (items: OpenMaintenanceRequest[]): Paginated<OpenMaintenanceRequest> => ({
  items,
  total: items.length,
  page: 1,
  page_size: 12,
})

describe('ProviderOpenJobs', () => {
  beforeEach(() => {
    vi.mocked(getOpenRequests).mockResolvedValue(
      jobPage([
        job(),
        job({
          id: 12,
          title: 'Rewire sitting room',
          category: 'electrical',
          priority: 'medium',
          city: 'Nakuru',
          county: 'Nakuru',
          description: 'Old wiring needs a full circuit replacement.',
          quotes_count: 1,
          my_quote_id: 55,
          my_quote_status: 'pending',
          my_quote_amount: '18000',
        }),
      ]),
    )
    vi.mocked(submitQuote).mockResolvedValue({} as any)
  })

  it('loads open jobs on mount and marks tickets already quoted', async () => {
    render(<ProviderOpenJobs />)

    expect(await screen.findByText('Burst pipe in kitchen')).toBeInTheDocument()
    expect(getOpenRequests).toHaveBeenCalledWith(
      expect.objectContaining({ page: 1, page_size: 12 }),
    )

    expect(screen.getByText('Ticket #11')).toBeInTheDocument()
    expect(screen.getByText('2 open jobs available')).toBeInTheDocument()
    expect(screen.getByText('Nairobi, Nairobi · Apartment')).toBeInTheDocument()
    expect(screen.getByText('Water spraying under the sink.')).toBeInTheDocument()

    expect(screen.getByRole('button', { name: /Submit Quote/ })).toBeInTheDocument()
    expect(screen.getByText('✓ Quote sent — KSh 18000 (pending)')).toBeInTheDocument()
  })

  it('applies trade, text and city filters to the job search', async () => {
    render(<ProviderOpenJobs />)
    await screen.findByText('Burst pipe in kitchen')

    fireEvent.change(screen.getByLabelText('Filter by trade category'), {
      target: { value: 'plumbing' },
    })
    await waitFor(() =>
      expect(getOpenRequests).toHaveBeenLastCalledWith(
        expect.objectContaining({ category: 'plumbing', page: 1 }),
      ),
    )

    fireEvent.change(screen.getByLabelText('Search open jobs'), { target: { value: 'pipe' } })
    fireEvent.change(screen.getByLabelText('Filter by city'), { target: { value: 'Nairobi' } })
    fireEvent.click(screen.getByRole('button', { name: 'Search Jobs' }))

    await waitFor(() =>
      expect(getOpenRequests).toHaveBeenLastCalledWith(
        expect.objectContaining({ q: 'pipe', city: 'Nairobi', category: 'plumbing', page: 1 }),
      ),
    )
  })

  it('submits a quote from the job board and refreshes the list', async () => {
    render(<ProviderOpenJobs />)
    await screen.findByText('Burst pipe in kitchen')

    fireEvent.click(screen.getByRole('button', { name: /Submit Quote/ }))
    expect(await screen.findByRole('heading', { name: 'Submit Quote' })).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Total Quoted Amount (KSh) *'), {
      target: { value: '15000' },
    })
    fireEvent.change(screen.getByLabelText('Estimated Labor Hours'), { target: { value: '4' } })
    fireEvent.change(screen.getByLabelText('Scope of Work & Materials Breakdown *'), {
      target: { value: 'Replace the pipe segment and seal the joint.' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send Quote to Manager' }))

    await waitFor(() =>
      expect(submitQuote).toHaveBeenCalledWith({
        request_id: 11,
        quoted_amount: '15000',
        estimated_hours: 4,
        scope_description: 'Replace the pipe segment and seal the joint.',
      }),
    )

    expect(
      await screen.findByText(
        'Quote submitted for "Burst pipe in kitchen". The property manager will review it shortly.',
      ),
    ).toBeInTheDocument()
    await waitFor(() => expect(getOpenRequests).toHaveBeenCalledTimes(2))
  })

  it('shows the empty board state when no tickets match', async () => {
    vi.mocked(getOpenRequests).mockResolvedValue(jobPage([]))

    render(<ProviderOpenJobs />)

    expect(await screen.findByText('No Open Jobs Match')).toBeInTheDocument()
    expect(screen.getByText('0 open jobs available')).toBeInTheDocument()
  })

  it('surfaces board load failures', async () => {
    vi.mocked(getOpenRequests).mockRejectedValue(new Error('board offline'))

    render(<ProviderOpenJobs />)

    expect(await screen.findByText('board offline')).toBeInTheDocument()
  })
})
