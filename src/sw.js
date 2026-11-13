// rev 2: reinstall so every device re-fetches offline.js
/* Offline service worker for the mirrored site.
   Every request the page makes (to this site or to Squarespace's servers) is answered
   from the copy saved on the device. Nothing here needs the internet once saving is done. */
const CACHE = 'offline-site-v1';
const RUNTIME = 'offline-site-runtime-v1';
const BASE = new URL('./', self.location).href;          // e.g. https://user.github.io/offlinesite/
const LIVE_HOST = 'www.andrewtranart.com';
let mapPromise = null;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(['./', 'offline.js', 'm/manifest.json'].map(u => new Request(u, { cache: 'reload' })))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('message', e => { if (e.data === 'reload-map') mapPromise = null; });

function loadMap() {
  if (!mapPromise) {
    mapPromise = caches.open(CACHE).then(c => c.match(BASE + 'm/manifest.json')).then(r => r ? r.json() : fetch(BASE + 'm/manifest.json').then(r => r.json())).then(m => {
      const byPath = new Map(); const byName = new Map();
      for (const key of Object.keys(m.urls)) {
        const q = key.indexOf('?'); const p = q < 0 ? key : key.slice(0, q);
        if (/\.(js|css)$/.test(p)) { const name = p.slice(p.lastIndexOf('/') + 1); if (!byName.has(name)) byName.set(name, key); }
        if (!byPath.has(p)) byPath.set(p, []);
        const w = /[?&]format=(\d+)w/.exec(key);
        byPath.get(p).push({ key, w: w ? +w[1] : 0 });
      }
      m.byPath = byPath; m.byName = byName;
      m.fileIndex = {}; m.files.forEach((f, i) => { m.fileIndex[f[0]] = i; });
      return m;
    }).catch(err => { mapPromise = null; throw err; });
  }
  return mapPromise;
}

// Find the saved file for a URL: exact match first, then the same path with the closest image size.
function lookup(m, url) {
  let host = url.host, path = url.pathname;
  if (url.href.startsWith(BASE)) return null;
  if (url.origin === self.location.origin) host = LIVE_HOST;   // absolute paths like /universal/svg/...
  const key = host + path + url.search;
  if (m.urls[key] !== undefined) return m.files[m.urls[key]];
  const list = m.byPath.get(host + path);
  if (!list) {   // scripts and styles are fingerprinted, so the file name alone identifies them wherever the page looks
    const name = path.slice(path.lastIndexOf('/') + 1);
    return m.byName.has(name) ? m.files[m.urls[m.byName.get(name)]] : null;
  }
  const want = /[?&]format=(\d+)w/.exec(url.search);
  let pick = list[0];
  if (list.length > 1) {
    const sorted = list.slice().sort((a, b) => a.w - b.w);
    pick = sorted[sorted.length - 1];
    if (want) { const ok = sorted.find(x => x.w >= +want[1]); if (ok) pick = ok; }
  }
  return m.files[m.urls[pick.key]];
}

async function fromCache(fileUrl, type, request) {
  const cache = await caches.open(CACHE);
  let res = await cache.match(fileUrl, { ignoreSearch: true });
  if (!res) {
    res = await fetch(fileUrl);
    if (res.ok) cache.put(fileUrl, res.clone());
  }
  if (!res.ok) return res;
  const range = request.headers.get('range');
  const headers = new Headers({ 'Content-Type': type || res.headers.get('Content-Type') || 'application/octet-stream', 'Accept-Ranges': 'bytes' });
  if (range) {   // video seeking: answer byte-range requests from the saved file
    const buf = await res.arrayBuffer();
    const m = /bytes=(\d*)-(\d*)/.exec(range) || [];
    let start = m[1] ? +m[1] : 0, end = m[2] ? +m[2] : buf.byteLength - 1;
    if (!m[1] && m[2]) { start = buf.byteLength - +m[2]; end = buf.byteLength - 1; }
    end = Math.min(end, buf.byteLength - 1);
    headers.set('Content-Range', `bytes ${start}-${end}/${buf.byteLength}`);
    headers.set('Content-Length', String(end - start + 1));
    return new Response(buf.slice(start, end + 1), { status: 206, headers });
  }
  return new Response(res.body, { status: 200, headers });
}

function timeout(ms) { return new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), ms)); }

async function handle(request) {
  const url = new URL(request.url);
  if (request.method !== 'GET') {
    // blocks that ask the server to render them get the answer saved from the live site; everything else (analytics) gets an empty one
    if (url.pathname.endsWith('/api/block/render')) {
      try {
        const m = await loadMap(); const id = (await request.clone().json()).block.id;
        if (m.blocks && m.blocks[id] !== undefined) return fromCache(BASE + m.files[m.blocks[id]][0], 'application/json', new Request(request.url));
      } catch (e) { /* fall through */ }
    }
    return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
  }
  if (url.searchParams.has('__fresh')) return fetch(request);                 // used while saving files to the device
  let m;
  try { m = await loadMap(); } catch (e) { return fetch(request); }
  // Files that are part of this copy (pages, saved assets, the app shell)
  if (url.href.startsWith(BASE)) {
    let rel = url.pathname.slice(new URL(BASE).pathname.length);
    if (request.mode === 'navigate' || rel === '' || rel.endsWith('/')) {
      // A folder address typed without its last slash must be redirected, as a web server does: otherwise the page's own
      // relative links (and the features version's jump to site/) resolve one level too high.
      if (rel !== '' && !rel.endsWith('/') && !/\.[a-z0-9]+$/i.test(rel)) return Response.redirect(BASE + rel + '/' + url.search, 301);
      rel = rel.replace(/\/?$/, '/').replace(/^\/$/, '');
      if (m.pages.includes(rel.replace(/\/$/, ''))) return fromCache(BASE + rel, 'text/html; charset=utf-8', request);
      // A page this saved copy does not know yet (the site was updated since it was saved): take it from the internet
      // and forget the old list so the next request reads the new one. Only when that fails, go home rather than show an error.
      try {
        const res = await Promise.race([fetch(request), timeout(6000)]);
        if (res && res.ok) { mapPromise = null; caches.open(CACHE).then(c => c.add(new Request(BASE + 'm/manifest.json', { cache: 'reload' }))).catch(() => {}); return res; }
      } catch (e) { /* offline */ }
      return fromCache(BASE, 'text/html; charset=utf-8', request);
    }
    const idx = m.fileIndex[rel];
    return fromCache(BASE + rel, idx !== undefined ? m.files[idx][1] : null, request);
  }
  const hit = lookup(m, url);
  if (hit) return fromCache(BASE + hit[0], hit[1], request);
  if (request.mode === 'navigate') return fetch(request);
  // the site's own server API does not exist in the copy; answer the way the live site does for visitors
  if (url.origin === self.location.origin) return new Response('{}', { status: 401, headers: { 'Content-Type': 'application/json' } });
  // Not in the saved copy: try the internet briefly, keep a copy if it works, otherwise fail quietly.
  const rt = await caches.open(RUNTIME);
  const cached = await rt.match(request.url);
  if (cached) return cached;
  try {
    const res = await Promise.race([fetch(request), timeout(4000)]);
    if (res && (res.ok || res.type === 'opaque') && /squarespace|sqspcdn/.test(url.host)) rt.put(request.url, res.clone());
    return res;
  } catch (e) {
    return new Response('', { status: 504, statusText: 'Offline' });
  }
}

self.addEventListener('fetch', e => {
  const u = e.request.url;
  if (!u.startsWith('http')) return;
  e.respondWith(handle(e.request));
});
