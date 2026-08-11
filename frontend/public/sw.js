// Minimal app-shell service worker.
//
// Scope is deliberately narrow: it only caches the static shell (this app's
// HTML/manifest/icon) so the app can install and its UI can load offline.
// It never intercepts or caches anything under /api/ - this app displays
// clinical/patient data, and serving that stale or from cache while
// offline would be actively misleading, not a feature.
const CACHE_NAME = 'inescape-shell-v1'
const APP_SHELL = ['/', '/index.html', '/manifest.webmanifest', '/icon.svg']

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)),
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))),
      ),
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return
  if (new URL(request.url).pathname.startsWith('/api/')) return

  // Only handle page navigations: fall back to the cached shell when the
  // network is unavailable. All other requests (JS/CSS/API) pass through
  // untouched.
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match('/index.html')))
  }
})
