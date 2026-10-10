import { describe, expect, it } from 'vitest'

import { parseVoiceQuery } from './voiceQueryParser'

describe('parseVoiceQuery', () => {
  it('parses a full rental brief into criteria and chips', () => {
    const { criteria, understood, heard } = parseVoiceQuery(
      'I need a three bedroom apartment in Kilimani under 80k per month with parking and security',
    )

    expect(criteria).toEqual({
      purpose: 'rent',
      max_budget: 80000,
      preferred_city: 'Kilimani',
      min_bedrooms: 3,
      property_type: 'apartment',
      require_parking: true,
      require_security: true,
    })
    expect(understood).toEqual([
      'Rent',
      'Up to KSh 80,000',
      'Kilimani',
      '3+ bedrooms',
      'Apartment',
      'Parking',
      'Security',
    ])
    expect(heard).toBe(
      'I need a three bedroom apartment in Kilimani under 80k per month with parking and security',
    )
  })

  it('parses a purchase brief with word-number bedrooms and millions', () => {
    const { criteria, understood } = parseVoiceQuery(
      'Looking to buy a four bedroom house in Karen for around 45 million shillings',
    )

    expect(criteria).toEqual({
      purpose: 'sale',
      max_budget: 45_000_000,
      preferred_city: 'Karen',
      min_bedrooms: 4,
      property_type: 'house',
    })
    expect(understood).toContain('Buy')
    expect(understood).toContain('Up to KSh 45,000,000')
  })

  it('treats a studio as one bedroom and keeps multi-word localities intact', () => {
    const { criteria, understood } = parseVoiceQuery(
      'Looking for a studio apartment in South B for under 25,000 shillings a month',
    )

    expect(criteria).toEqual({
      purpose: 'rent',
      max_budget: 25000,
      preferred_city: 'South B',
      min_bedrooms: 1,
      property_type: 'apartment',
    })
    expect(understood).toContain('Studio')
    expect(understood).not.toContain('1+ bedrooms')
  })

  it('captures an unfurnished flat with a balcony', () => {
    const { criteria, understood } = parseVoiceQuery(
      'I want to rent an unfurnished two bedroom flat in Westlands with a balcony',
    )

    expect(criteria).toEqual({
      purpose: 'rent',
      preferred_city: 'Westlands',
      min_bedrooms: 2,
      property_type: 'apartment',
      furnishing: 'unfurnished',
      require_balcony: true,
    })
    expect(understood).toContain('Unfurnished')
    expect(understood).toContain('Balcony')
  })

  it('captures furnished listings, amenities and the CBD alias', () => {
    const { criteria, understood } = parseVoiceQuery(
      'Show me a fully furnished three bedroom apartment in CBD with a swimming pool and gym for 120k per month',
    )

    expect(criteria).toEqual({
      purpose: 'rent',
      max_budget: 120000,
      preferred_city: 'CBD',
      min_bedrooms: 3,
      property_type: 'apartment',
      furnishing: 'furnished',
      amenities: ['Swimming Pool', 'Gym'],
    })
    expect(understood).toContain('Swimming pool')
    expect(understood).toContain('Gym')
  })

  it('maps office/business wording to commercial', () => {
    const { criteria, understood } = parseVoiceQuery(
      'I need office space in Nakuru under 2 million for my business',
    )

    expect(criteria).toEqual({
      max_budget: 2_000_000,
      preferred_city: 'Nakuru',
      property_type: 'commercial',
    })
    expect(understood).toContain('Commercial')
  })

  it('returns empty criteria for gibberish', () => {
    const { criteria, understood } = parseVoiceQuery('hello there just checking')

    expect(criteria).toEqual({})
    expect(understood).toEqual([])
  })

  it('handles a bedsitter with a compact budget', () => {
    const { criteria } = parseVoiceQuery('bedsitter in Buruburu for 15k')

    expect(criteria).toEqual({
      max_budget: 15000,
      preferred_city: 'Buruburu',
      min_bedrooms: 1,
      property_type: 'apartment',
    })
  })

  it('falls back to an unknown locality from context', () => {
    const { criteria, understood } = parseVoiceQuery("I'm looking for a house in Greenfields")

    expect(criteria.preferred_city).toBe('Greenfields')
    expect(criteria.property_type).toBe('house')
    expect(understood).toContain('Greenfields')
  })

  it('rejects generic phrases masquerading as localities', () => {
    const { criteria } = parseVoiceQuery(
      'I want to buy a commercial property in a good area around 20 million',
    )

    expect(criteria.preferred_city).toBeUndefined()
    expect(criteria.property_type).toBe('commercial')
    expect(criteria.max_budget).toBe(20_000_000)
  })

  it('parses "for sale" with digit bedrooms and a maisonette', () => {
    const { criteria } = parseVoiceQuery('for sale 4 bedroom maisonette in Kiambu for 35 million')

    expect(criteria).toEqual({
      purpose: 'sale',
      max_budget: 35_000_000,
      preferred_city: 'Kiambu',
      min_bedrooms: 4,
      property_type: 'house',
    })
  })

  it('parses a minimal digit-bedroom townhouse brief', () => {
    const { criteria, understood } = parseVoiceQuery('3 bedroom townhouse in Ruiru')

    expect(criteria).toEqual({
      preferred_city: 'Ruiru',
      min_bedrooms: 3,
      property_type: 'house',
    })
    expect(understood).toEqual(['Ruiru', '3+ bedrooms', 'House'])
  })

  it('keeps the original casing in the heard transcript', () => {
    const { heard } = parseVoiceQuery('  Two Bedroom Apartment in Kilimani  ')

    expect(heard).toBe('Two Bedroom Apartment in Kilimani')
  })
})
