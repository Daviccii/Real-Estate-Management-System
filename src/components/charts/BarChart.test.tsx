import React from 'react'
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import BarChart from './BarChart'

const SEGMENTS = [
  { label: 'Collected', color: 'var(--chart-2)' },
  { label: 'Outstanding', color: 'var(--chart-3)' },
]

describe('BarChart', () => {
  it('shows the empty label when every bar is zero', () => {
    render(
      <BarChart
        ariaLabel="Rent collection"
        data={[{ label: 'May', values: [0, 0] }]}
        segments={SEGMENTS}
      />,
    )

    expect(screen.getByText('No data for this period')).toBeInTheDocument()
  })

  it('stacks segments bottom-up with a titled tooltip per bar', () => {
    const { container } = render(
      <BarChart
        ariaLabel="Rent collection"
        data={[{ label: 'May', values: [10, 5] }]}
        segments={SEGMENTS}
      />,
    )

    const rects = container.querySelectorAll('.chart-bar-seg')
    expect(rects).toHaveLength(2)
    expect(Number(rects[1].getAttribute('y'))).toBeLessThan(Number(rects[0].getAttribute('y')))
    expect(container.querySelector('title')?.textContent).toBe(
      'May\nCollected: 10\nOutstanding: 5',
    )
    expect(screen.getByText('May')).toBeInTheDocument()
  })

  it('places grouped segments side by side', () => {
    const { container } = render(
      <BarChart
        ariaLabel="Maintenance inflow"
        data={[{ label: 'May', values: [10, 4] }]}
        segments={SEGMENTS}
        stacked={false}
      />,
    )

    const rects = container.querySelectorAll('.chart-bar-seg')
    expect(rects).toHaveLength(2)
    expect(rects[1].getAttribute('x')).not.toBe(rects[0].getAttribute('x'))
  })

  it('skips zero-valued segments', () => {
    const { container } = render(
      <BarChart
        ariaLabel="Rent collection"
        data={[{ label: 'May', values: [10, 0] }]}
        segments={SEGMENTS}
      />,
    )

    expect(container.querySelectorAll('.chart-bar-seg')).toHaveLength(1)
  })

  it('exposes the chart with its aria label', () => {
    render(
      <BarChart
        ariaLabel="Rent collection"
        data={[{ label: 'May', values: [10, 5] }]}
        segments={SEGMENTS}
      />,
    )

    expect(screen.getByRole('img', { name: 'Rent collection' })).toBeInTheDocument()
  })
})
