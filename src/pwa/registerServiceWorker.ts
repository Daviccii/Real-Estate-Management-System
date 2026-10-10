/**
 * Service-worker registration.
 *
 * Production: register /sw.js after the window load event so installation
 * never competes with first-paint resources.
 *
 * Development: actively unregister — a SW left behind by a previous
 * `vite preview` / production build would serve stale cached assets to the
 * dev server and make hot reload look broken.
 */
export const registerServiceWorker = (isProd: boolean = import.meta.env.PROD): void => {
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) return

  if (!isProd) {
    navigator.serviceWorker
      .getRegistrations()
      .then((registrations) => registrations.forEach((registration) => void registration.unregister()))
      .catch(() => undefined)
    return
  }

  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {
      // Offline support is an enhancement; the app works fully without it.
    })
  })
}
