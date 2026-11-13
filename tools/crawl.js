// Records every network response the live site makes while it is browsed at iPad sizes.
// Usage: node crawl.js <captureDir>
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path'); const crypto = require('crypto');
const ORIGIN = 'https://www.andrewtranart.com';
const PAGES = ['', 'home', 'home/illustration', 'home/fan-art', 'home/sketches', 'home/animated-sketches', 'home/3d', 'home/mecha',
  'home/traditional', 'home/spinefall-gate', 'pantheon-amc', 'pantheon-season-2', 'marvel-puzzle-quest', 'back-4-blood',
  'halo-master-chief-collection', 'digman-1', 'metalocalypse-army-of-the-doomstar', 'the-second-best-hospital-in-the-galaxy-1',
  'tinytina', 'academic', 'resume', 'work', 'fanart', 'new-page', 'bg-paint'];
const VIEWPORTS = [{ width: 1366, height: 1024 }, { width: 1024, height: 1366 }, { width: 1180, height: 820 }, { width: 820, height: 1180 }];
const UA = 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';
const out = process.argv[2]; fs.mkdirSync(path.join(out, 'files'), { recursive: true });
const idxPath = path.join(out, 'index.json');
const index = fs.existsSync(idxPath) ? JSON.parse(fs.readFileSync(idxPath)) : {};
const skipped = {};
(async () => {
  const browser = await chromium.launch();
  for (const vp of VIEWPORTS) {
    const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: 2, hasTouch: true, userAgent: UA });
    for (const p of PAGES) {
      const page = await ctx.newPage(); const pending = [];
      page.on('response', r => {
        const url = r.url(); const req = r.request();
        if (req.method() !== 'GET' || !url.startsWith('http')) return;
        if (r.status() !== 200) { if (r.status() !== 204 && r.status() < 300 || r.status() >= 400) skipped[url] = r.status(); return; }
        if (index[url]) return;
        pending.push(r.body().then(buf => {
          const f = crypto.createHash('sha1').update(url).digest('hex');
          fs.writeFileSync(path.join(out, 'files', f), buf);
          index[url] = { f, type: r.headers()['content-type'] || '', size: buf.length, kind: req.resourceType() };
        }).catch(() => { skipped[url] = 'nobody'; }));
      });
      try {
        await page.goto(ORIGIN + '/' + p, { waitUntil: 'load', timeout: 90000 });
        await page.waitForTimeout(1500);
        const h = await page.evaluate(() => document.documentElement.scrollHeight);
        for (let y = 0; y < h + vp.height; y += Math.round(vp.height * 0.6)) { await page.evaluate(v => window.scrollTo(0, v), y); await page.waitForTimeout(350); }
        await page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {});
        const trigger = page.locator('.gallery-masonry-lightbox-link, .gallery-grid-lightbox-link, .js-lightbox-trigger, .sqs-block-image-button.lightbox').first();
        if (await trigger.count()) {
          await trigger.scrollIntoViewIfNeeded().catch(() => {});
          await trigger.click({ timeout: 4000 }).catch(() => {});
          await page.waitForTimeout(1200); await page.keyboard.press('ArrowRight'); await page.waitForTimeout(800);
          await page.keyboard.press('Escape'); await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
        }
      } catch (e) { console.log('ERR', p, e.message.split('\n')[0]); }
      await Promise.all(pending); await page.close();
      console.log(vp.width + 'x' + vp.height, '/' + p, Object.keys(index).length);
      fs.writeFileSync(idxPath, JSON.stringify(index));
    }
    await ctx.close();
  }
  fs.writeFileSync(path.join(out, 'skipped.json'), JSON.stringify(skipped, null, 1));
  await browser.close();
})();
