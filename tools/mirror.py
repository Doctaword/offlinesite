"""Reads the mirrored pages in docs/: which images each page shows and which saved file holds each one."""
import os, re, json
from bs4 import BeautifulSoup
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DOCS = os.path.join(ROOT, 'docs')
_m = json.load(open(os.path.join(DOCS, 'm', 'manifest.json')))
_by_path = {}
for k, idx in _m['urls'].items():
    base, _, q = k.partition('?')
    _by_path.setdefault(base, []).append((q, idx))

def saved_file(url):
    """Largest saved rendition of an image URL -> path under docs (m/…), or None."""
    k = re.sub(r'^(https?:)?//', '', url).partition('?')[0]
    best = None
    for q, idx in _by_path.get(k, []):
        f = _m['files'][idx]
        if not f[1].startswith('image/'): continue
        if best is None or f[2] > best[2]: best = f
    return best[0] if best else None

def soup(page):
    return BeautifulSoup(open(os.path.join(DOCS, page, 'index.html')).read(), 'html.parser')

def images(page):
    main = soup(page).find('main')
    out, seen = [], set()
    for i in main.find_all('img'):
        u = i.get('data-src') or i.get('src') or ''
        f = saved_file(u)
        if not f or f in seen: continue
        seen.add(f); out.append({'file': f, 'alt': i.get('alt') or '', 'url': u})
    return out
