import { PropertyMatchCriteria } from '../types'
import { LOCATION_SUGGESTIONS } from '../data/kenyaLocations'

// Deterministic spoken-brief parser: transcribed text in, structured match
// criteria out. Deliberately rule-based (like the backend matching engine) so
// every extracted field can be shown back to the user as a chip.

export interface VoiceQueryParseResult {
  criteria: PropertyMatchCriteria
  /** Human-readable summary chips for everything that was understood. */
  understood: string[]
  /** The transcript exactly as received (trimmed). */
  heard: string
}

const NUMBER_WORDS: Record<string, number> = {
  one: 1, two: 2, three: 3, four: 4, five: 5,
  six: 6, seven: 7, eight: 8, nine: 9, ten: 10,
}

const AMOUNT_WORD_OR_DIGITS =
  '(?:\\d[\\d,]*(?:\\.\\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|a|an)'
const MAGNITUDE_SUFFIX = '(thousand|million|grand|mn|k|m)'

const BUDGET_CUE = new RegExp(
  `\\b(?:under|below|less than|not more than|max(?:imum)?|up to|budget(?: of)?)\\s+(?:ksh|kes|shillings?)?\\s*(${AMOUNT_WORD_OR_DIGITS})\\s*${MAGNITUDE_SUFFIX}?\\b`,
)
const CURRENCY_AMOUNT = new RegExp(
  `\\b(?:ksh|kes)\\s*(${AMOUNT_WORD_OR_DIGITS})\\s*${MAGNITUDE_SUFFIX}?\\b`,
)
const SHILLINGS_AMOUNT = /(\d[\d,]*(?:\.\d+)?)\s*(?:shillings?|bob)\b/
const BARE_MAGNITUDE = new RegExp(`\\b(${AMOUNT_WORD_OR_DIGITS})\\s*${MAGNITUDE_SUFFIX}\\b`)

const BEDROOM_DIGITS = /\b(\d{1,2})\s*\+?\s*[- ]?\s*(?:bed(?:room)?s?|bdrms?|br)\b/
const BEDROOM_WORDS =
  /\b(one|two|three|four|five|six|seven|eight|nine|ten)\s*[- ]?\s*(?:bed(?:room)?s?|bdrms?|br)\b/

const RENT_CUE = /\b(rent(?:ing|al|s)?|to let|to lease|for lease|tenants?|per month|monthly|a month)\b/
const SALE_CUE = /\b(buy(?:ing)?|purchase|for sale|sale|invest(?:ing|ment)?|ownership)\b/

const COMMERCIAL_TYPE = /\b(commercial|offices?|shops?|retail|warehouses?|godowns?|business)\b/
const HOUSE_TYPE = /\b(houses?|homes?|villas?|bungalows?|town ?houses?|maisonettes?|duplex(?:es)?|mansions?)\b/
const APARTMENT_TYPE = /\b(apartments?|flats?|studios?|bedsitters?|penthouses?|lofts?)\b/
const STUDIO = /\b(studios?|bedsitters?)\b/

const UNFURNISHED = /\b(unfurnished|not furnished|bare shell)\b/
const FURNISHED = /\bfurnished\b/

const PARKING = /\b(parking|car ?park|garage|parking (?:space|lot|bays?))\b/
const SECURITY = /\b(security|cctv|gated|guards?|guarded|alarms?)\b/
const BALCONY = /\b(balcon(?:y|ies)|terraces?)\b/
const POOL = /\b(?:swimming )?pools?\b/
const GYM = /\b(gym|fitness (?:centre|center|studio))\b/

const LOCALITY_ALIASES: Record<string, string> = { cbd: 'CBD' }

const escapeRegExp = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

const LOCALITY_PATTERNS = [
  ...Object.entries(LOCALITY_ALIASES).map(([alias, canonical]) => ({ name: canonical, re: new RegExp(`\\b${escapeRegExp(alias)}\\b`) })),
  ...[...new Set(LOCATION_SUGGESTIONS)]
    .sort((a, b) => b.length - a.length)
    .map((name) => ({ name, re: new RegExp(`\\b${escapeRegExp(name.toLowerCase())}\\b`) })),
]

const LOCATION_STOP_WORDS =
  /\b(?:with|under|below|over|above|max(?:imum)?|up to|budget|for|that|which|per|monthly|and|plus|having|must|should|please|around)\b/
const LEADING_ARTICLES = /^(?:a|an|the|my|our|this|that|some|any)\s+/
// Phrases like "in a commercial property" must not become a city.
const GENERIC_LOCATION_TOKENS = new Set([
  'property', 'properties', 'place', 'area', 'somewhere', 'anywhere',
  'house', 'home', 'apartment', 'flat', 'office', 'space', 'bedroom', 'bedrooms',
])

function parseAmount(raw: string, suffix?: string): number | null {
  const cleaned = raw.replace(/,/g, '')
  const base = /^\d/.test(cleaned) ? Number.parseFloat(cleaned) : NUMBER_WORDS[cleaned]
  if (base === undefined || Number.isNaN(base)) return null
  if (!suffix) return base
  const factor = suffix === 'million' || suffix === 'mn' || suffix === 'm' ? 1_000_000 : 1_000
  return Math.round(base * factor)
}

function findBudget(text: string): number | null {
  const cue = BUDGET_CUE.exec(text)
  if (cue) {
    const value = parseAmount(cue[1], cue[2])
    if (value !== null) return value
  }
  const currency = CURRENCY_AMOUNT.exec(text)
  if (currency) {
    const value = parseAmount(currency[1], currency[2])
    if (value !== null) return value
  }
  const shillings = SHILLINGS_AMOUNT.exec(text)
  if (shillings) {
    const value = parseAmount(shillings[1])
    if (value !== null) return value
  }
  const bare = BARE_MAGNITUDE.exec(text)
  if (bare) {
    const value = parseAmount(bare[1], bare[2])
    if (value !== null) return value
  }
  return null
}

function findLocality(text: string): string | null {
  let best: { name: string; index: number } | null = null
  for (const { name, re } of LOCALITY_PATTERNS) {
    const match = re.exec(text)
    if (!match) continue
    if (best === null || match.index < best.index || (match.index === best.index && name.length > best.name.length)) {
      best = { name, index: match.index }
    }
  }
  return best?.name ?? null
}

function findFallbackLocality(text: string): string | null {
  const match = /\b(?:in|near|around|at)\s+([a-z][a-z\s'-]{1,40})/.exec(text)
  if (!match) return null
  const phrase = match[1]
    .split(LOCATION_STOP_WORDS)[0]
    .replace(/[.,!?].*$/, '')
    .trim()
    .replace(LEADING_ARTICLES, '')
  const tokens = phrase.split(/\s+/).filter(Boolean).slice(0, 3)
  if (!tokens.length) return null
  if (tokens.some((token) => GENERIC_LOCATION_TOKENS.has(token))) return null
  return tokens.map((token) => token[0].toUpperCase() + token.slice(1)).join(' ')
}

export function parseVoiceQuery(transcript: string): VoiceQueryParseResult {
  const heard = transcript.trim()
  const text = heard.toLowerCase().replace(/[’']/g, "'")
  const criteria: PropertyMatchCriteria = {}
  const understood: string[] = []

  const purpose = RENT_CUE.test(text) ? 'rent' : SALE_CUE.test(text) ? 'sale' : undefined
  if (purpose) {
    criteria.purpose = purpose
    understood.push(purpose === 'rent' ? 'Rent' : 'Buy')
  }

  const budget = findBudget(text)
  if (budget !== null) {
    criteria.max_budget = budget
    understood.push(`Up to KSh ${budget.toLocaleString('en-US')}`)
  }

  const locality = findLocality(text) ?? findFallbackLocality(text)
  if (locality) {
    criteria.preferred_city = locality
    understood.push(locality)
  }

  const isStudio = STUDIO.test(text)
  const bedroomDigits = BEDROOM_DIGITS.exec(text)
  const bedroomWords = BEDROOM_WORDS.exec(text)
  const bedrooms = isStudio
    ? 1
    : bedroomWords
      ? NUMBER_WORDS[bedroomWords[1]]
      : bedroomDigits
        ? Number.parseInt(bedroomDigits[1], 10)
        : null
  if (bedrooms !== null) {
    criteria.min_bedrooms = bedrooms
    understood.push(isStudio ? 'Studio' : `${bedrooms}+ bedrooms`)
  }

  const propertyType = COMMERCIAL_TYPE.test(text)
    ? 'commercial'
    : HOUSE_TYPE.test(text)
      ? 'house'
      : APARTMENT_TYPE.test(text)
        ? 'apartment'
        : undefined
  if (propertyType) {
    criteria.property_type = propertyType
    understood.push(
      propertyType === 'commercial' ? 'Commercial' : propertyType === 'house' ? 'House' : 'Apartment',
    )
  }

  const furnishing = UNFURNISHED.test(text) ? 'unfurnished' : FURNISHED.test(text) ? 'furnished' : undefined
  if (furnishing) {
    criteria.furnishing = furnishing
    understood.push(furnishing === 'unfurnished' ? 'Unfurnished' : 'Furnished')
  }

  if (PARKING.test(text)) {
    criteria.require_parking = true
    understood.push('Parking')
  }
  if (SECURITY.test(text)) {
    criteria.require_security = true
    understood.push('Security')
  }
  if (BALCONY.test(text)) {
    criteria.require_balcony = true
    understood.push('Balcony')
  }

  const amenities: string[] = []
  if (POOL.test(text)) {
    amenities.push('Swimming Pool')
    understood.push('Swimming pool')
  }
  if (GYM.test(text)) {
    amenities.push('Gym')
    understood.push('Gym')
  }
  if (amenities.length) criteria.amenities = amenities

  return { criteria, understood, heard }
}
