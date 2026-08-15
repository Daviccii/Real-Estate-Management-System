import { Property } from '../types'

/**
 * Isolated, clearly-labelled content for the public homepage.
 *
 * PUBLIC_FEATURED_PROPERTIES_FALLBACK is a sample dataset only. It is used
 * when the live property API is unavailable or returns zero public
 * listings, so the homepage still demonstrates the product. Replace/remove
 * once the public listings endpoint is reliably seeded.
 *
 * Everything else here (purpose copy, locations, intelligence cards, steps)
 * is homepage marketing copy, not live data — it does not claim to come
 * from the API.
 */

export type PropertyPurpose = 'buy' | 'rent' | 'invest'

// Alias kept so page components can depend on a homepage-scoped name
// instead of importing the shared `Property` type directly everywhere.
export type PublicProperty = Property

type PurposeCopy = {
  title: string
  subtitle: string
  helper: string
}

export const PUBLIC_PURPOSE_COPY: Record<PropertyPurpose, PurposeCopy> = {
  buy: {
    title: 'Buy with confidence',
    subtitle: 'Ownership-ready homes and developments across Nairobi and beyond.',
    helper: 'Search live listings for sale, or tell us what you need and we\u2019ll narrow it down.',
  },
  rent: {
    title: 'Find your next rental',
    subtitle: 'Apartments, houses and units ready to move into.',
    helper: 'Filter by budget and bedrooms to see what\u2019s available to rent right now.',
  },
  invest: {
    title: 'Invest with intelligence',
    subtitle: 'Opportunities selected for yield, growth and long-term value.',
    helper: 'Explore investment-grade listings as the market intelligence layer comes online.',
  },
}

export const PUBLIC_HOME_LOCATIONS: { label: string; note: string; to: string }[] = [
  { label: 'Nairobi', note: 'The heart of the market \u2014 from CBD offices to Karen villas.', to: '/properties?location=Nairobi' },
  { label: 'Mombasa', note: 'Coastal homes, holiday lets and beachfront investment.', to: '/properties?location=Mombasa' },
  { label: 'Kisumu', note: 'A growing lakeside market with emerging developments.', to: '/properties?location=Kisumu' },
  { label: 'Nakuru', note: 'Fast-expanding residential and commercial corridors.', to: '/properties?location=Nakuru' },
  { label: 'Kiambu', note: 'Suburban growth on Nairobi\u2019s doorstep.', to: '/properties?location=Kiambu' },
]

export const PUBLIC_HOME_INTELLIGENCE: { status: string; title: string; description: string }[] = [
  {
    status: 'Coming soon',
    title: 'Market Trends',
    description: 'Track how prices and demand move across neighbourhoods over time.',
  },
  {
    status: 'Coming soon',
    title: 'Property Values',
    description: 'Understand what similar properties are actually worth today.',
  },
  {
    status: 'Coming soon',
    title: 'Neighbourhood Insights',
    description: 'See the context around a listing \u2014 amenities, growth and character.',
  },
  {
    status: 'Coming soon',
    title: 'Investment Opportunities',
    description: 'Surface listings that match a stronger yield or growth profile.',
  },
]

export const PUBLIC_HOME_STEPS: { step: string; title: string; description: string }[] = [
  { step: '01', title: 'Discover', description: 'Find properties matching your needs.' },
  { step: '02', title: 'Understand', description: 'Explore property details, location and market context.' },
  { step: '03', title: 'Compare', description: 'Evaluate your options side by side.' },
  { step: '04', title: 'Act', description: 'Save, contact, schedule a viewing or apply.' },
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