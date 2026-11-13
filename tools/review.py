"""Builds the data for the keep-or-delete review page from the features pages in extra/features/.
Every image and text block gets a stable id, so marks made on the review page can be applied by the generators.
Usage: python3 review.py <outDir>   -> <outDir>/data.json and <outDir>/s/<n>.jpg (thumbnail sheets)
"""
import os, sys, re, json, hashlib, time
from bs4 import BeautifulSoup
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX = os.path.join(ROOT, 'extra', 'features'); OUT = sys.argv[1]
STAMP = format(int(time.time()), 'x')   # new sheet names each run, so a cached old sheet is never paired with new data
CELL = 260; COLS = 6; PER = 48

def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
def tid(s): return 't' + hashlib.md5(s.encode()).hexdigest()[:10]

def find(page_dir, src):
    p = os.path.normpath(os.path.join(page_dir, src))
    if os.path.exists(p): return p
    p2 = p.replace(os.path.join(ROOT, 'extra'), os.path.join(ROOT, 'docs'))
    return p2 if os.path.exists(p2) else None

def parse(rel, group):
    d = os.path.join(FX, rel); soup = BeautifulSoup(open(os.path.join(d, 'index.html')).read(), 'html.parser')
    main = soup.find('main'); title = (main.find('h1').get_text(' ', strip=True) if main.find('h1') else rel)
    secs = [{'id': 'top', 'title': 'Top of page', 'items': []}]; seen = set()
    def add(it):
        if it['id'] in seen: return
        seen.add(it['id']); secs[-1]['items'].append(it)
    for el in main.find_all(True):
        cls = el.get('class') or []
        if el.find_parent('nav') or el.name == 'nav' or 'crumb' in cls or el.find_parent(class_='crumb'): continue
        if el.name == 'h2':
            t = el.get_text(' ', strip=True); sid = slug(t); n = 2
            while any(s['id'] == sid for s in secs): sid = f"{slug(t)}-{n}"; n += 1
            secs.append({'id': sid, 'title': t, 'items': []})
            add({'id': tid('h2' + t), 'k': 't', 'text': t, 'role': 'heading'})
        elif el.name == 'a' and ('shot' in cls or 'card' in cls):
            img = el.find('img'); f = find(d, img['src']) if img else None
            if not f: continue
            iid = os.path.splitext(os.path.basename(el['href'].rstrip('/')))[0] if 'shot' in cls else 'card-' + slug(el['href'])
            cap = el.get('data-cap') or (el.find('b').get_text(strip=True) if el.find('b') else '')
            add({'id': iid, 'k': 'i', 'cap': cap, 'f': f})
        elif el.name == 'img' and not el.find_parent('a'):
            f = find(d, el['src'])
            if f: add({'id': 'img-' + slug(os.path.basename(el['src'])), 'k': 'i', 'cap': el.get('alt', ''), 'f': f})
        elif el.name in ('h1', 'p', 'li') or 'jh' in cls:
            if el.find_parent('a') or (el.name == 'p' and el.find_parent(class_='jh')): continue
            t = el.get_text(' ', strip=True)
            if t: add({'id': tid(el.name + t), 'k': 't', 'text': t, 'role': 'title' if el.name == 'h1' else 'text'})
    secs = [s for s in secs if s['items']]
    return {'id': rel.strip('/').replace('/', '.'), 'group': group, 'title': title, 'secs': secs}

def main():
    pages = [parse('professional', 'Professional'), parse('process', 'Process')]
    order = re.findall(r"class='card' href='([^']+)/'", open(os.path.join(FX, 'process', 'index.html')).read())
    pages += [parse('process/' + s, 'Process') for s in order]
    pages += [parse('direction', 'Direction'), parse('resume', 'Resume')]
    os.makedirs(os.path.join(OUT, 's'), exist_ok=True)
    before = set(os.listdir(os.path.join(OUT, 's'))); now = set(); nimg = 0
    # one or more sheets per page, named by what they hold, so an unchanged page keeps its sheets between runs
    for p in pages:
        imgs = [it for s in p['secs'] for it in s['items'] if it['k'] == 'i']; nimg += len(imgs)
        for n in range(0, len(imgs), PER):
            chunk = imgs[n:n + PER]; rows = (len(chunk) + COLS - 1) // COLS
            name = hashlib.md5(('|'.join(it['id'] + str(os.path.getsize(it['f'])) for it in chunk)).encode()).hexdigest()[:12]
            now.add(name + '.jpg'); path = os.path.join(OUT, 's', name + '.jpg')
            sheet = None if os.path.exists(path) else Image.new('RGB', (COLS * CELL, rows * CELL), '#0c0c0d')
            for i, it in enumerate(chunk):
                f = it.pop('f'); it['s'] = [name, i % COLS, i // COLS, rows]
                if sheet is None: continue
                im = Image.open(f).convert('RGB'); im.thumbnail((CELL, CELL))
                sheet.paste(im, ((i % COLS) * CELL + (CELL - im.width) // 2, (i // COLS) * CELL + (CELL - im.height) // 2))
            if sheet is not None: sheet.save(path, quality=74)
    for f in before - now: os.remove(os.path.join(OUT, 's', f))
    delta = {'s/' + f: 's/' + f for f in sorted(now - before)}; delta.update({'s/' + f: None for f in sorted(before - now)}); delta['data.json'] = 'data.json'
    json.dump(delta, open(os.path.join(OUT, 'delta.json'), 'w'))
    imgs = [0] * nimg
    json.dump({'cols': COLS, 'pages': pages}, open(os.path.join(OUT, 'data.json'), 'w'), separators=(',', ':'))
    print('pages', len(pages), 'images', len(imgs), 'text', sum(1 for p in pages for s in p['secs'] for it in s['items'] if it['k'] == 't'), 'sheets', len(now), 'new', len(now - before))

main()
