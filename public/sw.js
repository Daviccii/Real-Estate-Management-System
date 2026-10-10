/*
 * PropNoxa service worker — hand-written, zero dependencies.
 *
 * Strategy:
 *  - App shell (navigation requests): network-first, falling back to the last
 *    successful HTML response cached under "/" so the SPA still boots offline.
 *  - Static assets (already content-hashed by the Vite build): stale-while-
 *    revalidate, so repeat visits are instant and updates land in background.
 *  - /api/*: never cached (live financial and personal data; a stale or shared
 *    cache here would be worse than an offline error).
 *
 * Build-time injection (see src/pwa/swBuild.ts + vite.config.ts):
 *  - VERSION is stamped with a content-derived build id so every deploy gets
 *    fresh cache names and activate() evicts the previous deploy's caches.
 *  - PRECACHE is replaced with the full list of built files, so one online
 *    visit is enough for the whole app to work offline.
 *
 * Every caches.match call passes ignoreVary: true. Vite serves assets with
 * `Vary: Origin`, and page subresources (<script crossorigin>, <link
 * crossorigin>) send an Origin header while SW-internal fetches (cache.add,
 * manual fetch) do not — without ignoreVary those entries are stored but
 * never matched, and offline boots fail with ERR_FAILED.
 */

const VERSION = /*__BUILD_ID__*/ 'dev'
const STATIC_CACHE = `propnoxa-static-${VERSION}`
const RUNTIME_CACHE = `propnoxa-runtime-${VERSION}`

// In an un-injected build this stays the app-shell seed; `npm run build`
// replaces everything between the markers with the full dist file list.
const PRECACHE = /*__PRECACHE_START__*/ [
  '/',
  '/offline.html',
  '/manifest.webmanifest',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/maskable-512.png',
  '/icons/apple-touch-icon.png',
  '/icons/favicon-32.png',
] /*__PRECACHE_END__*/

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(STATIC_CACHE)
      .then((cache) => Promise.all(PRECACHE.map((url) => cache.add(url).catch(() => undefined))))
      .then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key.startsWith('propnoxa-') && key !== STATIC_CACHE && key !== RUNTIME_CACHE)
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return

  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return
  if (url.pathname.startsWith('/api/')) return

  if (request.mode === 'navigate') {
    event.respondWith(networkFirstNavigation(request))
    return
  }
  event.respondWith(staleWhileRevalidate(event))
})

async function networkFirstNavigation(request) {
  try {
    const response = await fetch(request)
    if (response && response.ok) {
      const cache = await caches.open(RUNTIME_CACHE)
      await cache.put('/', response.clone())
    }
    return response
  } catch {
    const cached =
      (await caches.match(request, { ignoreSearch: true, ignoreVary: true })) ||
      (await caches.match('/', { ignoreVary: true }))
    if (cached) return cached
    const offline = await caches.match('/offline.html', { ignoreVary: true })
    return offline || Response.error()
  }
}

function staleWhileRevalidate(event) {
  const { request } = event
  const cached = caches.match(request, { ignoreVary: true })
  const revalidation = fetch(request).then(async (response) => {
    if (response && (response.ok || response.type === 'opaque')) {
      const cache = await caches.open(RUNTIME_CACHE)
      await cache.put(request, response.clone())
    }
    return response
  })
  // Tie the revalidation to the event lifetime: an unattached cache.put can be
  // killed when the worker shuts down before the body is buffered.
  event.waitUntil(revalidation.then(() => undefined, () => undefined))
  return cached.then((hit) => hit || revalidation.catch(() => Response.error()))
}
