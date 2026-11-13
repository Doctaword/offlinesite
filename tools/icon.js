const { chromium } = require('playwright'); const path = require('path');
(async () => { const b = await chromium.launch();
  for (const s of [180, 512]) { const p = await b.newPage({ viewport: { width: s, height: s } });
    await p.setContent(`<body style="margin:0;background:#000;display:flex;align-items:center;justify-content:center;height:100vh"><div style="color:#fff;font:700 ${s * 0.36}px/1 Helvetica,Arial,sans-serif;letter-spacing:${-s * 0.01}px">ADT</div></body>`);
    await p.screenshot({ path: path.join(__dirname, '..', 'src', `icon-${s}.png`) }); }
  await b.close(); })();
