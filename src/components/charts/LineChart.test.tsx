import React from 'react'
import { describe, expect, it } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'

import LineChart from './LineChart'

const SERIES = [{ key: 'income', label: 'Income', color: 'var(--chart-2)' }]

const rows = [
  { month: '2026-08', income: 1000 },
  { month: '2026-09', income: 2000 },
  { month: '2026-10', income: 3000 },
]

const stubRect = (element: Element, width: number) => {
  element.getBoundingClientRect = () =>
    ({
      left: 0,
      top: 0,
      width,
      height: 240,
      right: width,
      bottom: 240,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    }) as DOMRect
}

describe('LineChart', () => {
  it('shows the empty label when every value is zero', () => {
    render(
      <LineChart
        ariaLabel="Income trend"
        data={[{ month: '2026-08', income: 0 }]}
        series={SERIES}
      />,
    )

    expect(screen.getByText('No data for this period')).toBeInTheDocument()
  })

  it('honours a custom empty label', () => {
    render(
      <LineChart
        ariaLabel="Income trend"
        data={[]}
        series={SERIES}
        emptyLabel="Nothing to plot"
      />,
    )

    expect(screen.getByText('Nothing to plot')).toBeInTheDocument()
  })

  it('renders one path per series with month axis labels', () => {
    const { container } = render(
      <LineChart ariaLabel="Income trend" data={rows} series={SERIES} />,
    )

    expect(screen.getByRole('img', { name: 'Income trend' })).toBeInTheDocument()
    expect(container.querySelectorAll('svg path')).toHaveLength(1)
    expect(screen.getByText('Aug')).toBeInTheDocument()
    expect(screen.getByText('Sep')).toBeInTheDocument()
    expect(screen.getByText('Oct')).toBeInTheDocument()
  })

  it('shows a tooltip for the hovered month and clears it on leave', () => {
    render(<LineChart ariaLabel="Income trend" data={rows} series={SERIES} />)

    const overlay = screen.getByTestId('line-chart-overlay') as unknown as SVGRectElement
    stubRect(overlay.ownerSVGElement!, 640)

    fireEvent.mouseMove(overlay, { clientX: 338 })

    expect(screen.getByText('Sep 2026')).toBeInTheDocument()
    expect(screen.getByText('Income: 2K')).toBeInTheDocument()

    fireEvent.mouseLeave(overlay)

    expect(screen.queryByText('Income: 2K')).not.toBeInTheDocument()
  })

  it('ignores hover when the chart has no measurable width', () => {
    render(<LineChart ariaLabel="Income trend" data={rows} series={SERIES} />)

    const overlay = screen.getByTestId('line-chart-overlay') as unknown as SVGRectElement
    stubRect(overlay.ownerSVGElement!, 0)

    fireEvent.mouseMove(overlay, { clientX: 338 })

    expect(screen.queryByText('Sep 2026')).not.toBeInTheDocument()
  })
})
