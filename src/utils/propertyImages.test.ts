import { describe, expect, it } from 'vitest'

import type { Property } from '../types'
import { propertyImage } from './propertyImages'

const property = (overrides: Partial<Property> = {}) =>
  ({ id: 42, name: 'Test listing', property_type: 'Apartment', purpose: 'buy', ...overrides }) as Property

describe('propertyImages', () => {
  it('prefers an explicit image_url over anything else', () => {
    expect(propertyImage(property({ image_url: 'https://cdn.test/real.jpg' }))).toBe('https://cdn.test/real.jpg')
  })

  it('serves a local, type-matched photo for apartments', () => {
    expect(propertyImage(property({ id: 2, property_type: 'Apartment' }))).toMatch(/^\/property-images\/apartment-\d\.jpg$/)
  })

  it('serves a matched exterior/interior for rent vs sale', () => {
    expect(propertyImage(property({ id: 1, property_type: 'Apartment', purpose: 'rent' })))
      .toMatch(/^\/property-images\/apartment-interior-\d\.jpg$/)
    expect(propertyImage(property({ id: 2, property_type: 'Apartment', purpose: 'rent' })))
      .toMatch(/^\/property-images\/apartment-\d\.jpg$/)
    expect(propertyImage(property({ id: 3, property_type: 'Apartment', purpose: 'buy' })))
      .toMatch(/^\/property-images\/apartment-\d\.jpg$/)
  })

  it('maps every property type family to its own library folder', () => {
    const cases: Array<[string, RegExp]> = [
      ['Villa', /^\/property-images\/villa-\d\.jpg$/],
      ['Mansion', /^\/property-images\/mansion-\d\.jpg$/],
      ['Bungalow', /^\/property-images\/bungalow-\d\.jpg$/],
      ['Townhouse', /^\/property-images\/townhouse-\d\.jpg$/],
      ['Maisonette', /^\/property-images\/maisonette-\d\.jpg$/],
      ['Studio', /^\/property-images\/studio-\d\.jpg$/],
      ['Bedsitter', /^\/property-images\/studio-\d\.jpg$/],
      ['Penthouse', /^\/property-images\/penthouse-1\.jpg$/],
      ['Office', /^\/property-images\/office-\d\.jpg$/],
      ['Commercial', /^\/property-images\/commercial-\d\.jpg$/],
      ['Industrial', /^\/property-images\/warehouse-\d\.jpg$/],
      ['Land', /^\/property-images\/land-\d\.jpg$/],
    ]
    for (const [type, pattern] of cases) {
      expect(propertyImage(property({ id: 5, property_type: type })), type).toMatch(pattern)
    }
  })

  it('is deterministic per property id', () => {
    const p = property({ id: 13, property_type: 'Villa' })
    expect(propertyImage(p)).toBe(propertyImage({ ...p }))
    expect(propertyImage(p)).toBe(propertyImage(p))
  })

  it('falls back to the apartment library for unknown types', () => {
    expect(propertyImage(property({ id: 4, property_type: 'Space Station' })))
      .toMatch(/^\/property-images\/apartment-\d\.jpg$/)
  })
})
