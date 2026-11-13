// Browses the local copy with the internet still reachable and records anything the copy had to
// fetch from the live servers (things the first crawl never saw). Re-run build.js afterwards.
// Usage: node fill.js <captureDir>   (needs serve.js running)
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path'); const crypto = require('crypto');
const cap = process.argv[2]; const idxPath = path.join(cap, 'index.json'); const index = JSON.parse(fs.readFileSync(idxPath));
const BASE = 'http://pages.localhost:8080/offlinesite/';
const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'docs', 'm', 'manifest.json')));
(async () => {
  const browser = await chromium.launch({ args: ['--host-resolver-rules=MAP pages.localhost 127.0.0.1', '--proxy-bypass-list=pages.localhost'] });
  let added = 0; const errors = {};
  for (const vp of [{ width: 1180, height: 820 }, { width: 820, height: 1180 }]) {
    const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: 2, hasTouch: true,
      userAgent: 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' });
    const first = await ctx.newPage(); await first.goto(BASE, { waitUntil: 'load' });
    await first.waitForFunction(() => navigator.serviceWorker.controller, null, { timeout: 30000 }); await first.close();
    for (const p of manifest.pages) {
      const page = await ctx.newPage(); const pending = [];
      page.on('pageerror', e => { errors[e.message.slice(0, 200)] = (errors[e.message.slice(0, 200)] || 0) + 1; });
      page.on('response', r => {
        const url = r.url(); if (!url.startsWith('http') || url.includes('pages.localhost') || index[url] || r.request().method() !== 'GET' || r.status() !== 200) return;
        if (/youtube|ytimg|google|doubleclick|instagram/.test(url)) return;
        pending.push(r.body().then(buf => { const f = crypto.createHash('sha1').update(url).digest('hex'); fs.writeFileSync(path.join(cap, 'files', f), buf);
          index[url] = { f, type: r.headers()['content-type'] || '', size: buf.length, kind: r.request().resourceType() }; added++; console.log('  +', url.slice(0, 150)); }).catch(() => {}));
      });
      await page.goto(BASE + (p ? p + '/' : ''), { waitUntil: 'load' }); await page.waitForTimeout(1200);
      const h = await page.evaluate(() => document.documentElement.scrollHeight);
      for (let y = 0; y < h; y += Math.round(vp.height * 0.6)) { await page.evaluate(v => window.scrollTo(0, v), y); await page.waitForTimeout(250); }
      const trigger = page.locator('.gallery-masonry-lightbox-link, .gallery-grid-lightbox-link, .js-lightbox-trigger, .sqs-block-image-button.lightbox').first();
      if (await trigger.count()) { await trigger.scrollIntoViewIfNeeded().catch(() => {}); await trigger.click({ timeout: 4000 }).catch(() => {}); await page.waitForTimeout(1000); await page.keyboard.press('ArrowRight'); await page.waitForTimeout(600); await page.keyboard.press('Escape'); }
      await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
      await Promise.all(pending); await page.close();
    }
    await ctx.close();
  }
  fs.writeFileSync(idxPath, JSON.stringify(index)); console.log('added', added, 'js errors', errors);
  await browser.close();
})();
