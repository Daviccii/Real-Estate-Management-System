import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'

export type ThemePreference = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

export const THEME_STORAGE_KEY = 'propnoxa-theme'

type ThemeContextType = {
  preference: ThemePreference
  theme: ResolvedTheme
  setPreference: (preference: ThemePreference) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

const isPreference = (value: unknown): value is ThemePreference =>
  value === 'light' || value === 'dark' || value === 'system'

const prefersDark = (): boolean => {
  try {
    return (
      typeof window !== 'undefined' &&
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-color-scheme: dark)').matches
    )
  } catch {
    return false
  }
}

const readStoredPreference = (): ThemePreference => {
  try {
    const stored = window?.localStorage?.getItem(THEME_STORAGE_KEY)
    if (isPreference(stored)) return stored
  } catch {
    // Storage can be unavailable (private mode, embedded webviews); system is a safe default.
  }
  return 'system'
}

export const resolveTheme = (preference: ThemePreference): ResolvedTheme =>
  preference === 'system' ? (prefersDark() ? 'dark' : 'light') : preference

export const applyThemeToDocument = (theme: ResolvedTheme): void => {
  try {
    document.documentElement.setAttribute('data-theme', theme)
  } catch {
    // Non-DOM environments (SSR, tests) simply skip the attribute.
  }
}

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState(() => {
    const preference = readStoredPreference()
    return { preference, theme: resolveTheme(preference) }
  })

  useEffect(() => {
    applyThemeToDocument(state.theme)
  }, [state.theme])

  useEffect(() => {
    if (state.preference !== 'system') return
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return
    const query = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () =>
      setState((prev) => (prev.preference === 'system' ? { ...prev, theme: resolveTheme('system') } : prev))
    query.addEventListener('change', onChange)
    return () => query.removeEventListener('change', onChange)
  }, [state.preference])

  const setPreference = useCallback((preference: ThemePreference) => {
    setState({ preference, theme: resolveTheme(preference) })
    try {
      window?.localStorage?.setItem(THEME_STORAGE_KEY, preference)
    } catch {
      // Persistence is best-effort; the in-memory preference still applies.
    }
  }, [])

  return (
    <ThemeContext.Provider value={{ preference: state.preference, theme: state.theme, setPreference }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
