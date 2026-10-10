import { describe, expect, it } from 'vitest'

import { LANGUAGE_CODES, LANGUAGE_LABELS, SUPPORTED_LANGUAGES, translations } from './translations'
import {
  PUBLIC_HOME_INTELLIGENCE,
  PUBLIC_HOME_LOCATIONS,
  PUBLIC_HOME_STEPS,
  PUBLIC_PURPOSE_COPY,
} from '../data/publicHomeContent'

const collectHomeContentKeys = (): string[] => {
  const keys: string[] = []
  Object.values(PUBLIC_PURPOSE_COPY).forEach((copy) => {
    keys.push(copy.titleKey, copy.subtitleKey, copy.helperKey)
  })
  PUBLIC_HOME_LOCATIONS.forEach((location) => keys.push(location.noteKey))
  PUBLIC_HOME_INTELLIGENCE.forEach((card) => {
    keys.push(card.statusKey, card.titleKey, card.descriptionKey)
  })
  PUBLIC_HOME_STEPS.forEach((step) => keys.push(step.titleKey, step.descriptionKey))
  return keys
}

describe('translation dictionaries', () => {
  it('covers every supported language', () => {
    expect(Object.keys(translations).sort()).toEqual([...SUPPORTED_LANGUAGES].sort())
  })

  it('ships a human label and code for every language', () => {
    SUPPORTED_LANGUAGES.forEach((language) => {
      expect(LANGUAGE_LABELS[language], `label:${language}`).toBeTruthy()
      expect(LANGUAGE_CODES[language], `code:${language}`).toBeTruthy()
    })
  })

  it('keeps en and sw key sets in exact parity', () => {
    expect(Object.keys(translations.sw).sort()).toEqual(Object.keys(translations.en).sort())
  })

  it('has no empty or whitespace-only values', () => {
    Object.entries(translations).forEach(([language, dictionary]) => {
      Object.entries(dictionary).forEach(([key, value]) => {
        expect(value.trim(), `${language}:${key}`).not.toBe('')
      })
    })
  })

  it('resolves every homepage content key in both languages', () => {
    const keys = collectHomeContentKeys()
    expect(keys.length).toBeGreaterThan(0)
    keys.forEach((key) => {
      expect(translations.en[key], `en:${key}`).toBeTruthy()
      expect(translations.sw[key], `sw:${key}`).toBeTruthy()
    })
  })
})
