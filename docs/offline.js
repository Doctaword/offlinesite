/* Runs on every page of the offline copy:
   1. saves the whole site onto the device the first time (with a progress pill),
   2. keeps a handed-over iPad from landing on dead ends (external links, YouTube) when there is no internet,
   3. adds a small Back button when opened from the Home Screen, where Safari's own buttons are gone. */
(function () {
  var BASE = new URL('.', document.currentScript.src).href;
  var CACHE = 'offline-site-v1';
  var homeMeta = document.querySelector('meta[name="ofl-home"]');
  var HOME = homeMeta ? new URL(homeMeta.content, location.href).href : BASE;   // the features version has its own home
  var FEATURES = location.href.indexOf(BASE + 'features/') === 0;               // the original copy does not download the features pages
  var MODE = FEATURES ? 'f' : 'o';
  function mine(path) { return FEATURES || path.indexOf('features/') !== 0; }
  var standalone = window.navigator.standalone === true || (window.matchMedia && matchMedia('(display-mode: standalone)').matches);

  var css = document.createElement('style');
  css.textContent =
    '#ofl-pill{position:fixed;right:14px;bottom:calc(14px + env(safe-area-inset-bottom));z-index:2147483000;font:500 13px/1 -apple-system,system-ui,sans-serif;' +
    'color:#fff;background:rgba(20,20,20,.86);border:1px solid rgba(255,255,255,.18);border-radius:999px;padding:10px 14px;backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);' +
    'transition:opacity .6s;pointer-events:none;max-width:80vw}' +
    '#ofl-pill.ok{background:rgba(22,101,52,.92)}#ofl-pill.hide{opacity:0}' +
    '#ofl-back{position:fixed;left:14px;bottom:calc(14px + env(safe-area-inset-bottom));z-index:2147483000;width:46px;height:46px;border-radius:50%;border:1px solid rgba(255,255,255,.22);' +
    'background:rgba(20,20,20,.7);color:#fff;font:400 24px/44px -apple-system,system-ui,sans-serif;text-align:center;padding:0;backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);' +
    'cursor:pointer;-webkit-tap-highlight-color:transparent;opacity:.75}' +
    '.ofl-video{display:block;width:100%;height:100%;object-fit:cover;background:#000}';
  document.head.appendChild(css);

  var pill, pillTimer;
  function say(text, cls, ms) {
    if (!pill) { pill = document.createElement('div'); pill.id = 'ofl-pill'; (document.body || document.documentElement).appendChild(pill); }
    pill.textContent = text; pill.className = cls || '';
    clearTimeout(pillTimer);
    if (ms) pillTimer = setTimeout(function () { pill.className = (cls || '') + ' hide'; }, ms);
  }

  // ---- 2. no dead ends when offline -------------------------------------------------
  document.addEventListener('click', function (e) {
    if (navigator.onLine) return;
    var t = e.target;
    var a = t.closest && t.closest('a[href]');
    if (a && /^https?:/.test(a.href) && a.href.indexOf(BASE) !== 0) {
      e.preventDefault(); e.stopPropagation(); say('That link needs internet', '', 2500); return;
    }
    var v = t.closest && t.closest('.sqs-block-video, .video-block');
    if (v && /youtube|vimeo/.test(v.innerHTML)) { e.preventDefault(); e.stopPropagation(); say('This video plays from YouTube and needs internet', '', 3000); }
  }, true);

  // ---- 3. Back button in Home Screen mode --------------------------------------------
  function addBack() {
    var atHome = location.href.split('#')[0].split('?')[0] === HOME;
    if (!standalone || atHome) return;
    var b = document.createElement('button'); b.id = 'ofl-back'; b.setAttribute('aria-label', 'Back'); b.textContent = '‹';
    b.addEventListener('click', function () { if (history.length > 1) history.back(); else location.href = HOME; });
    document.body.appendChild(b);
  }
  if (document.body) addBack(); else document.addEventListener('DOMContentLoaded', addBack);

  // ---- 1. save everything to the device ---------------------------------------------
  if (!('serviceWorker' in navigator) || !window.caches) return;
  navigator.serviceWorker.register(BASE + 'sw.js', { scope: BASE }).then(function () { return navigator.serviceWorker.ready; }).then(save).catch(function (e) { console.warn('offline setup failed', e); });

  function save() {
    if (navigator.storage && navigator.storage.persist) navigator.storage.persist();
    return fetch(BASE + 'm/manifest.json?__fresh=' + Date.now(), { cache: 'no-store' }).then(function (r) { if (!r.ok) throw 0; return r.text(); }).then(function (text) {
      var m = JSON.parse(text);
      var done = localStorage.getItem('ofl-complete-' + MODE);
      if (done === m.version) return;
      return caches.open(CACHE).then(function (cache) {
        return cache.put(BASE + 'm/manifest.json', new Response(text, { headers: { 'Content-Type': 'application/json' } })).then(function () {
          if (navigator.serviceWorker.controller) navigator.serviceWorker.controller.postMessage('reload-map');
          return cache.keys();
        }).then(function (keys) {
          var have = {}; keys.forEach(function (k) { have[k.url] = 1; });
          var pagesStale = localStorage.getItem('ofl-pages-' + MODE) !== m.version;
          var jobs = [], total = 0, got = 0;
          m.pages.forEach(function (p) { var u = BASE + (p ? p + '/' : ''); if (mine(p) && (pagesStale || !have[u])) jobs.push([u, 150000]); });
          ['offline.js', 'manifest.webmanifest', 'icon-180.png', 'icon-512.png'].forEach(function (f) { jobs.push([BASE + f, 20000]); });
          m.files.forEach(function (f) { var u = BASE + f[0]; if (mine(f[0]) && (!have[u] || pagesStale && /(^|\/)cover[^\/]*$/.test(f[0]))) jobs.push([u, f[2]]);   // cover images keep their names, so refresh them with the pages });
          jobs.forEach(function (j) { total += j[1]; });
          var wanted = {}; wanted[BASE + 'm/manifest.json'] = 1; wanted[BASE] = 1;
          m.pages.forEach(function (p) { wanted[BASE + (p ? p + '/' : '')] = 1; });
          m.files.forEach(function (f) { wanted[BASE + f[0]] = 1; });
          ['offline.js', 'manifest.webmanifest', 'icon-180.png', 'icon-512.png'].forEach(function (f) { wanted[BASE + f] = 1; });
          var failed = 0, i = 0;
          function show() { say('Saving for offline… ' + Math.min(99, Math.floor(got / Math.max(total, 1) * 100)) + '%  (keep this open)'); }
          function one(j, tries) {
            return fetch(j[0] + '?__fresh=1', { cache: 'no-store' }).then(function (r) {
              if (!r.ok) throw new Error(r.status);
              return cache.put(j[0], r);
            }).catch(function (e) { if (tries > 0) return one(j, tries - 1); failed++; console.warn('could not save', j[0], e); });
          }
          function worker() {
            if (i >= jobs.length) return Promise.resolve();
            var j = jobs[i++];
            return one(j, 2).then(function () { got += j[1]; show(); return worker(); });
          }
          show();
          var ws = []; for (var n = 0; n < 6; n++) ws.push(worker());
          return Promise.all(ws).then(function () {
            if (failed) { say('Could not save ' + failed + ' files. Reopen with internet to retry.', '', 0); return; }
            keys.forEach(function (k) { if (!wanted[k.url]) cache.delete(k); });
            localStorage.setItem('ofl-pages-' + MODE, m.version); localStorage.setItem('ofl-complete-' + MODE, m.version);
            if (navigator.serviceWorker.controller) navigator.serviceWorker.controller.postMessage('reload-map');
            say('✓ Ready offline', 'ok', 6000);
          });
        });
      });
    }).catch(function () { /* no internet: the saved copy is used as is */ });
  }
})();
