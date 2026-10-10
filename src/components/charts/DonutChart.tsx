import React, { useMemo } from 'react'

import { donutSegments } from './chartUtils'

export interface DonutSlice {
  label: string
  value: number
  color: string
}

interface DonutChartProps {
  ariaLabel: string
  slices: DonutSlice[]
  centerValue?: string | number
  centerLabel?: string
  size?: number
  formatValue?: (value: number) => string
  emptyLabel?: string
}

const DonutChart: React.FC<DonutChartProps> = ({
  ariaLabel,
  slices,
  centerValue,
  centerLabel,
  size = 176,
  formatValue = (value) => value.toLocaleString(),
  emptyLabel = 'No data for this period',
}) => {
  const total = slices.reduce((sum, slice) => sum + (slice.value > 0 ? slice.value : 0), 0)

  const segments = useMemo(() => {
    const cx = size / 2
    const cy = size / 2
    const outer = size / 2 - 4
    const inner = outer * 0.62
    const paths = donutSegments(
      slices.map((slice) => slice.value),
      cx,
      cy,
      outer,
      inner,
    )
    let index = 0
    return slices
      .map((slice) => {
        if (slice.value <= 0) return null
        const segment = paths[index]
        index += 1
        return segment ? { slice, path: segment.path } : null
      })
      .filter((entry): entry is { slice: DonutSlice; path: string } => entry !== null)
  }, [slices, size])

  if (total <= 0) {
    return <div className="chart-empty">{emptyLabel}</div>
  }

  return (
    <div className="donut-chart" style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
      <svg
        className="chart-svg"
        viewBox={`0 0 ${size} ${size}`}
        role="img"
        aria-label={ariaLabel}
        style={{ width: size, height: size, flex: '0 0 auto' }}
      >
        {segments.map(({ slice, path }) => (
          <path key={slice.label} className="chart-donut-seg" d={path} fill={slice.color}>
            <title>{`${slice.label}: ${formatValue(slice.value)}`}</title>
          </path>
        ))}
        {centerValue !== undefined && (
          <text x={size / 2} y={size / 2 + 1} textAnchor="middle" fill="var(--ink)" fontSize={24} fontWeight={700}>
            {centerValue}
          </text>
        )}
        {centerLabel && (
          <text x={size / 2} y={size / 2 + 20} textAnchor="middle" fill="var(--muted)" fontSize={10}>
            {centerLabel}
          </text>
        )}
      </svg>
      <ul className="chart-legend" aria-label={`${ariaLabel} legend`}>
        {slices
          .filter((slice) => slice.value > 0)
          .map((slice) => (
            <li key={slice.label}>
              <span className="chart-legend-dot" style={{ background: slice.color }} aria-hidden="true" />
              <span>{slice.label}</span>
              <span className="chart-legend-value">{formatValue(slice.value)}</span>
            </li>
          ))}
      </ul>
    </div>
  )
}

export default DonutChart
