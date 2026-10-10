import { describe, expect, it } from 'vitest'

import { propertyMapUrl } from './propertyLocation'
import type { Property } from '../types'

const base = { id: 1, owner_id: 1, status: 'active', name: 'Test' } as Property

describe('propertyMapUrl', () => {
  it('prefers precise coordinates with an OpenStreetMap link', () => {
    const url = propertyMapUrl({ ...base, latitude: -1.2921, longitude: 36.8219 })
    expect(url).toContain('openstreetmap.org')
    expect(url).toContain('mlat=-1.2921')
    expect(url).toContain('mlon=36.8219')
  })

  it('falls back to the building coordinates when the listing has none', () => {
    const url = propertyMapUrl({ ...base, building: { latitude: -1.3, longitude: 36.8 } } as Property)
    expect(url).toContain('mlat=-1.3')
  })

  it('uses a geocoded Google search when only an address is known', () => {
    const url = propertyMapUrl({ ...base, address: '12 Kianda Road', city: 'Nairobi', country: 'Kenya' })
    expect(url).toContain('google.com/maps/search')
    expect(url).toContain(encodeURIComponent('12 Kianda Road, Nairobi, Kenya'))
  })

  it('returns null when there is nothing to locate', () => {
    expect(propertyMapUrl(base)).toBeNull()
  })

  it('treats a zero coordinate as a real position, not as missing', () => {
    const url = propertyMapUrl({ ...base, latitude: 0, longitude: 0 })
    expect(url).toContain('mlat=0')
  })
})
