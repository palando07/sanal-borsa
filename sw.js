// Uygulamayı çevrimdışı da açılabilir kılan basit önbellek
const CACHE = 'sanal-borsa-v4';
const FILES = ['./', './index.html', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
// Önce ağdan dene (güncel sürüm gelsin), ağ yoksa önbellekten aç
self.addEventListener('fetch', e => {
  // Fiyat istekleri (GitHub, Binance) önbelleğe alınmaz; uygulama son fiyatları kendisi saklar
  if (e.request.method !== 'GET' || new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(
    fetch(e.request).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy));
      return res;
    }).catch(() => caches.match(e.request))
  );
});
