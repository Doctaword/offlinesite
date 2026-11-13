// Makes sure every image referenced by the pages has a full-quality (2500px wide) copy,
// so lightboxes look sharp on any iPad in either orientation, even for images the crawl never opened.
// Usage: node topup.js <captureDir>
const fs = require('fs'); const path = require('path'); const crypto = require('crypto');
const { execFileSync } = require('child_process');
const out = process.argv[2]; const idxPath = path.join(out, 'index.json');
const index = JSON.parse(fs.readFileSync(idxPath));
const bases = new Set();
for (const [url, v] of Object.entries(index)) {
  if (v.kind !== 'document') continue;
  const html = fs.readFileSync(path.join(out, 'files', v.f), 'utf8');
  for (const m of html.matchAll(/(?:https?:)?\/\/images\.squarespace-cdn\.com\/content\/[^"'\s?&<>\\)]+/g)) {
    let u = m[0].replace(/^(https?:)?\/\//, 'https://').replace(/&amp;.*$/, '');
    if (/\.(ico)$/i.test(u)) continue;
    bases.add(u);
  }
}
const have = {};
for (const u of Object.keys(index)) { const U = new URL(u); if (U.host !== 'images.squarespace-cdn.com') continue; const w = /format=(\d+)w/.exec(U.search); const b = U.origin + U.pathname; have[b] = Math.max(have[b] || 0, w ? +w[1] : 1); }
let n = 0, bytes = 0, fail = 0;
for (const b of bases) {
  const norm = new URL(b); const key = norm.origin + norm.pathname;
  if ((have[key] || 0) >= 2500) continue;
  const url = key + '?format=2500w';
  if (index[url]) continue;
  const f = crypto.createHash('sha1').update(url).digest('hex'); const dest = path.join(out, 'files', f);
  try {
    const type = execFileSync('curl', ['-sS', '-L', '--fail', '--retry', '3', '-H', 'Accept: image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8', '-o', dest, '-w', '%{content_type}', url], { encoding: 'utf8' });
    const size = fs.statSync(dest).size; index[url] = { f, type, size, kind: 'image' }; n++; bytes += size;
  } catch (e) { fail++; console.log('FAIL', url); }
  if (n % 25 === 0) fs.writeFileSync(idxPath, JSON.stringify(index));
}
fs.writeFileSync(idxPath, JSON.stringify(index));
console.log('images referenced', bases.size, 'added', n, (bytes / 1e6).toFixed(1) + 'MB', 'failed', fail);
