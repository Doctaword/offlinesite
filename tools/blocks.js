// Some blocks ask the live server to render them after the page loads (POST /api/block/render).
// This saves each answer, keyed by block id, so the offline copy can give the same answer.
// Usage: node blocks.js <captureDir>
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const cap = process.argv[2]; const out = path.join(cap, 'blocks'); fs.mkdirSync(out, { recursive: true });
const index = JSON.parse(fs.readFileSync(path.join(cap, 'index.json')));
const pages = Object.entries(index).filter(([u, v]) => v.kind === 'document' && u.includes('www.andrewtranart.com')).map(([u]) => u);
(async () => {
  const browser = await chromium.launch(); let n = 0;
  const ctx = await browser.newContext({ viewport: { width: 1180, height: 820 }, hasTouch: true, userAgent: 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' });
  for (const u of pages) {
    const page = await ctx.newPage(); const pending = [];
    page.on('response', r => { if (r.request().method() === 'POST' && r.url().includes('/api/block/render') && r.status() === 200) pending.push(r.text().then(t => {
      const id = JSON.parse(r.request().postData()).block.id; fs.writeFileSync(path.join(out, id.replace(/[^\w-]/g, '_') + '.json'), t); n++; }).catch(e => console.log('ERR', e.message))); });
    await page.goto(u, { waitUntil: 'load' }).catch(() => {}); await page.waitForTimeout(1500);
    const h = await page.evaluate(() => document.documentElement.scrollHeight);
    for (let y = 0; y < h; y += 600) { await page.evaluate(v => window.scrollTo(0, v), y); await page.waitForTimeout(150); }
    await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {}); await Promise.all(pending); await page.close();
  }
  console.log('block answers saved', n, fs.readdirSync(out));
  await browser.close();
})();
