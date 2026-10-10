import React from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import TourEditor from './TourEditor'
import { propertyService } from '../services/property'
import type { PropertyTour } from '../types'

const { addToast } = vi.hoisted(() => ({ addToast: vi.fn() }))

vi.mock('../components/ToastProvider', () => ({
  useToast: () => ({ addToast, removeToast: vi.fn() }),
}))

vi.mock('../services/property', () => ({
  propertyService: {
    listTours: vi.fn(),
    addTour: vi.fn(),
    updateTour: vi.fn(),
    removeTour: vi.fn(),
  },
}))

const tour = (overrides: Partial<PropertyTour> = {}): PropertyTour => ({
  id: 1,
  property_id: 12,
  title: 'Living room 360',
  url: 'https://my.matterport.com/show/?m=SxQL3iGyoDo',
  provider: 'matterport',
  embed_url: 'https://my.matterport.com/show/?m=SxQL3iGyoDo',
  thumbnail_url: null,
  sort_order: 0,
  ...overrides,
})

describe('TourEditor', () => {
  beforeEach(() => {
    vi.mocked(propertyService.listTours).mockResolvedValue([])
    vi.mocked(propertyService.addTour).mockReset()
    vi.mocked(propertyService.updateTour).mockReset()
    vi.mocked(propertyService.removeTour).mockReset()
    addToast.mockClear()
  })

  it('loads the property tours and shows the empty state', async () => {
    render(<TourEditor propertyId={12} />)
    expect(await screen.findByText(/no tours yet/i)).toBeInTheDocument()
    expect(propertyService.listTours).toHaveBeenCalledWith(12)
  })

  it('lists existing tours with provider badges', async () => {
    vi.mocked(propertyService.listTours).mockResolvedValue([
      tour(),
      tour({ id: 2, title: 'Cloud tour', provider: 'link', embed_url: null, url: 'https://example.com/t' }),
    ])
    render(<TourEditor propertyId={12} />)

    expect(await screen.findByText('Living room 360')).toBeInTheDocument()
    expect(screen.getByText(/matterport 3d · embedded/i)).toBeInTheDocument()
    expect(screen.getByText(/external link · external/i)).toBeInTheDocument()
  })

  it('rejects non-https links client-side without calling the API', async () => {
    render(<TourEditor propertyId={12} />)
    await screen.findByText(/no tours yet/i)

    fireEvent.change(screen.getByLabelText(/tour share link/i), {
      target: { value: 'http://example.com/tour' },
    })
    fireEvent.click(screen.getByRole('button', { name: /add tour/i }))

    expect(propertyService.addTour).not.toHaveBeenCalled()
    expect(addToast).toHaveBeenCalledWith(expect.objectContaining({ type: 'error' }))
  })

  it('adds a tour and appends it to the list', async () => {
    vi.mocked(propertyService.addTour).mockResolvedValue(
      tour({ id: 3, title: 'Rooftop', provider: 'kuula', url: 'https://kuula.co/share/7Zg6p', embed_url: 'https://kuula.co/share/7Zg6p' }),
    )
    render(<TourEditor propertyId={12} />)
    await screen.findByText(/no tours yet/i)

    fireEvent.change(screen.getByLabelText(/tour share link/i), {
      target: { value: 'https://kuula.co/share/7Zg6p' },
    })
    fireEvent.change(screen.getByLabelText(/title \(optional\)/i), { target: { value: 'Rooftop' } })
    fireEvent.click(screen.getByRole('button', { name: /add tour/i }))

    await waitFor(() =>
      expect(propertyService.addTour).toHaveBeenCalledWith(12, {
        url: 'https://kuula.co/share/7Zg6p',
        title: 'Rooftop',
        thumbnail_url: undefined,
      }),
    )
    expect(await screen.findByText('Rooftop')).toBeInTheDocument()
    expect(addToast).toHaveBeenCalledWith(expect.objectContaining({ type: 'success' }))
  })

  it('deletes a tour via two-step confirmation', async () => {
    vi.mocked(propertyService.listTours).mockResolvedValue([tour({ id: 5, title: 'Old tour' })])
    vi.mocked(propertyService.removeTour).mockResolvedValue(true)
    render(<TourEditor propertyId={12} />)
    await screen.findByText('Old tour')

    fireEvent.click(screen.getByRole('button', { name: /^delete$/i }))
    expect(propertyService.removeTour).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: /confirm delete\?/i }))
    await waitFor(() => expect(propertyService.removeTour).toHaveBeenCalledWith(12, 5))
    expect(screen.queryByText('Old tour')).not.toBeInTheDocument()
  })

  it('surfaces load errors through a toast', async () => {
    vi.mocked(propertyService.listTours).mockRejectedValue(new Error('Network down'))
    render(<TourEditor propertyId={12} />)

    await waitFor(() =>
      expect(addToast).toHaveBeenCalledWith(expect.objectContaining({ message: 'Network down', type: 'error' })),
    )
  })
})
