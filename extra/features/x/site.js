/* Lightbox for the added pages: opens instantly from the already-loaded thumbnail, swaps in the full
   image when it is decoded, and preloads the neighbours so swiping never waits. */
(function () {
  var shots = [].slice.call(document.querySelectorAll('a.shot'));
  if (!shots.length) return;
  var lb = document.createElement('div'); lb.id = 'lb';
  lb.innerHTML = '<img alt=""><div class="cap"></div><button class="x" aria-label="Close">×</button><button class="p" aria-label="Previous">‹</button><button class="n" aria-label="Next">›</button>';
  document.body.appendChild(lb);
  var img = lb.querySelector('img'), cap = lb.querySelector('.cap'), cur = -1, warm = {};
  function preload(i) { if (i < 0 || i >= shots.length || warm[i]) return; var p = new Image(); p.decoding = 'async'; p.src = shots[i].href; warm[i] = p; }
  function show(i) {
    if (i < 0 || i >= shots.length) return;
    cur = i; var a = shots[i], t = a.querySelector('img');
    img.style.transform = ''; img.src = (warm[i] && warm[i].complete) ? a.href : (t ? t.currentSrc || t.src : a.href);
    if (!(warm[i] && warm[i].complete)) { preload(i); var want = i; warm[i].decode ? warm[i].decode().then(function () { if (cur === want) img.src = a.href; }).catch(function () { if (cur === want) img.src = a.href; }) : (warm[i].onload = function () { if (cur === want) img.src = a.href; }); }
    cap.textContent = (a.dataset.cap ? a.dataset.cap + '   ' : '') + (i + 1) + ' / ' + shots.length;
    preload(i + 1); preload(i - 1); preload(i + 2);
  }
  function open(i) { lb.classList.add('open'); document.documentElement.style.overflow = 'hidden'; show(i); }
  function close() { lb.classList.remove('open'); document.documentElement.style.overflow = ''; cur = -1; }
  shots.forEach(function (a, i) { a.addEventListener('click', function (e) { e.preventDefault(); open(i); }); });
  lb.querySelector('.x').addEventListener('click', close);
  lb.querySelector('.p').addEventListener('click', function (e) { e.stopPropagation(); show(cur - 1); });
  lb.querySelector('.n').addEventListener('click', function (e) { e.stopPropagation(); show(cur + 1); });
  document.addEventListener('keydown', function (e) { if (cur < 0) return; if (e.key === 'Escape') close(); if (e.key === 'ArrowRight') show(cur + 1); if (e.key === 'ArrowLeft') show(cur - 1); });
  // touch: swipe sideways to move, swipe down to close, pinch or double-tap to zoom, drag to pan while zoomed
  var sx = 0, sy = 0, scale = 1, tx = 0, ty = 0, startDist = 0, startScale = 1, mode = '', lastTap = 0, bx = 0, by = 0;
  function apply() { img.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')'; }
  function reset() { scale = 1; tx = ty = 0; img.style.transition = 'transform .18s'; apply(); setTimeout(function () { img.style.transition = ''; }, 200); }
  lb.addEventListener('touchstart', function (e) {
    if (e.target.tagName === 'BUTTON') return;
    if (e.touches.length === 2) { mode = 'pinch'; startDist = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY); startScale = scale; }
    else { mode = scale > 1 ? 'pan' : 'swipe'; sx = e.touches[0].clientX; sy = e.touches[0].clientY; bx = tx; by = ty; }
  }, { passive: true });
  lb.addEventListener('touchmove', function (e) {
    if (mode === 'pinch' && e.touches.length === 2) { var d = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY); scale = Math.max(1, Math.min(5, startScale * d / startDist)); apply(); }
    else if (mode === 'pan') { tx = bx + e.touches[0].clientX - sx; ty = by + e.touches[0].clientY - sy; apply(); }
    else if (mode === 'swipe') { tx = e.touches[0].clientX - sx; ty = Math.max(0, e.touches[0].clientY - sy); if (Math.abs(tx) > ty) ty = 0; else tx = 0; apply(); }
  }, { passive: true });
  lb.addEventListener('touchend', function (e) {
    if (e.target.tagName === 'BUTTON') return;
    if (mode === 'pinch') { if (scale < 1.05) reset(); mode = ''; return; }
    if (mode === 'swipe') {
      var dx = tx, dy = ty; tx = ty = 0; apply();
      if (Math.abs(dx) > 50) { show(cur + (dx < 0 ? 1 : -1)); }
      else if (dy > 90) { close(); }
      else if (Math.abs(dx) < 8 && dy < 8) { var now = Date.now(); if (now - lastTap < 300) { scale = 2.5; apply(); } lastTap = now; }
    } else if (mode === 'pan') { var n = Date.now(); if (Math.abs(tx - bx) < 8 && Math.abs(ty - by) < 8) { if (n - lastTap < 300) reset(); lastTap = n; } }
    mode = '';
  });
})();
