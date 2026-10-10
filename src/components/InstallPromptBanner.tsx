import React, { useState } from 'react'
import { useTranslation } from '../i18n/LanguageContext'
import { INSTALL_PROMPT_DISMISSED_KEY, useInstallPrompt } from '../hooks/useInstallPrompt'

const readDismissed = (): boolean => {
  try {
    return window.localStorage.getItem(INSTALL_PROMPT_DISMISSED_KEY) === '1'
  } catch {
    return false
  }
}

const InstallPromptBanner: React.FC = () => {
  const { t } = useTranslation()
  const { canInstall, showIosHint, promptInstall } = useInstallPrompt()
  const [dismissed, setDismissed] = useState(readDismissed)

  if (dismissed || (!canInstall && !showIosHint)) return null

  const dismiss = () => {
    setDismissed(true)
    try {
      window.localStorage.setItem(INSTALL_PROMPT_DISMISSED_KEY, '1')
    } catch {
      // Persistence is best-effort; the banner just reappears next visit.
    }
  }

  return (
    <aside className="install-banner" aria-label={t('pwa.install.title')}>
      <img className="install-banner-icon" src="/icons/icon-192.png" alt="" />
      <div className="install-banner-text">
        <strong>{t('pwa.install.title')}</strong>
        <span>{showIosHint && !canInstall ? t('pwa.install.iosBody') : t('pwa.install.body')}</span>
      </div>
      {canInstall && (
        <button type="button" className="button install-banner-action" onClick={() => void promptInstall()}>
          {t('pwa.install.button')}
        </button>
      )}
      <button
        type="button"
        className="button muted install-banner-dismiss"
        onClick={dismiss}
        aria-label={t('pwa.install.dismiss')}
      >
        ✕
      </button>
    </aside>
  )
}

export default InstallPromptBanner
