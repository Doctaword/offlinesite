"""Applies review-page marks (tools/overrides.json, "other") to the generated features pages that are not built by process.py.
Run after features.py. Removes marked images and text, moves images between sections, drops sections left empty."""
import os, re, json, hashlib
from bs4 import BeautifulSoup
HERE = os.path.dirname(os.path.abspath(__file__)); FX = os.path.join(HERE, '..', 'extra', 'features')
def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
def tid(s): return 't' + hashlib.md5(s.encode()).hexdigest()[:10]
ov = json.load(open(os.path.join(HERE, 'overrides.json'))).get('other', {})
for pid, o in ov.items():
    f = os.path.join(FX, pid.replace('.', '/'), 'index.html')
    if not os.path.exists(f): continue
    soup = BeautifulSoup(open(f).read(), 'html.parser'); main = soup.find('main'); dl = set(o['del']); n = 0
    secs = {slug(s.find('h2').get_text(' ', strip=True)): s for s in main.find_all('section') if s.find('h2')}
    for a in main.select('a.shot'):
        iid = os.path.splitext(os.path.basename(a['href']))[0]
        if iid in dl: a.decompose(); n += 1
        elif o['mv'].get(iid) in secs and secs[o['mv'][iid]].find(class_='gal'): secs[o['mv'][iid]].find(class_='gal').append(a.extract()); n += 1
    for el in main.find_all(['h1', 'h2', 'p', 'li']):
        if el.find_parent('nav') or 'crumb' in (el.get('class') or []): continue
        t = el.get_text(' ', strip=True)
        if t and (tid(el.name + t) in dl or tid('h2' + t) in dl and el.name == 'h2'): el.decompose(); n += 1
    for s in main.find_all('section'):
        if not s.select('a.shot') and not s.find(['p', 'li']):
            sid = s.get('id'); s.decompose()
            if sid:
                for a in main.select(f"nav a[href='#{sid}']"): a.decompose()
    open(f, 'w').write(str(soup)); print(pid, 'changes', n)
