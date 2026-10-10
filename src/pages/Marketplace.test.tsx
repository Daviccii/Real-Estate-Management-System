import React from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import Marketplace from './Marketplace'
import { useAuth } from '../contexts/AuthContext'
import { getMarketplaceProviders, getProviderReviews } from '../services/serviceMarketplace'
import type { Paginated, ProviderReviewPage, ServiceProviderProfile } from '../types'

vi.mock('../contexts/AuthContext')
vi.mock('../services/serviceMarketplace', () => ({
  getMarketplaceProviders: vi.fn(),
  getProviderReviews: vi.fn(),
}))

const provider = (overrides: Partial<ServiceProviderProfile> = {}): ServiceProviderProfile => ({
  id: 1,
  user_id: 10,
  company_name: 'Njoroge Plumbing Ltd',
  categories: ['Plumbing'],
  specialty: 'Plumbing',
  service_areas: ['Westlands', 'Kilimani'],
  hourly_rate: '2500',
  insurance_verified: true,
  rating_avg: 4.5,
  reviews_count: 8,
  completed_jobs_count: 23,
  is_available: true,
  created_at: '2026-09-01T00:00:00',
  ...overrides,
})

const providerPage = (items: ServiceProviderProfile[]): Paginated<ServiceProviderProfile> => ({
  items,
  total: items.length,
  page: 1,
  page_size: 12,
})

const reviewPage = (): ProviderReviewPage => ({
  items: [
    {
      id: 101,
      provider_id: 1,
      work_order_id: 31,
      score: 5,
      comment: 'Fixed a persistent leak quickly.',
      created_at: '2026-10-05T09:00:00',
      reviewer_name: 'Mary W.',
      maintenance_title: 'Plumbing leak repair',
    },
  ],
  total: 1,
  page: 1,
  page_size: 10,
  rating_avg: 4.5,
  reviews_count: 8,
})

describe('Marketplace', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({ user: { id: 2, role: 'manager' } } as any)
    vi.mocked(getMarketplaceProviders).mockResolvedValue(
      providerPage([
        provider(),
        provider({
          id: 2,
          company_name: 'Sparky Electrical',
          categories: ['Electrical'],
          specialty: 'Electrical',
          service_areas: [],
          hourly_rate: null,
          insurance_verified: false,
          rating_avg: null,
          reviews_count: 0,
          completed_jobs_count: 0,
          is_available: false,
        }),
      ]),
    )
    vi.mocked(getProviderReviews).mockResolvedValue(reviewPage())
  })

  it('loads providers with default sort and renders ratings, jobs and availability', async () => {
    render(<Marketplace />)

    expect(await screen.findByText('Njoroge Plumbing Ltd')).toBeInTheDocument()
    expect(getMarketplaceProviders).toHaveBeenCalledWith(
      expect.objectContaining({ sort: 'rating', page: 1, page_size: 12 }),
    )

    expect(screen.getByText('4.5')).toBeInTheDocument()
    expect(screen.getByText('(8 reviews)')).toBeInTheDocument()
    expect(screen.getByText('23 completed jobs · KSh 2,500/hr')).toBeInTheDocument()
    expect(screen.getByText('✓ Verified')).toBeInTheDocument()
    expect(screen.getByText('Available')).toBeInTheDocument()
    expect(screen.getByText('2 providers found')).toBeInTheDocument()

    // Provider without reviews renders an honest "New" state, not a fake rating.
    expect(screen.getByText('Sparky Electrical')).toBeInTheDocument()
    expect(screen.getByText('New')).toBeInTheDocument()
    expect(screen.getByText('(0 reviews)')).toBeInTheDocument()
    expect(screen.getByText('0 completed jobs · —/hr')).toBeInTheDocument()
    expect(screen.getByText('Unavailable')).toBeInTheDocument()
  })

  it('applies search text, city, specialty, sort and availability filters', async () => {
    render(<Marketplace />)
    await screen.findByText('Njoroge Plumbing Ltd')

    fireEvent.change(screen.getByLabelText('Search providers'), { target: { value: ' pipe ' } })
    fireEvent.change(screen.getByLabelText('Filter by city'), { target: { value: 'Nairobi' } })
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))

    await waitFor(() =>
      expect(getMarketplaceProviders).toHaveBeenLastCalledWith(
        expect.objectContaining({ q: 'pipe', city: 'Nairobi', page: 1 }),
      ),
    )

    fireEvent.change(screen.getByLabelText('Filter by specialty'), { target: { value: 'Plumbing' } })
    await waitFor(() =>
      expect(getMarketplaceProviders).toHaveBeenLastCalledWith(
        expect.objectContaining({ category: 'Plumbing', page: 1 }),
      ),
    )

    fireEvent.change(screen.getByLabelText('Sort providers'), { target: { value: 'jobs' } })
    await waitFor(() =>
      expect(getMarketplaceProviders).toHaveBeenLastCalledWith(
        expect.objectContaining({ sort: 'jobs' }),
      ),
    )

    fireEvent.click(screen.getByLabelText('Available now'))
    await waitFor(() =>
      expect(getMarketplaceProviders).toHaveBeenLastCalledWith(
        expect.objectContaining({ available_only: true }),
      ),
    )
  })

  it('paginates directories larger than one page', async () => {
    vi.mocked(getMarketplaceProviders).mockResolvedValue({
      items: [provider()],
      total: 30,
      page: 1,
      page_size: 12,
    })

    render(<Marketplace />)
    await screen.findByText('Page 1 of 3')

    fireEvent.click(screen.getByRole('button', { name: 'Next →' }))

    await waitFor(() =>
      expect(getMarketplaceProviders).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 2 }),
      ),
    )
  })

  it('opens the reviews modal and lists masked reviewer feedback', async () => {
    render(<Marketplace />)
    await screen.findByText('Njoroge Plumbing Ltd')

    fireEvent.click(screen.getAllByRole('button', { name: 'View reviews' })[0])

    await waitFor(() => expect(getProviderReviews).toHaveBeenCalledWith(1, 1, 10))
    expect(await screen.findByText('Mary W.')).toBeInTheDocument()
    expect(screen.getByText('Fixed a persistent leak quickly.')).toBeInTheDocument()
    expect(screen.getByText(/Plumbing leak repair/)).toBeInTheDocument()
  })

  it('shows an empty state when no providers match', async () => {
    vi.mocked(getMarketplaceProviders).mockResolvedValue(providerPage([]))

    render(<Marketplace />)

    expect(await screen.findByText('No providers match these filters yet.')).toBeInTheDocument()
    expect(screen.getByText('0 providers found')).toBeInTheDocument()
  })

  it('uses the admin-specific heading for admin users', async () => {
    vi.mocked(useAuth).mockReturnValue({ user: { id: 1, role: 'admin' } } as any)

    render(<Marketplace />)

    expect(await screen.findByText('Platform marketplace')).toBeInTheDocument()
  })

  it('surfaces load failures to the user', async () => {
    vi.mocked(getMarketplaceProviders).mockRejectedValue(new Error('marketplace down'))

    render(<Marketplace />)

    expect(await screen.findByText('marketplace down')).toBeInTheDocument()
  })
})
