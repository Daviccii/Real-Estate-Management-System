import { Property } from '../types'

/**
 * Isolated, clearly-labelled content for the public homepage.
 *
 * PUBLIC_FEATURED_PROPERTIES_FALLBACK is a sample dataset only. It is used
 * when the live property API is unavailable or returns zero public
 * listings, so the homepage still demonstrates the product. Replace/remove
 * once the public listings endpoint is reliably seeded.
 *
 * Marketing copy (purpose copy, location notes, intelligence cards, steps) is
 * stored as translation keys; the strings live in src/i18n/translations.ts.
 */

export type PropertyPurpose = 'buy' | 'rent' | 'invest'

// Alias kept so page components can depend on a homepage-scoped name
// instead of importing the shared `Property` type directly everywhere.
export type PublicProperty = Property

type PurposeCopy = {
  titleKey: string
  subtitleKey: string
  helperKey: string
}

export const PUBLIC_PURPOSE_COPY: Record<PropertyPurpose, PurposeCopy> = {
  buy: {
    titleKey: 'home.purpose.buy.title',
    subtitleKey: 'home.purpose.buy.subtitle',
    helperKey: 'home.purpose.buy.helper',
  },
  rent: {
    titleKey: 'home.purpose.rent.title',
    subtitleKey: 'home.purpose.rent.subtitle',
    helperKey: 'home.purpose.rent.helper',
  },
  invest: {
    titleKey: 'home.purpose.invest.title',
    subtitleKey: 'home.purpose.invest.subtitle',
    helperKey: 'home.purpose.invest.helper',
  },
}

export const PUBLIC_HOME_LOCATIONS: { label: string; noteKey: string; to: string }[] = [
  { label: 'Nairobi', noteKey: 'home.locations.nairobi.note', to: '/properties?location=Nairobi' },
  { label: 'Mombasa', noteKey: 'home.locations.mombasa.note', to: '/properties?location=Mombasa' },
  { label: 'Kisumu', noteKey: 'home.locations.kisumu.note', to: '/properties?location=Kisumu' },
  { label: 'Nakuru', noteKey: 'home.locations.nakuru.note', to: '/properties?location=Nakuru' },
  { label: 'Kiambu', noteKey: 'home.locations.kiambu.note', to: '/properties?location=Kiambu' },
]

export const PUBLIC_HOME_INTELLIGENCE: { statusKey: string; titleKey: string; descriptionKey: string }[] = [
  {
    statusKey: 'home.intel.comingSoon',
    titleKey: 'home.intel.trends.title',
    descriptionKey: 'home.intel.trends.desc',
  },
  {
    statusKey: 'home.intel.comingSoon',
    titleKey: 'home.intel.values.title',
    descriptionKey: 'home.intel.values.desc',
  },
  {
    statusKey: 'home.intel.comingSoon',
    titleKey: 'home.intel.neighbourhood.title',
    descriptionKey: 'home.intel.neighbourhood.desc',
  },
  {
    statusKey: 'home.intel.comingSoon',
    titleKey: 'home.intel.opportunities.title',
    descriptionKey: 'home.intel.opportunities.desc',
  },
]

export const PUBLIC_HOME_STEPS: { step: string; titleKey: string; descriptionKey: string }[] = [
  { step: '01', titleKey: 'home.steps.discover.title', descriptionKey: 'home.steps.discover.desc' },
  { step: '02', titleKey: 'home.steps.understand.title', descriptionKey: 'home.steps.understand.desc' },
  { step: '03', titleKey: 'home.steps.compare.title', descriptionKey: 'home.steps.compare.desc' },
  { step: '04', titleKey: 'home.steps.act.title', descriptionKey: 'home.steps.act.desc' },
]

// Sample-only fallback. Shape matches the live `Property` type used by
// PropertyCard so it can be swapped for API data with no component changes.
export const PUBLIC_FEATURED_PROPERTIES_FALLBACK: Property[] = [
  {
    id: -1,
    name: 'Riverside Two-Bedroom Apartment',
    property_type: 'Residential',
    address: 'Riverside Drive',
    city: 'Nairobi',
    country: 'Kenya',
    status: 'active',
    units_count: 24,
    price: 12500000,
    image_url: 'https://images.unsplash.com/photo-1493809842364-78817add7ffb?q=80&w=1200&auto=format&fit=crop',
    bedrooms: 2,
    bathrooms: 2,
    area: '110 sqm',
  } as Property,
  {
    id: -2,
    name: 'Karen Family Villa',
    property_type: 'Villa',
    address: 'Karen',
    city: 'Nairobi',
    country: 'Kenya',
    status: 'active',
    units_count: 1,
    price: 48000000,
    image_url: 'https://images.unsplash.com/photo-1568605114967-8130f3a36994?q=80&w=1200&auto=format&fit=crop',
    bedrooms: 5,
    bathrooms: 4,
    area: '420 sqm',
  } as Property,
  {
    id: -3,
    name: 'Westlands Office Suite',
    property_type: 'Commercial',
    address: 'Waiyaki Way',
    city: 'Nairobi',
    country: 'Kenya',
    status: 'active',
    units_count: 6,
    price_label: 'KES 180,000 / month',
    image_url: 'https://images.unsplash.com/photo-1497366216548-37526070297c?q=80&w=1200&auto=format&fit=crop',
    area: '85 sqm',
  } as Property,
  {
    id: -4,
    name: 'Kilimani One-Bedroom',
    property_type: 'Residential',
    address: 'Kilimani',
    city: 'Nairobi',
    country: 'Kenya',
    status: 'vacant',
    units_count: 40,
    price_label: 'KES 65,000 / month',
    image_url: 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?q=80&w=1200&auto=format&fit=crop',
    bedrooms: 1,
    bathrooms: 1,
    area: '58 sqm',
  } as Property,
  {
    id: -5,
    name: 'Ruaka Mixed-Use Development',
    property_type: 'Mixed Use',
    address: 'Ruaka',
    city: 'Kiambu',
    country: 'Kenya',
    status: 'active',
    units_count: 96,
    price_label: 'From KES 6,900,000',
    image_url: 'https://images.unsplash.com/photo-1449844908441-8829872d2607?q=80&w=1200&auto=format&fit=crop',
    bedrooms: 2,
    area: '75 sqm',
  } as Property,
  {
    id: -6,
    name: 'Nyali Beachfront Bungalow',
    property_type: 'Bungalow',
    address: 'Nyali',
    city: 'Mombasa',
    country: 'Kenya',
    status: 'active',
    units_count: 1,
    price: 32000000,
    image_url: 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?q=80&w=1200&auto=format&fit=crop',
    bedrooms: 4,
    bathrooms: 3,
    area: '260 sqm',
  } as Property,
]
