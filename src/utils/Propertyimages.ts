import { Property } from '../types'

const PEXELS_API_KEY = import.meta.env.VITE_PEXELS_API_KEY as string | undefined
const CACHE_PREFIX = 'pn-image-cache:'

function fallbackImage(property: Property): string {
  return `https://picsum.photos/seed/propnoxa-${property.id}/640/420`
}

function searchQueryFor(property: Property): string {
  const type = (property.property_type || '').toLowerCase()
  const purpose = (property.purpose || '').toLowerCase()

  if (type.includes('villa')) return 'luxury villa exterior'
  if (type.includes('mansion')) return 'mansion estate exterior'
  if (type.includes('bungalow')) return 'bungalow house exterior'
  if (type.includes('apartment')) return purpose === 'rent' ? 'apartment interior modern' : 'modern apartment building exterior'
  if (type.includes('mixed')) return 'mixed use building modern'
  if (type.includes('commercial')) return 'modern office building exterior'
  if (type.includes('industrial')) return 'industrial warehouse building'
  if (type.includes('land')) return 'land plot aerial view'
  return 'modern real estate building'
}

function readCache(propertyId: number): string | null {
  try {
    return sessionStorage.getItem(CACHE_PREFIX + propertyId)
  } catch {
    return null
  }
}

function writeCache(propertyId: number, url: string) {
  try {
    sessionStorage.setItem(CACHE_PREFIX + propertyId, url)
  } catch {
    // sessionStorage unavailable (e.g. private mode) — safe to skip caching
  }
}

/**
 * Resolves the best available image for a property:
 * 1. An explicit image_url on the property record always wins.
 * 2. A cached Pexels result from earlier this session.
 * 3. A fresh Pexels lookup, if VITE_PEXELS_API_KEY is configured.
 * 4. A stable picsum.photos placeholder as the final fallback.
 *
 * Never throws — any failure quietly falls back to the placeholder so a
 * flaky network or missing API key never breaks the property grid.
 */
export async function resolvePropertyImage(property: Property): Promise<string> {
  if (property.image_url) return property.image_url

  const cached = readCache(property.id)
  if (cached) return cached

  if (!PEXELS_API_KEY) return fallbackImage(property)

  try {
    const query = encodeURIComponent(searchQueryFor(property))
    const res = await fetch(`https://api.pexels.com/v1/search?query=${query}&per_page=1&orientation=landscape`, {
      headers: { Authorization: PEXELS_API_KEY },
    })
    if (!res.ok) return fallbackImage(property)
    const data = await res.json()
    const url: string | undefined = data?.photos?.[0]?.src?.large
    if (!url) return fallbackImage(property)
    writeCache(property.id, url)
    return url
  } catch {
    return fallbackImage(property)
  }
}

/** Synchronous placeholder to show while resolvePropertyImage() is in flight. */
export function placeholderPropertyImage(property: Property): string {
  return fallbackImage(property)
}