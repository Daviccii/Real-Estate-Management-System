export const PROPERTY_TYPES = [
  { label: 'Any type', value: '' },
  { label: 'Apartment', value: 'Apartment' },
  { label: 'Villa', value: 'Villa' },
  { label: 'Bungalow', value: 'Bungalow' },
  { label: 'Mansion', value: 'Mansion' },
  { label: 'Mixed Use', value: 'Mixed Use' },
  { label: 'Commercial', value: 'Commercial' },
  { label: 'Industrial', value: 'Industrial' },
  { label: 'Land', value: 'Land' },
]

export const BUDGETS = [
  { label: 'Any budget', value: '' },
  { label: 'Under KES 5M', value: 'under-5m' },
  { label: 'KES 5M - 15M', value: '5m-15m' },
  { label: 'KES 15M - 50M', value: '15m-50m' },
  { label: 'KES 50M+', value: '50m-plus' },
]

export const BEDROOMS = [
  { label: 'Any', value: '' },
  { label: 'Studio', value: '0' },
  { label: '1', value: '1' },
  { label: '2', value: '2' },
  { label: '3', value: '3' },
  { label: '4+', value: '4-plus' },
]

// Suggestions only (used as a <datalist>) — location is a free-text field
// everywhere else in the app (homepage hero search, match panel, explore-by-
// -location links), so the discovery page's filter matches that instead of
// locking users into a fixed dropdown.
export const CITY_SUGGESTIONS = [
  'Nairobi', 'Westlands', 'Kilimani', 'Kileleshwa', 'Lavington', 'Karen',
  'Parklands', 'Upper Hill', 'Nairobi CBD', 'Ruaka', 'Kiambu', 'Ruiru',
  'Syokimau', 'Mombasa', 'Kisumu', 'Nakuru',
]

/** Returns a rough numeric KES value for budget-bucket filtering, or null if unknown. */
export function budgetBucketBounds(value: string): { min: number; max: number } | null {
  switch (value) {
    case 'under-5m': return { min: 0, max: 5_000_000 }
    case '5m-15m': return { min: 5_000_000, max: 15_000_000 }
    case '15m-50m': return { min: 15_000_000, max: 50_000_000 }
    case '50m-plus': return { min: 50_000_000, max: Infinity }
    default: return null
  }
}

/** Best-effort numeric price extraction from a Property's price/price_label fields. */
export function extractPriceValue(price?: string | number | null, priceLabel?: string | null): number | null {
  if (typeof price === 'number' && Number.isFinite(price)) return price
  const source = typeof price === 'string' && price.trim() ? price : priceLabel
  if (!source) return null
  const match = source.replace(/,/g, '').match(/([\d.]+)\s*(m|k)?/i)
  if (!match) return null
  const num = parseFloat(match[1])
  if (Number.isNaN(num)) return null
  const suffix = match[2]?.toLowerCase()
  if (suffix === 'm') return num * 1_000_000
  if (suffix === 'k') return num * 1_000
  return num
}