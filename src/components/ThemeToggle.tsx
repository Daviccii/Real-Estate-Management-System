import React from 'react'
import { useTheme, type ThemePreference } from '../contexts/ThemeContext'

const ORDER: ThemePreference[] = ['light', 'dark', 'system']
const ICONS: Record<ThemePreference, string> = { light: '☀️', dark: '🌙', system: '🖥️' }
const LABELS: Record<ThemePreference, string> = { light: 'Light', dark: 'Dark', system: 'System' }

const ThemeToggle: React.FC<{ className?: string }> = ({ className }) => {
  const { preference, setPreference } = useTheme()
  const next = ORDER[(ORDER.indexOf(preference) + 1) % ORDER.length]

  return (
    <button
      type="button"
      className={`button muted theme-toggle${className ? ` ${className}` : ''}`}
      onClick={() => setPreference(next)}
      data-theme-preference={preference}
      aria-label={`Theme: ${LABELS[preference]}. Activate for ${LABELS[next]}.`}
      title={`Theme: ${LABELS[preference]} — activate for ${LABELS[next]}`}
    >
      <span aria-hidden="true">{ICONS[preference]}</span>
    </button>
  )
}

export default ThemeToggle
