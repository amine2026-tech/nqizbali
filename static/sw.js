const CACHE = 'nqizbali-v1';
const ASSETS = [
    '/',
    '/client',
    '/collector',
    '/static/css/style.css',
    '/static/js/client.js',
    '/static/js/collector.js',
    '/static/manifest.json',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png'
];

// Install — cache all assets
self.addEventListener('install', e => {
    e.waitUntil(
        caches.open(CACHE).then(cache => cache.addAll(ASSETS))
    );
    self.skipWaiting();
});

// Activate — clean old caches
self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

// Fetch — serve from cache first, then network
self.addEventListener('fetch', e => {
    e.respondWith(
        caches.match(e.request).then(cached => {
            return cached || fetch(e.request).then(response => {
                const copy = response.clone();
                caches.open(CACHE).then(cache => cache.put(e.request, copy));
                return response;
            });
        }).catch(() => caches.match('/'))
    );
});