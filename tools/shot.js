// Screenshot pages of the local copy at an iPad size. Usage: node shot.js <outDir> <w> <h> <path> [path...]
const { chromium } = require('playwright'); const path = require('path');
(async () => { const [out, w, h, ...paths] = process.argv.slice(2);
  const b = await chromium.launch({ args: ['--host-resolver-rules=MAP pages.localhost 127.0.0.1', '--proxy-server=http://127.0.0.1:9', '--proxy-bypass-list=pages.localhost'] });
  const ctx = await b.newContext({ viewport: { width: +w, height: +h }, hasTouch: true });
  for (const p of paths) { const pg = await ctx.newPage(); await pg.goto('http://pages.localhost:8080/offlinesite/' + p, { waitUntil: 'load' }); await pg.waitForTimeout(2500);
    await pg.screenshot({ path: path.join(out, (p.replace(/[\/#]/g, '_') || 'home') + `-${w}.png`), fullPage: process.env.FULL === '1' }); await pg.close(); }
  await b.close(); })();
