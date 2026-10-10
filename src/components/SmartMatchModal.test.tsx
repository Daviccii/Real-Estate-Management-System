import React from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import SmartMatchModal from './SmartMatchModal'
import { matchProperties } from '../services/property'
import type { Property } from '../types'
import {
  FakeRecognition,
  finalSpeechResult,
  installFakeSpeechRecognition,
  removeFakeSpeechRecognition,
} from '../test/speechRecognitionFake'

vi.mock('../services/property', () => ({
  matchProperties: vi.fn(),
}))

const property = (overrides: Partial<Property> = {}) =>
  ({
    id: 12,
    name: 'Riverside Apartments',
    property_type: 'Apartment',
    purpose: 'rent',
    status: 'active',
    price: 90000,
    bedrooms: 2,
    bathrooms: 1,
    address: 'Riverside Drive',
    city: 'Nairobi',
    country: 'Kenya',
    ...overrides,
  }) as Property

const renderModal = (isOpen = true) =>
  render(
    <MemoryRouter>
      <SmartMatchModal isOpen={isOpen} onClose={vi.fn()} />
    </MemoryRouter>,
  )

const submit = () =>
  fireEvent.click(screen.getByRole('button', { name: /calculate best matches/i }))

describe('SmartMatchModal', () => {
  it('renders nothing while closed', () => {
    const { container } = renderModal(false)
    expect(container).toBeEmptyDOMElement()
  })

  it('submits the criteria in the API snake_case shape', async () => {
    vi.mocked(matchProperties).mockResolvedValue([])
    renderModal()

    submit()

    await waitFor(() => expect(matchProperties).toHaveBeenCalledTimes(1))
    expect(matchProperties).toHaveBeenCalledWith(
      expect.objectContaining({
        purpose: 'rent',
        max_budget: 120000,
        preferred_city: 'Nairobi',
        min_bedrooms: 2,
        property_type: 'apartment',
        require_parking: true,
        require_security: true,
        require_balcony: false,
      }),
    )
  })

  it('shows score, label, top factors and reasons for each result', async () => {
    vi.mocked(matchProperties).mockResolvedValue([
      {
        property: property(),
        match_score: 92,
        match_label: 'Excellent match',
        match_reasons: ['Within your budget (KSh 90,000)', 'Located in Nairobi'],
        score_breakdown: { Budget: 25, Location: 20, Size: 15, Type: 10, Quality: 6 },
      },
    ])
    renderModal()

    submit()

    expect(await screen.findByText('92% Match')).toBeInTheDocument()
    expect(screen.getByText('Excellent match')).toBeInTheDocument()
    expect(screen.getByText('Budget +25')).toBeInTheDocument()
    expect(screen.getByText('Location +20')).toBeInTheDocument()
    expect(screen.getByText('Size +15')).toBeInTheDocument()
    expect(screen.getByText('Type +10')).toBeInTheDocument()
    // Only the top four factors are shown
    expect(screen.queryByText('Quality +6')).not.toBeInTheDocument()
    expect(screen.getByText(/Within your budget/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /view listing/i })).toHaveAttribute(
      'href',
      '/properties/12',
    )
  })

  it('shows the empty state when nothing matches', async () => {
    vi.mocked(matchProperties).mockResolvedValue([])
    renderModal()

    submit()

    expect(await screen.findByText(/no active properties matched/i)).toBeInTheDocument()
  })

  it('surfaces API failures via an alert', async () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    vi.mocked(matchProperties).mockRejectedValue(new Error('boom'))
    renderModal()

    submit()

    await waitFor(() => expect(alertSpy).toHaveBeenCalledWith('boom'))
  })
})

describe('SmartMatchModal voice assistant', () => {
  beforeEach(() => {
    FakeRecognition.instances = []
    installFakeSpeechRecognition()
  })

  afterEach(() => {
    removeFakeSpeechRecognition()
  })

  it('prefills the form from a spoken brief and forwards voice amenities', async () => {
    vi.mocked(matchProperties).mockResolvedValue([])
    renderModal()

    // Uncheck parking first so the transcript — not the default — re-enables it.
    fireEvent.click(screen.getByLabelText(/dedicated vehicle parking/i))
    expect(screen.getByLabelText(/dedicated vehicle parking/i)).not.toBeChecked()

    fireEvent.click(screen.getByRole('button', { name: /describe your ideal property by voice/i }))
    const recognition = FakeRecognition.instances[0]

    act(() => {
      recognition.onresult?.(
        finalSpeechResult(
          'Three bedroom apartment in Kilimani under 80k per month with parking and a swimming pool and gym',
        ),
      )
    })

    expect(screen.getByText('Heard:')).toBeInTheDocument()
    expect(screen.getByText('Kilimani')).toBeInTheDocument()
    expect(screen.getByText('Up to KSh 80,000')).toBeInTheDocument()
    expect(screen.getByText('3+ bedrooms')).toBeInTheDocument()
    expect(screen.getByText('Swimming pool')).toBeInTheDocument()
    expect(screen.getByText('Gym')).toBeInTheDocument()

    expect((screen.getByLabelText(/maximum budget/i) as HTMLInputElement).value).toBe('80000')
    expect((screen.getByLabelText(/preferred city/i) as HTMLInputElement).value).toBe('Kilimani')
    expect((screen.getByLabelText(/minimum bedrooms/i) as HTMLSelectElement).value).toBe('3')
    expect(screen.getByLabelText(/dedicated vehicle parking/i)).toBeChecked()

    submit()

    await waitFor(() => expect(matchProperties).toHaveBeenCalledTimes(1))
    expect(matchProperties).toHaveBeenCalledWith(
      expect.objectContaining({
        purpose: 'rent',
        max_budget: 80000,
        preferred_city: 'Kilimani',
        min_bedrooms: 3,
        property_type: 'apartment',
        require_parking: true,
        amenities: ['Swimming Pool', 'Gym'],
      }),
    )
  })

  it('surfaces microphone errors in the assistant panel', () => {
    renderModal()

    fireEvent.click(screen.getByRole('button', { name: /describe your ideal property by voice/i }))
    act(() => {
      FakeRecognition.instances[0].onerror?.({ error: 'not-allowed' })
    })

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Microphone access was blocked. Allow microphone permission and try again.',
    )
  })

  it('hides the voice button when speech recognition is unsupported', () => {
    removeFakeSpeechRecognition()
    renderModal()

    expect(
      screen.queryByRole('button', { name: /describe your ideal property by voice/i }),
    ).not.toBeInTheDocument()
  })
})
