import React, { useMemo } from 'react'

import { formatCompact, niceTicks } from './chartUtils'

export interface BarSegmentSpec {
  label: string
  color: string
}

export interface BarDatum {
  label: string
  values: number[]
}

interface BarChartProps {
  ariaLabel: string
  data: BarDatum[]
  segments: BarSegmentSpec[]
  stacked?: boolean
  height?: number
  formatValue?: (value: number) => string
  emptyLabel?: string
}

const VIEW_WIDTH = 640
const PAD_LEFT = 54
const PAD_RIGHT = 18
const PAD_TOP = 16
const PAD_BOTTOM = 30

const BarChart: React.FC<BarChartProps> = ({
  ariaLabel,
  data,
  segments,
  stacked = true,
  height = 240,
  formatValue = formatCompact,
  emptyLabel = 'No data for this period',
}) => {
  const model = useMemo(() => {
    let maxTotal = 0
    for (const datum of data) {
      const values = segments.map((_, index) => datum.values[index] || 0)
      const candidate = stacked ? values.reduce((sum, value) => sum + value, 0) : Math.max(0, ...values)
      maxTotal = Math.max(maxTotal, candidate)
    }
    const ticks = niceTicks(maxTotal, 4)
    const yMax = ticks[ticks.length - 1]
    const innerWidth = VIEW_WIDTH - PAD_LEFT - PAD_RIGHT
    const innerHeight = height - PAD_TOP - PAD_BOTTOM
    const count = data.length
    const stepX = count > 0 ? innerWidth / count : 0
    const yFor = (value: number) => PAD_TOP + ((yMax - value) / (yMax || 1)) * innerHeight
    return { maxTotal, ticks, innerWidth, innerHeight, stepX, yFor }
  }, [data, segments, stacked, height])

  const hasData = model.maxTotal > 0

  if (!hasData) {
    return <div className="chart-empty">{emptyLabel}</div>
  }

  const barWidth = Math.min(38, model.stepX * 0.6)

  return (
    <svg className="chart-svg" viewBox={`0 0 ${VIEW_WIDTH} ${height}`} role="img" aria-label={ariaLabel}>
      {model.ticks.map((tick) => {
        const y = model.yFor(tick)
        return (
          <g key={tick}>
            <line className="chart-grid-line" x1={PAD_LEFT} x2={VIEW_WIDTH - PAD_RIGHT} y1={y} y2={y} />
            <text className="chart-axis-label" x={PAD_LEFT - 8} y={y + 3} textAnchor="end">
              {formatValue(tick)}
            </text>
          </g>
        )
      })}

      {data.map((datum, datumIndex) => {
        const values = segments.map((_, index) => datum.values[index] || 0)
        const centerX = PAD_LEFT + datumIndex * model.stepX + model.stepX / 2
        const titleLines = [
          datum.label,
          ...segments.map((segment, index) => `${segment.label}: ${formatValue(values[index])}`),
        ]
        if (stacked) {
          let running = 0
          return (
            <g key={datum.label} className="chart-bar-group">
              <title>{titleLines.join('\n')}</title>
              {segments.map((segment, index) => {
                const value = values[index]
                const yTop = model.yFor(running + value)
                const yBottom = model.yFor(running)
                running += value
                if (value <= 0) return null
                return (
                  <rect
                    key={segment.label}
                    className="chart-bar-seg"
                    x={centerX - barWidth / 2}
                    y={yTop}
                    width={barWidth}
                    height={Math.max(1, yBottom - yTop)}
                    rx={3}
                    fill={segment.color}
                  />
                )
              })}
            </g>
          )
        }
        const groupWidth = Math.min(52, model.stepX * 0.66)
        const segWidth = groupWidth / segments.length
        return (
          <g key={datum.label} className="chart-bar-group">
            <title>{titleLines.join('\n')}</title>
            {segments.map((segment, index) => {
              const value = values[index]
              const yTop = model.yFor(value)
              const yBottom = model.yFor(0)
              if (value <= 0) return null
              return (
                <rect
                  key={segment.label}
                  className="chart-bar-seg"
                  x={centerX - groupWidth / 2 + index * segWidth + 1}
                  y={yTop}
                  width={Math.max(1, segWidth - 2)}
                  height={Math.max(1, yBottom - yTop)}
                  rx={3}
                  fill={segment.color}
                />
              )
            })}
          </g>
        )
      })}

      {data.map((datum, datumIndex) => (
        <text
          key={`label-${datum.label}`}
          className="chart-axis-label"
          x={PAD_LEFT + datumIndex * model.stepX + model.stepX / 2}
          y={height - 10}
          textAnchor="middle"
        >
          {datum.label}
        </text>
      ))}
    </svg>
  )
}

export default BarChart
