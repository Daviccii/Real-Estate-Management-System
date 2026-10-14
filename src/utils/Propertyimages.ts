import { Property } from '../types'

// Every listing image is served from a local, type-matched photo library
// (public/property-images). Each file is a real, freely-licensed photograph
// chosen so the picture always matches the property type it labels — an
// apartment card shows an apartment building, a land plot shows land, and so
// on. Selection is deterministic per property id, so a listing always keeps
// the same photo across renders and sessions.
const LIBRARY = {
  apartment: [
    '/property-images/apartment-1.jpg',
    '/property-images/apartment-2.jpg',
    '/property-images/apartment-3.jpg',
    '/property-images/apartment-4.jpg',
  ],
  apartmentInterior: [
    '/property-images/apartment-interior-1.jpg',
    '/property-images/apartment-interior-2.jpg',
  ],
  studio: ['/property-images/studio-1.jpg', '/property-images/studio-2.jpg'],
  penthouse: ['/property-images/penthouse-1.jpg'],
  villa: ['/property-images/villa-1.jpg', '/property-images/villa-2.jpg'],
  mansion: ['/property-images/mansion-1.jpg', '/property-images/mansion-2.jpg'],
  bungalow: ['/property-images/bungalow-1.jpg', '/property-images/bungalow-2.jpg'],
  townhouse: ['/property-images/townhouse-1.jpg', '/property-images/townhouse-2.jpg'],
  maisonette: ['/property-images/maisonette-1.jpg', '/property-images/maisonette-2.jpg'],
  office: ['/property-images/office-1.jpg', '/property-images/office-2.jpg'],
  commercial: ['/property-images/commercial-1.jpg', '/property-images/commercial-2.jpg'],
  warehouse: ['/property-images/warehouse-1.jpg', '/property-images/warehouse-2.jpg'],
  land: ['/property-images/land-1.jpg', '/property-images/land-2.jpg'],
} as const

type Kind = keyof typeof LIBRARY

function resolveKind(property: Property): Kind {
  const t = (property.property_type || '').toLowerCase()
  const purpose = (property.purpose || '').toLowerCase()

  if (t.includes('bedsitter') || t.includes('bedsit') || t.includes('studio')) return 'studio'
  if (t.includes('penthouse')) return 'penthouse'
  if (t.includes('apartment') || t.includes('flat')) {
    // Rentals alternate between building shots and real interiors so the grid
    // shows both; sales and investments show the building itself.
    if (purpose === 'rent' && Math.abs(property.id) % 2 === 1) return 'apartmentInterior'
    return 'apartment'
  }
  if (t.includes('villa')) return 'villa'
  if (t.includes('mansion')) return 'mansion'
  if (t.includes('bungalow')) return 'bungalow'
  if (t.includes('townhouse') || t.includes('town house')) return 'townhouse'
  if (t.includes('maisonette')) return 'maisonette'
  if (t.includes('office') || t.includes('mixed')) return 'office'
  if (t.includes('commercial') || t.includes('shop') || t.includes('retail') || t.includes('plaza') || t.includes('mall')) return 'commercial'
  if (t.includes('industrial') || t.includes('warehouse') || t.includes('godown') || t.includes('factory')) return 'warehouse'
  if (t.includes('land') || t.includes('plot')) return 'land'
  return 'apartment'
}

/**
 * Resolves the photo for a property: an explicit image_url always wins,
 * otherwise a deterministic, type-matched photo from the local library.
 * Never returns an unrelated image and never touches the network.
 */
export function propertyImage(property: Property): string {
  if (property.image_url) return property.image_url
  const pool = LIBRARY[resolveKind(property)]
  const index = Math.abs(Math.trunc(property.id) || 0) % pool.length
  return pool[index]
}
