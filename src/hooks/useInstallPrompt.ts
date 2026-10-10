import { useCallback, useEffect, useState } from 'react'

export type InstallOutcome = 'accepted' | 'dismissed' | 'unavailable'

// Chromium's beforeinstallprompt is not in the DOM lib types; model only the
// surface we use.
interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export const INSTALL_PROMPT_DISMISSED_KEY = 'propnoxa-install-dismissed'

const detectIos = (): boolean =>
  typeof navigator !== 'undefined' && /iphone|ipad|ipod/i.test(navigator.userAgent)

const detectStandalone = (): boolean => {
  if (typeof window === 'undefined') return false
  if (typeof window.matchMedia === 'function' && window.matchMedia('(display-mode: standalone)').matches) {
    return true
  }
  return (navigator as Navigator & { standalone?: boolean }).standalone === true
}

export function useInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)

  useEffect(() => {
    const onBeforeInstallPrompt = (event: Event) => {
      event.preventDefault()
      setDeferredPrompt(event as BeforeInstallPromptEvent)
    }
    const onInstalled = () => setDeferredPrompt(null)
    window.addEventListener('beforeinstallprompt', onBeforeInstallPrompt)
    window.addEventListener('appinstalled', onInstalled)
    return () => {
      window.removeEventListener('beforeinstallprompt', onBeforeInstallPrompt)
      window.removeEventListener('appinstalled', onInstalled)
    }
  }, [])

  const promptInstall = useCallback(async (): Promise<InstallOutcome> => {
    if (!deferredPrompt) return 'unavailable'
    await deferredPrompt.prompt()
    const choice = await deferredPrompt.userChoice
    setDeferredPrompt(null)
    return choice.outcome
  }, [deferredPrompt])

  const isStandalone = detectStandalone()

  return {
    canInstall: deferredPrompt !== null,
    // iOS Safari never fires beforeinstallprompt; show manual instructions instead.
    showIosHint: detectIos() && !isStandalone,
    isStandalone,
    promptInstall,
  }
}
