import { describe, expect, it } from 'vitest'

import {
  areaPath,
  clampIndex,
  donutSegments,
  formatCompact,
  linePath,
  monthLabel,
  niceTicks,
} from './chartUtils'

describe('formatCompact', () => {
  it('leaves values below one thousand untouched', () => {
    expect(formatCompact(0)).toBe('0')
    expect(formatCompact(950)).toBe('950')
  })

  it('compacts thousands and millions', () => {
    expect(formatCompact(1200)).toBe('1.2K')
    expect(formatCompact(45000)).toBe('45K')
    expect(formatCompact(1500000)).toBe('1.5M')
  })

  it('keeps the sign for negative values', () => {
    expect(formatCompact(-1200)).toBe('-1.2K')
  })

  it('falls back to zero for non-finite input', () => {
    expect(formatCompact(Number.POSITIVE_INFINITY)).toBe('0')
    expect(formatCompact(Number.NaN)).toBe('0')
  })
})

describe('niceTicks', () => {
  it('returns a safe default when the max is not positive', () => {
    expect(niceTicks(0)).toEqual([0, 1])
    expect(niceTicks(-5)).toEqual([0, 1])
  })

  it('covers the max with rounded steps', () => {
    expect(niceTicks(100)).toEqual([0, 25, 50, 75, 100])
    expect(niceTicks(3, 3)).toEqual([0, 1, 2, 3])
  })

  it('never emits a last tick below the max', () => {
    const ticks = niceTicks(1234)
    expect(ticks[ticks.length - 1]).toBeGreaterThanOrEqual(1234)
  })
})

describe('monthLabel', () => {
  it('renders short and long month names', () => {
    expect(monthLabel('2026-10')).toBe('Oct')
    expect(monthLabel('2026-01', true)).toBe('Jan 2026')
  })

  it('falls back to the raw key when it cannot be parsed', () => {
    expect(monthLabel('nonsense')).toBe('nonsense')
    expect(monthLabel('2026-13')).toBe('2026-13')
  })
})

describe('linePath and areaPath', () => {
  it('returns an empty string without points', () => {
    expect(linePath([])).toBe('')
    expect(areaPath([], 0)).toBe('')
  })

  it('builds an SVG line path', () => {
    expect(linePath([{ x: 1, y: 2 }, { x: 3.456, y: 4.2 }])).toBe('M 1 2 L 3.46 4.2')
  })

  it('closes the area down to the base line', () => {
    expect(areaPath([{ x: 0, y: 1 }, { x: 10, y: 5 }], 20)).toBe('M 0 1 L 10 5 L 10 20 L 0 20 Z')
  })
})

describe('donutSegments', () => {
  it('returns nothing when there is no positive value', () => {
    expect(donutSegments([0, 0, -3], 100, 100, 50, 30)).toEqual([])
  })

  it('splits positive values into proportional arcs and skips the rest', () => {
    const segments = donutSegments([1, -2, 1], 100, 100, 50, 30)

    expect(segments).toHaveLength(2)
    expect(segments[0].fraction).toBeCloseTo(0.5)
    expect(segments[1].fraction).toBeCloseTo(0.5)
    expect(segments[0].path).toContain('A 50 50')
    expect(segments[0].path).toContain('A 30 30')
  })

  it('renders a single value as a full ring of four arcs', () => {
    const segments = donutSegments([5], 100, 100, 50, 30)

    expect(segments).toHaveLength(1)
    expect(segments[0].fraction).toBe(1)
    expect(segments[0].path.startsWith('M ')).toBe(true)
    expect(segments[0].path.match(/ A /g)).toHaveLength(4)
    expect(segments[0].path.endsWith(' Z')).toBe(true)
  })
})

describe('clampIndex', () => {
  it('returns -1 when there is no data', () => {
    expect(clampIndex(0, 54, 100, 0)).toBe(-1)
  })

  it('always points at the only point when the series has one item', () => {
    expect(clampIndex(0, 54, 0, 1)).toBe(0)
    expect(clampIndex(600, 54, 0, 1)).toBe(0)
  })

  it('rounds to the nearest index and clamps to the edges', () => {
    expect(clampIndex(338, 54, 284, 3)).toBe(1)
    expect(clampIndex(-500, 54, 100, 5)).toBe(0)
    expect(clampIndex(99999, 54, 100, 5)).toBe(4)
  })
})
