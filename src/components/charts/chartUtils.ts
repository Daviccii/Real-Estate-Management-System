const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function trimDecimal(value: number): string {
  const rounded = Math.round(value * 10) / 10
  return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1)
}

/** 950 -> "950", 1200 -> "1.2K", 45000 -> "45K", 1500000 -> "1.5M", -1200 -> "-1.2K". */
export function formatCompact(value: number): string {
  if (!Number.isFinite(value)) return '0'
  const sign = value < 0 ? '-' : ''
  const abs = Math.abs(value)
  if (abs >= 1_000_000) return `${sign}${trimDecimal(abs / 1_000_000)}M`
  if (abs >= 1_000) return `${sign}${trimDecimal(abs / 1_000)}K`
  return `${sign}${trimDecimal(abs)}`
}

/** Ascending "nice" axis ticks covering [0, >=max]; [0, 1] when max <= 0. */
export function niceTicks(max: number, count = 4): number[] {
  if (!Number.isFinite(max) || max <= 0) return [0, 1]
  const rough = max / count
  const magnitude = 10 ** Math.floor(Math.log10(rough))
  const residual = rough / magnitude
  let step: number
  if (residual > 5) step = 10 * magnitude
  else if (residual > 2.5) step = 5 * magnitude
  else if (residual > 2) step = 2.5 * magnitude
  else if (residual > 1) step = 2 * magnitude
  else step = magnitude
  const niceMax = Math.ceil(max / step) * step
  const ticks: number[] = []
  for (let value = 0; value <= niceMax + step / 2; value += step) {
    ticks.push(Math.round(value * 1000) / 1000)
  }
  return ticks
}

/** "2026-10" -> "Oct" (or "Oct 2026" when long); falls back to the raw key. */
export function monthLabel(key: string, long = false): string {
  const [year, month] = key.split('-')
  const index = Number(month) - 1
  if (!year || !Number.isInteger(index) || index < 0 || index > 11) return key
  const name = MONTH_NAMES[index]
  return long ? `${name} ${year}` : name
}

export interface Point {
  x: number
  y: number
}

function round2(value: number): number {
  return Math.round(value * 100) / 100
}

export function linePath(points: Point[]): string {
  if (points.length === 0) return ''
  return points
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${round2(point.x)} ${round2(point.y)}`)
    .join(' ')
}

export function areaPath(points: Point[], baseY: number): string {
  if (points.length === 0) return ''
  const first = points[0]
  const last = points[points.length - 1]
  return `${linePath(points)} L ${round2(last.x)} ${round2(baseY)} L ${round2(first.x)} ${round2(baseY)} Z`
}

export interface DonutSegment {
  value: number
  fraction: number
  path: string
}

function polarToXY(cx: number, cy: number, radius: number, theta: number): Point {
  return { x: cx + radius * Math.sin(theta), y: cy - radius * Math.cos(theta) }
}

function ringPath(cx: number, cy: number, outer: number, inner: number): string {
  // A single arc with start == end renders nothing, so a full ring is two
  // half arcs for the outer edge and two for the inner edge.
  const top = `${round2(cx)} ${round2(cy - outer)}`
  const bottom = `${round2(cx)} ${round2(cy + outer)}`
  const innerTop = `${round2(cx)} ${round2(cy - inner)}`
  const innerBottom = `${round2(cx)} ${round2(cy + inner)}`
  return (
    `M ${top} A ${outer} ${outer} 0 1 1 ${bottom} A ${outer} ${outer} 0 1 1 ${top} ` +
    `L ${innerTop} A ${inner} ${inner} 0 1 0 ${innerBottom} A ${inner} ${inner} 0 1 0 ${innerTop} Z`
  )
}

/** Ring segments (12 o'clock start, clockwise). Values <= 0 are skipped. */
export function donutSegments(
  values: number[],
  cx: number,
  cy: number,
  outerRadius: number,
  innerRadius: number,
): DonutSegment[] {
  const total = values.reduce((sum, value) => sum + (value > 0 ? value : 0), 0)
  if (total <= 0) return []
  const segments: DonutSegment[] = []
  let cumulative = 0
  for (const value of values) {
    if (value <= 0) continue
    const fraction = value / total
    const start = cumulative * Math.PI * 2
    cumulative += fraction
    const end = cumulative * Math.PI * 2
    if (fraction >= 0.9999) {
      segments.push({ value, fraction, path: ringPath(cx, cy, outerRadius, innerRadius) })
      continue
    }
    const startOuter = polarToXY(cx, cy, outerRadius, start)
    const endOuter = polarToXY(cx, cy, outerRadius, end)
    const startInner = polarToXY(cx, cy, innerRadius, end)
    const endInner = polarToXY(cx, cy, innerRadius, start)
    const largeArc = end - start > Math.PI ? 1 : 0
    segments.push({
      value,
      fraction,
      path:
        `M ${round2(startOuter.x)} ${round2(startOuter.y)} ` +
        `A ${outerRadius} ${outerRadius} 0 ${largeArc} 1 ${round2(endOuter.x)} ${round2(endOuter.y)} ` +
        `L ${round2(startInner.x)} ${round2(startInner.y)} ` +
        `A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${round2(endInner.x)} ${round2(endInner.y)} Z`,
    })
  }
  return segments
}

/** Nearest series index for an svg-space x coordinate; -1 when there is no data. */
export function clampIndex(svgX: number, padLeft: number, stepX: number, count: number): number {
  if (count <= 0) return -1
  if (count === 1 || stepX <= 0) return 0
  const index = Math.round((svgX - padLeft) / stepX)
  return Math.min(Math.max(index, 0), count - 1)
}
