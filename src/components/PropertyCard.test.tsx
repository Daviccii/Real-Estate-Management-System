import React from 'react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import PropertyCard from './PropertyCard'
import { useAuth } from '../contexts/AuthContext'
import { useFavorites } from '../contexts/FavoriteContext'
import type { Property, User } from '../types'

vi.mock('../contexts/AuthContext')
vi.mock('../contexts/FavoriteContext')

const viewer = { id: 5, role: 'agent', email: 'a@b.com', full_name: 'Agent' } as User

const property = (overrides: Partial<Property> = {}) =>
  ({
    id: 12,
    name: 'Riverside Apartments',
    property_type: 'Apartment',
    purpose: 'rent',
    status: 'active',
    price: 250000,
    bedrooms: 2,
    bathrooms: 1,
    area: '95 sqm',
    units_count: null,
    city: 'Nairobi',
    country: 'Kenya',
    sub_location: 'Kilimani',
    verification_status: 'VERIFIED',
    owner_id: 99,
    ...overrides,
  }) as Property

const renderCard = (p: Partial<Property>, props: Record<string, unknown> = {}) =>
  render(
    <MemoryRouter>
      <PropertyCard p={property(p)} {...(props as any)} />
    </MemoryRouter>,
  )

describe('PropertyCard', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({ user: viewer } as any)
    vi.mocked(useFavorites).mockReturnValue({
      isFavorite: () => false,
      addFavorite: vi.fn(),
      removeFavorite: vi.fn(),
    } as any)
  })

  it('formats the price and collapses the location into one line', () => {
    renderCard({})

    expect(screen.getByText('Riverside Apartments')).toBeInTheDocument()
    expect(screen.getByText(/Ksh 250,000/)).toBeInTheDocument()
    expect(screen.getByText('Kilimani, Nairobi, Kenya')).toBeInTheDocument()
    expect(screen.getByText('2 beds • 1 bath • 95 sqm')).toBeInTheDocument()
  })

  it('honours an explicit price_label over the numeric price', () => {
    renderCard({ price_label: 'KES 1,200 / month', price: undefined })

    expect(screen.getByText('KES 1,200 / month')).toBeInTheDocument()
  })

  it('hides bedroom/bathroom counts for non-residential types', () => {
    renderCard({ property_type: 'Industrial', bedrooms: 0, bathrooms: 0 })

    expect(screen.getByText('95 sqm')).toBeInTheDocument()
    expect(screen.queryByText(/bed/)).not.toBeInTheDocument()
    expect(screen.queryByText(/bath/)).not.toBeInTheDocument()
  })

  it('labels demo and pending listings differently from verified ones', () => {
    const { unmount } = renderCard({ is_demo: true })
    expect(screen.getByText('Demo listing')).toBeInTheDocument()
    unmount()

    renderCard({ verification_status: 'PENDING' })
    expect(screen.getByText('Verification pending')).toBeInTheDocument()
  })

  it('toggles the favourite through the context and the parent callback', async () => {
    const addFavorite = vi.fn()
    const onFavoriteToggle = vi.fn()
    vi.mocked(useFavorites).mockReturnValue({ isFavorite: () => false, addFavorite, removeFavorite: vi.fn() } as any)

    renderCard({}, { onFavoriteToggle })
    fireEvent.click(screen.getByRole('button', { name: /save/i }))

    await waitFor(() => expect(addFavorite).toHaveBeenCalledWith(12))
    expect(onFavoriteToggle).toHaveBeenCalled()
  })

  it('removes an already-saved property from favourites', () => {
    const removeFavorite = vi.fn()
    vi.mocked(useFavorites).mockReturnValue({ isFavorite: () => true, addFavorite: vi.fn(), removeFavorite } as any)

    renderCard({}, { onFavoriteToggle: vi.fn() })
    const button = screen.getByRole('button', { name: /saved/i })
    expect(button).toHaveAttribute('aria-pressed', 'true')
    fireEvent.click(button)

    expect(removeFavorite).toHaveBeenCalledWith(12)
  })

  it('does not offer saving to anonymous visitors', () => {
    vi.mocked(useAuth).mockReturnValue({ user: null } as any)
    renderCard({}, { onFavoriteToggle: vi.fn() })

    expect(screen.queryByRole('button', { name: /save/i })).not.toBeInTheDocument()
  })

  it('shows Manage to staff and to the listing owner only', () => {
    renderCard({ owner_id: 99 })
    expect(screen.getByRole('link', { name: /manage/i })).toBeInTheDocument()
  })

  it('hides Manage from a tenant who does not own the listing', () => {
    vi.mocked(useAuth).mockReturnValue({ user: { ...viewer, role: 'tenant' } as User } as any)
    renderCard({ owner_id: 99 })
    expect(screen.queryByRole('link', { name: /manage/i })).not.toBeInTheDocument()
  })

  it('lets a tenant manage their own listing', () => {
    vi.mocked(useAuth).mockReturnValue({ user: { ...viewer, role: 'tenant' } as User } as any)
    renderCard({ owner_id: 5 })
    expect(screen.getByRole('link', { name: /manage/i })).toBeInTheDocument()
  })
})
