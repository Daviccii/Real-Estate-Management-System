import React from 'react'
import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'

import VirtualTourViewer from './VirtualTourViewer'
import type { PropertyTour } from '../types'

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

describe('VirtualTourViewer', () => {
  it('renders nothing while closed', () => {
    const { container } = render(
      <VirtualTourViewer tours={[tour()]} isOpen={false} onClose={vi.fn()} />,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing when there are no tours', () => {
    const { container } = render(<VirtualTourViewer tours={[]} isOpen onClose={vi.fn()} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('embeds provider tours in a sandboxed https iframe', () => {
    render(<VirtualTourViewer tours={[tour()]} isOpen onClose={vi.fn()} />)
    const iframe = screen.getByTitle('Living room 360') as HTMLIFrameElement
    expect(iframe.tagName).toBe('IFRAME')
    expect(iframe.getAttribute('src')).toBe('https://my.matterport.com/show/?m=SxQL3iGyoDo')
    expect(iframe.getAttribute('sandbox')).toContain('allow-scripts')
    expect(iframe.getAttribute('sandbox')).toContain('allow-same-origin')
  })

  it('refuses a non-https embed_url and falls back to an external link', () => {
    render(
      <VirtualTourViewer
        tours={[tour({ embed_url: 'http://my.matterport.com/show/?m=SxQL3iGyoDo' })]}
        isOpen
        onClose={vi.fn()}
      />,
    )
    expect(screen.queryByTitle('Living room 360')).not.toBeInTheDocument()
    const link = screen.getByRole('link', { name: /open tour in new tab/i })
    expect(link).toHaveAttribute('href', 'https://my.matterport.com/show/?m=SxQL3iGyoDo')
  })

  it('shows the external-link panel for link-provider tours', () => {
    const external = tour({
      provider: 'link',
      embed_url: null,
      url: 'https://example.com/cloud-tour',
      title: 'Cloud tour',
    })
    render(<VirtualTourViewer tours={[external]} isOpen onClose={vi.fn()} />)
    expect(screen.queryByTitle('Cloud tour')).not.toBeInTheDocument()
    expect(screen.getByText(/opens in a new tab/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /open tour in new tab/i })).toHaveAttribute(
      'href',
      'https://example.com/cloud-tour',
    )
  })

  it('switches the active tour via the switcher chips', () => {
    const second = tour({
      id: 2,
      title: 'Kitchen 360',
      provider: 'kuula',
      url: 'https://kuula.co/share/7Zg6p',
      embed_url: 'https://kuula.co/share/7Zg6p',
    })
    render(<VirtualTourViewer tours={[tour(), second]} isOpen onClose={vi.fn()} />)
    expect(screen.getByTitle('Living room 360')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: 'Kitchen 360' }))
    expect(screen.getByTitle('Kitchen 360')).toHaveAttribute('src', 'https://kuula.co/share/7Zg6p')
  })

  it('closes on Escape and on the close button', () => {
    const onClose = vi.fn()
    render(<VirtualTourViewer tours={[tour()]} isOpen onClose={onClose} />)

    fireEvent.keyDown(window, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByRole('button', { name: /close tour viewer/i }))
    expect(onClose).toHaveBeenCalledTimes(2)
  })

  it('closes when the overlay is clicked but not when the dialog body is', () => {
    const onClose = vi.fn()
    render(<VirtualTourViewer tours={[tour()]} isOpen onClose={onClose} />)

    fireEvent.click(screen.getByRole('dialog'))
    expect(onClose).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByText('Living room 360'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
