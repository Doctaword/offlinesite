// Turns the captured responses into the static offline site in ../docs.
// Usage: node build.js <captureDir> <videoDir>
const fs = require('fs'); const path = require('path');
const [cap, videoDir] = process.argv.slice(2);
const ROOT = path.join(__dirname, '..'); const DOCS = path.join(ROOT, 'docs'); const SRC = path.join(ROOT, 'src');
const LIVE = 'https://www.andrewtranart.com'; const LIVE_HOST = 'www.andrewtranart.com';
const index = JSON.parse(fs.readFileSync(path.join(cap, 'index.json')));
fs.rmSync(DOCS, { recursive: true, force: true }); fs.mkdirSync(path.join(DOCS, 'm'), { recursive: true });

const EXT = { 'text/html': '.html', 'text/css': '.css', 'text/javascript': '.js', 'application/javascript': '.js', 'application/json': '.json', 'image/webp': '.webp', 'image/gif': '.gif',
  'image/jpeg': '.jpg', 'image/png': '.png', 'image/svg+xml': '.svg', 'font/woff2': '.woff2', 'font/woff': '.woff', 'image/x-icon': '.ico', 'image/vnd.microsoft.icon': '.ico', 'text/plain': '.txt', 'video/mp4': '.mp4', 'image/avif': '.avif' };
const files = [], fileIdx = {}, urls = {}, pages = [], pageHtml = {};
const sha = p => require('crypto').createHash('sha1').update(fs.readFileSync(p)).digest('hex').slice(0, 16);
function addFile(srcPath, name, type, size) {
  if (fileIdx[name] === undefined) { fs.copyFileSync(srcPath, path.join(DOCS, 'm', name)); fileIdx[name] = files.length; files.push(['m/' + name, type, size]); }
  return fileIdx[name];
}
for (const [url, v] of Object.entries(index)) {
  const U = new URL(url);
  if (v.kind === 'document' && U.host === LIVE_HOST) { const p = U.pathname.replace(/^\/|\/$/g, ''); pages.push(p); pageHtml[p] = fs.readFileSync(path.join(cap, 'files', v.f), 'utf8'); continue; }
  if (U.host === 'video.squarespace-cdn.com' && !/\/thumbnail$/.test(U.pathname)) continue;   // streams are replaced by plain mp4 files below
  if (v.size === 0) continue;
  let type = (v.type || '').split(';')[0].trim(), src = path.join(cap, 'files', v.f), ctype = v.type, size = v.size;
  const opt = path.join(cap, 'opt', v.f);   // lighter re-encode made by optimize.py, when there is one
  if (fs.existsSync(opt)) { src = opt; type = ctype = 'image/webp'; size = fs.statSync(opt).size; }
  const i = addFile(src, sha(src) + (EXT[type] || ''), ctype, size);   // named by content, so identical files are stored once
  urls[U.host + U.pathname + U.search] = i;
}
// videos
const videos = {};
for (const f of fs.readdirSync(videoDir)) {
  if (!f.endsWith('.mp4')) continue; const id = f.replace('.mp4', '');
  addFile(path.join(videoDir, f), 'video-' + id.slice(0, 8) + '.mp4', 'video/mp4', fs.statSync(path.join(videoDir, f)).size);
  addFile(path.join(videoDir, id + '.thumb'), 'video-' + id.slice(0, 8) + '.jpg', 'image/jpeg', fs.statSync(path.join(videoDir, id + '.thumb')).size);
  videos[id] = 'm/video-' + id.slice(0, 8);
}

// server-rendered block answers (see blocks.js)
const blocks = {};
const blockDir = path.join(cap, 'blocks');
if (fs.existsSync(blockDir)) for (const f of fs.readdirSync(blockDir)) {
  const src = path.join(blockDir, f); const id = JSON.parse(fs.readFileSync(src, 'utf8')).blockId;
  blocks[id] = addFile(src, 'block-' + sha(src) + '.json', 'application/json', fs.statSync(src).size);
}
const unesc = s => s.replace(/&quot;/g, '"').replace(/&amp;/g, '&');
let version = '';
// Each mirrored page is written twice: once as the untouched original, and once under features/site/ with the top bar added.
// pages whose look depends on the light page background; every other page gets a black one, so iPadOS has no light colour to fade the top edge into
const LIGHT_PAGES = ['back-4-blood', 'tinytina', 'work', 'new-page'];
function render(p, outRel, up, head) {
  const depth = p ? p.split('/').length : 0; const pre = depth ? '../'.repeat(depth) : './';
  const root = pre + up;   // where m/, offline.js and the icons live, seen from this page
  let h = pageHtml[p];
  // internal links -> relative, so the copy works under any address
  h = h.replace(/(href|src)="(?:https?:\/\/www\.andrewtranart\.com)?(\/(?!\/)[^"]*)?"/g, (all, attr, target) => {
    if (target === undefined) { return all.includes('andrewtranart') ? `${attr}="${pre}"` : all; }
    const hash = target.includes('#') ? target.slice(target.indexOf('#')) : ''; const clean = target.split('#')[0].split('?')[0].replace(/^\/|\/$/g, '');
    if (pages.includes(clean)) return `${attr}="${pre}${clean ? clean + '/' : ''}${hash}"`;
    const asset = urls[LIVE_HOST + '/' + clean];
    if (asset !== undefined) return `${attr}="${root}${files[asset][0]}${hash}"`;
    return `${attr}="${pre}"`;
  });
  // native video blocks -> plain <video> playing the saved mp4
  h = h.replace(/<div\s+class="sqs-native-video"\s+data-config-settings="([^"]*)"\s+data-config-video="([^"]*)"[^>]*>\s*<div\s+class="native-video-player"\s+style="([^"]*)"\s*>\s*<\/div>/g, (all, s, v, style) => {
    const set = JSON.parse(unesc(s)), vid = JSON.parse(unesc(v)); const local = videos[vid.systemDataId];
    if (!local) { console.log('WARN no local video for', vid.systemDataId); return all; }
    const attrs = ['playsinline', 'webkit-playsinline', 'preload="auto"', set.muted ? 'muted' : '', set.autoPlay ? 'autoplay' : '', set.loop ? 'loop' : '', set.controls === 'full' || !set.autoPlay ? 'controls' : ''].filter(Boolean).join(' ');
    return `<div class="ofl-native-video"><div class="native-video-player" style="${style}"><video class="ofl-video" ${attrs} poster="${root}${local}.jpg" src="${root}${local}.mp4"></video></div>`;
  });
  if (h.includes('sqs-native-video"')) console.log('WARN unreplaced native video on', p);
  h = h.replace(/<meta name="viewport" content="[^"]*">/, '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">');
  h = h.replace('</head>', `<meta name="robots" content="noindex">
<link rel="manifest" href="${up ? pre + '../' : pre}manifest.webmanifest">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="Andrew Tran">
<meta name="theme-color" content="#000000">${LIGHT_PAGES.includes(p) ? '' : '<style>html,body{background:#000!important}</style>'}
<link rel="apple-touch-icon" href="${root}icon-180.png">${head ? head(pre) : ''}
<script defer src="${root}offline.js"></script>
</head>`);
  const dir = path.join(DOCS, outRel, p); fs.mkdirSync(dir, { recursive: true }); fs.writeFileSync(path.join(dir, 'index.html'), h);
  version += h.length + ':';
}
const mirrored = pages.slice();
for (const p of mirrored) render(p, '', '', null);
const FEATURES = fs.existsSync(path.join(ROOT, 'extra', 'features'));
if (FEATURES) for (const p of mirrored) {
  render(p, 'features/site', '../../', pre => `<meta name="ofl-home" content="${pre}"><link rel="stylesheet" href="${pre}../x/bar.css"><script defer src="${pre}../x/bar.js"></script>`);
  pages.push('features/site' + (p ? '/' + p : ''));
}

for (const f of fs.readdirSync(SRC)) fs.copyFileSync(path.join(SRC, f), path.join(DOCS, f));
// extra pages (process, direction, tailored resume...) live in ../extra and are copied on top of the mirror.
// A folder there with an index.html becomes (or replaces) a page; every other file is saved for offline too.
const EXTRA = path.join(ROOT, 'extra');
const TYPE_BY_EXT = Object.fromEntries(Object.entries(EXT).map(([t, e]) => [e, t])); TYPE_BY_EXT['.pdf'] = 'application/pdf';
const renamed = [];
(function walk(dir, rel) {
  if (!fs.existsSync(dir)) return;
  for (const f of fs.readdirSync(dir)) {
    const src = path.join(dir, f), r = rel ? rel + '/' + f : f;
    if (fs.statSync(src).isDirectory()) { walk(src, r); continue; }
    if (f === 'summary.json') continue;
    fs.mkdirSync(path.join(DOCS, rel), { recursive: true });
    if (/(^|\/)x$/.test(rel) && /\.(css|js)$/.test(f)) {
      // shared styles and scripts get their content hash in the name: a device only downloads files it does not have yet,
      // so a changed file must have a new name to reach it
      const h = require('crypto').createHash('sha1').update(fs.readFileSync(src)).digest('hex').slice(0, 10);
      const hf = f.replace(/\.(css|js)$/, '.' + h + '.$1'), hr = rel + '/' + hf;
      fs.copyFileSync(src, path.join(DOCS, hr)); renamed.push([f, hf]);
      fileIdx[hr] = files.length; files.push([hr, TYPE_BY_EXT[path.extname(f).toLowerCase()] || 'application/octet-stream', fs.statSync(src).size]); version += hr;
      continue;
    }
    fs.copyFileSync(src, path.join(DOCS, r));
    if (f === 'index.html') { if (!pages.includes(rel)) pages.push(rel); version += require('crypto').createHash('sha1').update(fs.readFileSync(src)).digest('hex').slice(0, 8) + ':'; }   // content, not size: a move between sections keeps the size
    else { fileIdx[r] = files.length; files.push([r, TYPE_BY_EXT[path.extname(f).toLowerCase()] || 'application/octet-stream', fs.statSync(src).size]); version += r + fs.statSync(src).size; }
  }
})(EXTRA, '');
for (const p of pages) {   // point every page at the hashed names
  const f = path.join(DOCS, p, 'index.html'); if (!renamed.length || !fs.existsSync(f)) continue;
  let h = fs.readFileSync(f, 'utf8'), h0 = h;
  for (const [a, b] of renamed) h = h.split('x/' + a).join('x/' + b);
  if (h !== h0) fs.writeFileSync(f, h);
}
fs.writeFileSync(path.join(DOCS, '.nojekyll'), '');
const crypto = require('crypto');
const body = { pages, files, urls, blocks };
body.version = crypto.createHash('sha1').update(JSON.stringify(body) + version + fs.readFileSync(path.join(SRC, 'sw.js')) + fs.readFileSync(path.join(SRC, 'offline.js'))).digest('hex').slice(0, 12);
fs.writeFileSync(path.join(DOCS, 'm', 'manifest.json'), JSON.stringify({ version: body.version, pages, files, urls, blocks }));
const total = files.reduce((a, f) => a + f[2], 0);
console.log('pages', pages.length, 'files', files.length, 'urls', Object.keys(urls).length, (total / 1e6).toFixed(1) + 'MB', 'version', body.version);
