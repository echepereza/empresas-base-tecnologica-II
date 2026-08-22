const CACHE_NAME = 'ebt-2-v4';
const APP_SHELL = [
  './',
  './index.html',
  './repaso-final.html',
  './repaso-final.md',
  './manifest.webmanifest',
  './pwa-icon.svg',
  './pwa-icon-maskable.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  const requestUrl = new URL(event.request.url);
  const isMermaid = requestUrl.hostname === 'cdn.jsdelivr.net';

  // Same-origin navigations: network-first, fall back to cached shell.
  if (event.request.mode === 'navigate' && requestUrl.origin === self.location.origin) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(event.request, { ignoreSearch: true });
          return cached || caches.match('./index.html');
        })
    );
    return;
  }

  // Same-origin assets + the Mermaid CDN module: cache-first so the guide and its
  // diagrams keep working offline after the first successful load.
  if (requestUrl.origin === self.location.origin || isMermaid) {
    event.respondWith(
      caches.match(event.request, { ignoreSearch: true }).then(cached => {
        const network = fetch(event.request).then(response => {
          if (response.ok || response.type === 'opaque') {
            const copy = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
          }
          return response;
        }).catch(() => cached);
        return cached || network;
      })
    );
  }
});
