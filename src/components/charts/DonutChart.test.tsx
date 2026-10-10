import React from 'react'
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import DonutChart from './DonutChart'

const SLICES = [
  { label: 'Occupied', value: 6, color: 'var(--chart-1)' },
  { label: 'Vacant', value: 2, color: 'var(--chart-2)' },
]

describe('DonutChart', () => {
  it('shows the empty label when there is nothing to draw', () => {
    render(
      <DonutChart
        ariaLabel="Units by status"
        slices={[{ label: 'Vacant', value: 0, color: 'var(--chart-1)' }]}
      />,
    )

    expect(screen.getByText('No data for this period')).toBeInTheDocument()
  })

  it('draws one arc per positive slice with a legend and center label', () => {
    const { container } = render(
      <DonutChart
        ariaLabel="Units by status"
        slices={[...SLICES, { label: 'Blocked', value: 0, color: 'var(--chart-3)' }]}
        centerValue={8}
        centerLabel="units"
      />,
    )

    expect(screen.getByRole('img', { name: 'Units by status' })).toBeInTheDocument()
    expect(container.querySelectorAll('.chart-donut-seg')).toHaveLength(2)
    expect(screen.getByText('Occupied')).toBeInTheDocument()
    expect(screen.getByText('6')).toBeInTheDocument()
    expect(screen.queryByText('Blocked')).not.toBeInTheDocument()
    expect(screen.getByText('8')).toBeInTheDocument()
    expect(screen.getByText('units')).toBeInTheDocument()
  })

  it('renders a single positive slice as a full ring', () => {
    const { container } = render(
      <DonutChart
        ariaLabel="Units by status"
        slices={[{ label: 'Occupied', value: 5, color: 'var(--chart-1)' }]}
      />,
    )

    const path = container.querySelector('.chart-donut-seg')!
    const d = path.getAttribute('d') || ''
    expect(d.match(/ A /g)).toHaveLength(4)
    expect(path.querySelector('title')?.textContent).toBe('Occupied: 5')
  })

  it('titles each arc with its label and value', () => {
    const { container } = render(
      <DonutChart ariaLabel="Units by status" slices={SLICES} />,
    )

    const titles = Array.from(container.querySelectorAll('.chart-donut-seg title')).map(
      (node) => node.textContent,
    )
    expect(titles).toEqual(['Occupied: 6', 'Vacant: 2'])
  })
})
