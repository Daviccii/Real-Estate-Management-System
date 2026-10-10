import React, { useMemo, useState } from 'react'

import { clampIndex, formatCompact, linePath, monthLabel, niceTicks } from './chartUtils'
import type { Point } from './chartUtils'

export interface LineSeriesSpec {
  key: string
  label: string
  color: string
}

interface LineChartProps {
  ariaLabel: string
  data: Array<Record<string, number | string>>
  series: LineSeriesSpec[]
  height?: number
  formatValue?: (value: number) => string
  emptyLabel?: string
}

const VIEW_WIDTH = 640
const PAD_LEFT = 54
const PAD_RIGHT = 18
const PAD_TOP = 16
const PAD_BOTTOM = 30

const LineChart: React.FC<LineChartProps> = ({
  ariaLabel,
  data,
  series,
  height = 240,
  formatValue = formatCompact,
  emptyLabel = 'No data for this period',
}) => {
  const [activeIndex, setActiveIndex] = useState<number | null>(null)

  const model = useMemo(() => {
    const values: number[] = []
    for (const row of data) {
      for (const spec of series) values.push(Number(row[spec.key]) || 0)
    }
    const dataMax = values.length ? Math.max(0, ...values) : 0
    const dataMin = values.length ? Math.min(0, ...values) : 0
    let ticks = niceTicks(dataMax, 3)
    if (dataMin < 0) {
      const negative = niceTicks(-dataMin, 2)
        .map((tick) => -tick)
        .filter((tick) => tick < 0)
        .reverse()
      ticks = [...negative, ...ticks]
    }
    const yMin = ticks[0]
    const yMax = ticks[ticks.length - 1]
    const innerWidth = VIEW_WIDTH - PAD_LEFT - PAD_RIGHT
    const innerHeight = height - PAD_TOP - PAD_BOTTOM
    const count = data.length
    const stepX = count > 1 ? innerWidth / (count - 1) : 0
    const xFor = (index: number) => PAD_LEFT + index * stepX
    const yFor = (value: number) => PAD_TOP + ((yMax - value) / (yMax - yMin || 1)) * innerHeight

    const seriesPaths = series.map((spec) => {
      const points: Point[] = data.map((row, index) => ({
        x: xFor(index),
        y: yFor(Number(row[spec.key]) || 0),
      }))
      return { spec, points, path: linePath(points) }
    })

    const labelStep = Math.max(1, Math.ceil(count / 8))
    return { ticks, yMin, yMax, innerWidth, innerHeight, stepX, xFor, yFor, seriesPaths, labelStep, count }
  }, [data, series, height])

  const hasData = data.length > 0 && model.seriesPaths.some((entry) => entry.points.some((p) => p.y !== model.yFor(0)))

  const handleMove = (event: React.MouseEvent<SVGRectElement>) => {
    const svg = event.currentTarget.ownerSVGElement
    if (!svg) return
    const rect = svg.getBoundingClientRect()
    if (rect.width === 0) return
    const svgX = ((event.clientX - rect.left) * VIEW_WIDTH) / rect.width
    setActiveIndex(clampIndex(svgX, PAD_LEFT, model.stepX, model.count))
  }

  const tooltip = useMemo(() => {
    if (activeIndex === null || activeIndex < 0 || activeIndex >= data.length) return null
    const row = data[activeIndex]
    const x = model.xFor(activeIndex)
    const lines = [
      monthLabel(String(row.month ?? ''), true),
      ...series.map((spec) => `${spec.label}: ${formatValue(Number(row[spec.key]) || 0)}`),
    ]
    const width = Math.min(230, Math.max(120, Math.max(...lines.map((line) => line.length)) * 6.4 + 20))
    const height = 16 + lines.length * 15
    const flip = x + width + 14 > VIEW_WIDTH - PAD_RIGHT
    const bx = flip ? x - width - 12 : x + 12
    const by = PAD_TOP + 4
    return { lines, x, bx, by, width, height }
  }, [activeIndex, data, series, model, formatValue])

  if (!hasData) {
    return <div className="chart-empty">{emptyLabel}</div>
  }

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

      {data.map((row, index) =>
        index % model.labelStep === 0 ? (
          <text
            key={`label-${index}`}
            className="chart-axis-label"
            x={model.xFor(index)}
            y={height - 10}
            textAnchor="middle"
          >
            {monthLabel(String(row.month ?? ''))}
          </text>
        ) : null,
      )}

      {model.seriesPaths.map((entry) => (
        <path
          key={entry.spec.key}
          d={entry.path}
          fill="none"
          stroke={entry.spec.color}
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      ))}

      {activeIndex !== null && activeIndex >= 0 && activeIndex < data.length && (
        <g>
          <line
            className="chart-crosshair"
            x1={model.xFor(activeIndex)}
            x2={model.xFor(activeIndex)}
            y1={PAD_TOP}
            y2={height - PAD_BOTTOM}
          />
          {model.seriesPaths.map((entry) => (
            <circle
              key={entry.spec.key}
              cx={entry.points[activeIndex].x}
              cy={entry.points[activeIndex].y}
              r={3.5}
              fill={entry.spec.color}
              stroke="var(--surface)"
              strokeWidth={1.5}
            />
          ))}
        </g>
      )}

      {tooltip && (
        <g>
          <rect
            className="chart-tooltip-box"
            x={tooltip.bx}
            y={tooltip.by}
            width={tooltip.width}
            height={tooltip.height}
            rx={10}
          />
          {tooltip.lines.map((line, index) => (
            <text
              key={line}
              className={index === 0 ? 'chart-tooltip-month' : 'chart-tooltip-row'}
              x={tooltip.bx + 10}
              y={tooltip.by + 16 + index * 15}
            >
              {line}
            </text>
          ))}
        </g>
      )}

      <rect
        x={PAD_LEFT}
        y={PAD_TOP}
        width={model.innerWidth}
        height={model.innerHeight}
        fill="transparent"
        onMouseMove={handleMove}
        onMouseLeave={() => setActiveIndex(null)}
        data-testid="line-chart-overlay"
      />
    </svg>
  )
}

export default LineChart
