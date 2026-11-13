// Local stand-in for GitHub Pages: serves ../docs at http://localhost:8080/offlinesite/
const http = require('http'); const fs = require('fs'); const path = require('path');
const DOCS = path.join(__dirname, '..', 'docs'); const PREFIX = '/offlinesite';
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.mp4': 'video/mp4' };
http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]);
  if (!p.startsWith(PREFIX)) { res.writeHead(404); return res.end('not found'); }
  p = p.slice(PREFIX.length) || '/';
  let f = path.join(DOCS, p);
  if (fs.existsSync(f) && fs.statSync(f).isDirectory()) { if (!p.endsWith('/')) { res.writeHead(301, { Location: PREFIX + p + '/' }); return res.end(); } f = path.join(f, 'index.html'); }
  if (!fs.existsSync(f)) { res.writeHead(404); return res.end('not found'); }
  const size = fs.statSync(f).size; const type = TYPES[path.extname(f)] || 'application/octet-stream';
  const r = /bytes=(\d+)-(\d*)/.exec(req.headers.range || '');
  if (r) { const s = +r[1], e = r[2] ? +r[2] : size - 1; res.writeHead(206, { 'Content-Type': type, 'Content-Range': `bytes ${s}-${e}/${size}`, 'Content-Length': e - s + 1, 'Accept-Ranges': 'bytes' }); return fs.createReadStream(f, { start: s, end: e }).pipe(res); }
  res.writeHead(200, { 'Content-Type': type, 'Content-Length': size, 'Accept-Ranges': 'bytes' }); fs.createReadStream(f).pipe(res);
}).listen(process.env.PORT || 8080, () => console.log('http://localhost:' + (process.env.PORT || 8080) + PREFIX + '/'));
