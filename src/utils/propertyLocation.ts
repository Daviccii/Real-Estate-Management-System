import { Property } from '../types'

export function propertyMapUrl(property: Property): string | null {
  const latitude = property.latitude ?? property.building?.latitude
  const longitude = property.longitude ?? property.building?.longitude

  if (latitude != null && longitude != null) {
    return `https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=17/${latitude}/${longitude}`
  }

  const address = [
    property.address,
    property.sub_location,
    property.city,
    property.county,
    property.country,
  ].filter(Boolean).join(', ')

  return address ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}` : null
}