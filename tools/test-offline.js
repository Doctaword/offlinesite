// Opens the local copy once "online" (only localhost is reachable anyway), waits for "Ready offline",
// then reloads pages with every non-local request blocked and reports anything that failed.
// Usage: node test-offline.js <screenshotDir> [width height]
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
const shots = process.argv[2]; const W = +process.argv[3] || 1180, H = +process.argv[4] || 820;
const BASE = 'http://pages.localhost:8080/offlinesite/';   // not plain "localhost", so the site behaves as it will on a real host
(async () => {
  // a dead proxy means nothing outside this machine can be reached, by pages or by the service worker
  const browser = await chromium.launch({ args: ['--proxy-server=http://127.0.0.1:9', '--proxy-bypass-list=pages.localhost', '--host-resolver-rules=MAP pages.localhost 127.0.0.1'] });
  const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1, hasTouch: true,
    userAgent: 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' });
  const page = await ctx.newPage();
  await page.goto(BASE, { waitUntil: 'load' }).catch(e => console.log('first load', e.message.split('\n')[0]));
  const t0 = Date.now();
  await page.waitForFunction(() => localStorage.getItem('ofl-complete'), null, { timeout: 600000 });
  console.log('saved for offline in', ((Date.now() - t0) / 1000).toFixed(0) + 's');
  const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'docs', 'm', 'manifest.json')));
  let problems = 0;
  for (const p of manifest.pages) {
    const pg = await ctx.newPage(); const bad = [], errs = [];
    pg.on('response', r => { if (r.status() >= 400) bad.push(r.status() + ' ' + r.url().slice(0, 140)); });
    pg.on('requestfailed', r => bad.push('FAILED ' + r.url().slice(0, 140)));
    pg.on('pageerror', e => errs.push(e.message.slice(0, 160)));
    await pg.goto(BASE + (p ? p + '/' : ''), { waitUntil: 'load' });
    await pg.waitForTimeout(1200);
    const h = await pg.evaluate(() => document.documentElement.scrollHeight);
    for (let y = 0; y < h; y += Math.round(H * 0.7)) { await pg.evaluate(v => window.scrollTo(0, v), y); await pg.waitForTimeout(250); }
    await pg.waitForTimeout(800);
    const broken = await pg.evaluate(() => [...document.images].filter(i => i.complete && i.naturalWidth === 0 && (i.currentSrc || i.src)).map(i => (i.currentSrc || i.src).slice(0, 140)));
    const unloaded = await pg.evaluate(() => [...document.querySelectorAll('img[data-src]')].filter(i => !i.currentSrc && !i.src).length);
    const vids = await pg.evaluate(() => [...document.querySelectorAll('video')].map(v => v.readyState + '/' + (v.paused ? 'paused' : 'playing')));
    await pg.evaluate(() => window.scrollTo(0, 0)); await pg.waitForTimeout(300);
    if (shots) await pg.screenshot({ path: path.join(shots, (p || 'index').replace(/\//g, '_') + `-${W}.png`) });
    const n = bad.length + broken.length + errs.length; problems += n;
    console.log((n ? 'XX ' : 'ok ') + '/' + p, 'imgs', await pg.evaluate(() => document.images.length), 'unloaded', unloaded, vids.length ? 'video ' + vids.join(',') : '');
    [...new Set(bad)].slice(0, 12).forEach(b => console.log('    ', b)); broken.slice(0, 5).forEach(b => console.log('     broken img', b)); errs.slice(0, 5).forEach(b => console.log('     js error', b));
    await pg.close();
  }
  console.log('problems', problems);
  await browser.close();
})();
