import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { Language, translations, SUPPORTED_LANGUAGES } from './translations'

export const LANGUAGE_STORAGE_KEY = 'propnoxa-language'

export type TranslateParams = Record<string, string | number>
export type TranslateFn = (key: string, params?: TranslateParams) => string

type LanguageContextType = {
  language: Language
  setLanguage: (language: Language) => void
  t: TranslateFn
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

const isLanguage = (value: unknown): value is Language =>
  typeof value === 'string' && (SUPPORTED_LANGUAGES as readonly string[]).includes(value)

const readStoredLanguage = (): Language => {
  try {
    const stored = window?.localStorage?.getItem(LANGUAGE_STORAGE_KEY)
    if (isLanguage(stored)) return stored
  } catch {
    // Storage can be unavailable (private mode, embedded webviews); English is a safe default.
  }
  return 'en'
}

export const applyLanguageToDocument = (language: Language): void => {
  try {
    document.documentElement.setAttribute('lang', language)
  } catch {
    // Non-DOM environments (SSR, tests) simply skip the attribute.
  }
}

export const interpolate = (template: string, params?: TranslateParams): string => {
  if (!params) return template
  return template.replace(/\{(\w+)\}/g, (match, name: string) =>
    Object.prototype.hasOwnProperty.call(params, name) ? String(params[name]) : match,
  )
}

export const translate = (language: Language, key: string, params?: TranslateParams): string => {
  const template = translations[language]?.[key] ?? translations.en[key] ?? key
  return interpolate(template, params)
}

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => readStoredLanguage())

  useEffect(() => {
    applyLanguageToDocument(language)
  }, [language])

  const setLanguage = useCallback((next: Language) => {
    if (!isLanguage(next)) return
    setLanguageState(next)
    try {
      window?.localStorage?.setItem(LANGUAGE_STORAGE_KEY, next)
    } catch {
      // Persistence is best-effort; the in-memory language still applies.
    }
  }, [])

  const t = useCallback<TranslateFn>((key, params) => translate(language, key, params), [language])

  const value = useMemo(() => ({ language, setLanguage, t }), [language, setLanguage, t])

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export function useLanguage() {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider')
  return ctx
}

export function useTranslation() {
  const { t, language, setLanguage } = useLanguage()
  return { t, language, setLanguage }
}
