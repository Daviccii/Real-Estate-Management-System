import React from 'react'
import { useLanguage } from '../i18n/LanguageContext'
import { LANGUAGE_CODES, LANGUAGE_LABELS, Language } from '../i18n/translations'

const NEXT_LANGUAGE: Record<Language, Language> = { en: 'sw', sw: 'en' }

const LanguageToggle: React.FC<{ className?: string }> = ({ className }) => {
  const { language, setLanguage } = useLanguage()
  const next = NEXT_LANGUAGE[language]

  return (
    <button
      type="button"
      className={`button muted language-toggle${className ? ` ${className}` : ''}`}
      onClick={() => setLanguage(next)}
      data-language={language}
      aria-label={`Language: ${LANGUAGE_LABELS[language]}. Activate for ${LANGUAGE_LABELS[next]}.`}
      title={`Language: ${LANGUAGE_LABELS[language]} — activate for ${LANGUAGE_LABELS[next]}`}
    >
      <span aria-hidden="true">{LANGUAGE_CODES[language]}</span>
    </button>
  )
}

export default LanguageToggle
