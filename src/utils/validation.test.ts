import { describe, expect, it } from 'vitest'

import { isEmail, validateAuth, validateProperty } from './validation'

describe('isEmail', () => {
  it('accepts normal addresses', () => {
    expect(isEmail('tenant@example.co.ke')).toBe(true)
  })

  it('rejects missing, blank, and malformed values', () => {
    expect(isEmail(undefined)).toBe(false)
    expect(isEmail('')).toBe(false)
    expect(isEmail('no-at-sign')).toBe(false)
    expect(isEmail('two@@at.com')).toBe(false)
    expect(isEmail('spaces in@email.com')).toBe(false)
    expect(isEmail('missing@domain')).toBe(false)
  })
})

describe('validateAuth', () => {
  it('returns no errors for a valid pair', () => {
    expect(validateAuth('user@example.com', 'Str0ng!Pass42')).toEqual({})
  })

  it('reports each field separately', () => {
    expect(validateAuth('', 'short')).toEqual({
      email: 'Email is required',
      password: 'Password must be at least 6 characters',
    })
    expect(validateAuth('bad-email', 'abcdef')).toEqual({ email: 'Invalid email' })
    expect(validateAuth('a@b.com', undefined)).toEqual({ password: 'Password is required' })
  })
})

describe('validateProperty', () => {
  const valid = {
    name: 'Kilimani Apartment',
    purpose: 'rent',
    units_count: 4,
    bedrooms: 2,
    bathrooms: 1,
    status: 'active',
    construction_status: 'completed',
    image_url: 'https://example.com/a.jpg',
  }

  it('accepts a well-formed listing', () => {
    expect(validateProperty(valid)).toEqual({})
  })

  it('requires a non-blank name and a known purpose', () => {
    expect(validateProperty({ ...valid, name: '   ' })).toEqual({ name: 'Name is required' })
    expect(validateProperty({ ...valid, purpose: 'lease' })).toEqual({ purpose: 'Select a valid purpose' })
  })

  it('rejects fractional or negative counts', () => {
    expect(validateProperty({ ...valid, units_count: -1 })).toEqual({ units_count: 'Units must be a whole number of 0 or more' })
    expect(validateProperty({ ...valid, bedrooms: 1.5 })).toEqual({ bedrooms: 'Bedrooms must be a whole number of 0 or more' })
    expect(validateProperty({ ...valid, bathrooms: -2 })).toEqual({ bathrooms: 'Bathrooms must be a whole number of 0 or more' })
  })

  it('accepts zero units (a land parcel has none)', () => {
    expect(validateProperty({ ...valid, units_count: 0 })).toEqual({})
  })

  it('constrains status and construction status', () => {
    expect(validateProperty({ ...valid, status: 'sold out' })).toEqual({ status: 'Select a valid status' })
    // an unrecognised construction status counts as "not completed", so the
    // completion date is demanded as well
    expect(validateProperty({ ...valid, construction_status: 'almost' })).toEqual({
      construction_status: 'Select a valid construction status',
      completion_date: 'Completion date is required for unfinished property',
    })
  })

  it('only accepts absolute http(s) image URLs', () => {
    expect(validateProperty({ ...valid, image_url: 'javascript:alert(1)' })).toEqual({
      image_url: 'Use a valid http(s) URL',
    })
    expect(validateProperty({ ...valid, showroom_url: '/local/path' })).toEqual({
      showroom_url: 'Use a valid http(s) URL',
    })
  })

  it('demands a completion date for anything not finished', () => {
    expect(validateProperty({ ...valid, construction_status: 'under_construction' })).toEqual({
      completion_date: 'Completion date is required for unfinished property',
    })
    expect(validateProperty({ ...valid, construction_status: 'planned', completion_date: '2027-06-30' })).toEqual({})
  })

  it('tolerates a missing payload entirely', () => {
    expect(validateProperty(undefined).name).toBe('Name is required')
  })
})
