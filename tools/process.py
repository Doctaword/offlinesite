"""Builds the Marvel Puzzle Quest process pages from the working folders on Andrew's PC.

Input : a folder with one sub-folder per character (staged copy of D:\\ART\\03_Personal\\BCS)
Output: ../extra/features/process/  (resized images + pages), picked up by build.js

Every image is sorted into a stage by its file name, then shown in the order the work happened:
references -> sketches -> line -> color flats -> render passes -> feedback rounds -> final deliverables.
Usage: python3 process.py <stagedBcsDir>
"""
import os, re, sys, json, html, hashlib
from multiprocessing import Pool
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
SRC = sys.argv[1]
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'extra', 'features', 'process')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pagekit import page, gallery, esc

NAMES = {'BladeClassic': 'Blade (Classic)', 'Cyclops Hellfire Gala': 'Cyclops (Hellfire Gala)', 'Daken': 'Daken (Pride)', 'Deadpool Taco Truck': 'Deadpool (Taco Truck)',
  'Emma Frost': 'Emma Frost', 'Howard the Duck': 'Howard the Duck', 'KarolinaDean': 'Karolina Dean', 'Man-Ant': 'Man-Ant', 'MantisRocketGroot': 'Mantis, Rocket and Groot',
  'Moonknight': 'Moon Knight', 'Namora': 'Namora', 'Nightcrawler': 'Nightcrawler', 'OmegaCel': 'Omega Red', 'SpiderHam': 'Spider-Ham', 'Spiderman Anti Ock': 'Spider-Man (Anti-Ock Suit)',
  'Spiderman Hornet': 'Spider-Man (Hornet)', 'Sunspot': 'Sunspot', 'Yelena Belova_Thunderbolts': 'Yelena Belova (Thunderbolts)', 'auxitems': 'Event and store art (Doctor Doom, S.H.I.E.L.D. Training)',
  'drax classic': 'Drax (Classic)', 'elektra': 'Elektra', 'hoodedmanwolverine': 'Wolverine (Hooded Man)', 'infamous ironman': 'Doctor Doom (Infamous Iron Man)',
  'mariahillbaronesthor': 'Maria Hill, Baron Zemo and Thor', 'monica': 'Monica Rambeau', 'prowler': 'Prowler', 'psylocke': 'Psylocke', 'silk': 'Silk', 'spiderham 2099': 'Spider-Ham 2099',
  'thing': 'The Thing', 'yellow_jacket': 'Yellowjacket'}
SKIP_DIRS = {'Templates', '_loose', 'psylocke', 'drax classic'}   # psylocke, drax classic: removed at Andrew's request
STAGES = [('ref', 'References', ''),
          ('sketch', 'Sketches and thumbnails', 'Pose and composition options sent for a first pick.'),
          ('line', 'Clean line', 'The chosen poses tightened up for approval before color.'),
          ('flats', 'Color flats', 'Local color and costume read, checked against the character model.'),
          ('render', 'Progress rounds', 'Each numbered version is a round sent for review, from rough to finished render.'),
          ('notes', 'Feedback and notes', 'Art director redlines and my own revision notes between rounds.'),
          ('final', 'Final deliverables', 'The approved poses as delivered to the game.')]
EXT = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.avif')
AI_NAME = re.compile(r'doctaword-.*[0-9a-f]{8}-[0-9a-f]{4}-|chatgpt|midjourney|dall-?e|_elektra_0a07a776', re.I)   # image-generator downloads and unrelated files: never shown

_ov = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'overrides.json')
OV = json.load(open(_ov)) if os.path.exists(_ov) else {'drop_pages': [], 'process': {}}   # Andrew's marks from the review page

def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

def classify(name, rel):
    n = name.lower(); low = '/' + rel.lower().replace('\\', '/')
    dated = re.match(r'(\d{4})-(\d{2})-\d{2}_', n)
    # Andrew joined the project in May 2022: anything older is existing game art he was matching, not his work
    # 'base' = existing game art used as a pose base (never shown); 'ref' = comic and photo reference Andrew gathered (shown)
    if re.search(r'/og/|/poses?/|/mpq shots/', low): return 'base'
    if re.search(r'/ref[^/]*/|/[^/]*ref/|/reference', low): return 'ref'
    if dated and (int(dated.group(1)), int(dated.group(2))) < (2022, 5): return 'base'   # older than his start date: existing game art
    if re.search(r'refs|rejected|_comic-', n): return 'ref'   # reference boards, a comic panel, comic covers
    if re.search(r'feedback|notat|notes|paintover|redline|drawover', n): return 'notes'
    if re.search(r'(^|[-_])refs?([-_.]|\d|$)|reference|screenshot', n): return 'ref'
    if re.search(r'sketch|thumb|rough', n) and not re.search(r'render', n): return 'sketch'
    if re.search(r'cleanline|lineart|[-_]line[-_]|[-_]lines?[-_.]', n): return 'line'
    if re.search(r'flats?[-_.]', n): return 'flats'
    deliverable = re.match(r'(abil|attack|full|fullattack|port|rost|icon|enemy|default)[-_ ]', re.sub(r'^\d{4}-\d{2}-\d{2}_bcs_[^_]+_', '', n))
    if not dated: return 'final' if deliverable else ('render' if re.search(r'workingfile|render', n) else 'ref')
    if deliverable or '/pngs/' in low or '/png/' in low or '/final' in low or '/export' in low: return 'final'
    if re.search(r'render|workingfile|concepttemplate|final|pose|flip|colors?[-_.]|featuredmotd|site|chapterimg|event-|comic-|small', n): return 'render'
    return 'ref'

def label(name):
    n = os.path.splitext(name)[0]
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})_bcs_[^_]+_(.+)_v(\d+)$', n)
    date = ''
    if m:
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        date = f"{months[int(m.group(2)) - 1]} {int(m.group(3))}, {m.group(1)}"; n = m.group(4)
    n = re.sub(r'^mpq-', '', n); n = re.sub(r'concepttemplate-?', '', n); n = re.sub(r'workingfile', '', n)
    n = re.sub(r'[-_]+', ' ', n).strip()
    n = re.sub(r'\bv(\d+)\b', r'version \1', n); n = re.sub(r'\babil ?(\d)', r'ability \1', n, flags=re.I)
    if re.fullmatch(r'[0-9a-f ]{12,}|image( version \d+)?|\d+', n): n = ''
    return (n[:1].upper() + n[1:]) if n else '', date

def convert(job):
    src, dst, long_edge, q = job
    if os.path.exists(dst): 
        with Image.open(dst) as im: return im.size
    try:
        im = Image.open(src)
        if getattr(im, 'is_animated', False): im.seek(0)
        im = im.convert('RGBA' if im.mode in ('RGBA', 'LA', 'P', 'PA') else 'RGB')
        if im.mode == 'RGBA':   # flatten transparency onto the site's dark background
            bg = Image.new('RGB', im.size, (17, 17, 17)); bg.paste(im, mask=im.split()[3]); im = bg
        im.thumbnail((long_edge, long_edge), Image.LANCZOS)
        os.makedirs(os.path.dirname(dst), exist_ok=True); im.save(dst, 'WEBP', quality=q, method=4)
        return im.size
    except Exception as e:
        print('skip', src, e); return None

def main():
    chars = []; jobs = []; skipped_ai = []
    for folder in sorted(os.listdir(SRC), key=str.lower):
        full = os.path.join(SRC, folder)
        if not os.path.isdir(full) or folder in SKIP_DIRS: continue
        cslug = slug(NAMES.get(folder, folder)); items = []; seen = set()
        if cslug in OV['drop_pages']: continue
        ov = OV['process'].get(cslug, {'del': [], 'mv': {}})
        for dp, _, fns in os.walk(full):
            for fn in sorted(fns):
                if not fn.lower().endswith(EXT): continue
                if AI_NAME.search(fn): skipped_ai.append(os.path.join(folder, fn)); continue
                src = os.path.join(dp, fn); rel = os.path.relpath(src, full)
                digest = hashlib.sha1(open(src, 'rb').read()).hexdigest()
                if digest in seen: continue          # exact duplicates are shown once
                seen.add(digest)
                if os.path.getsize(src) < 3000: continue
                key = digest[:12]; lab, date = label(fn)
                stage = classify(fn, rel)
                if key in ov['del']: continue
                stage = ov['mv'].get(key, stage)
                if stage == 'base': continue   # existing game art used as a pose base is not shown
                items.append({'stage': stage, 'label': lab, 'date': date, 'sort': fn.lower(), 'key': key, 'src': src})
                jobs.append((src, os.path.join(OUT, 'img', cslug, key + '.webp'), 2200, 85))
                jobs.append((src, os.path.join(OUT, 'img', cslug, key + '_t.webp'), 560, 78))
        if items: chars.append({'folder': folder, 'name': NAMES.get(folder, folder), 'slug': cslug, 'items': items})
    with Pool(4) as p: sizes = p.map(convert, jobs, chunksize=4)
    keep = {j[1] for j in jobs}          # drop resized copies of anything no longer included
    for dp, _, fns in os.walk(os.path.join(OUT, 'img')):
        for fn in fns:
            if os.path.join(dp, fn) not in keep: os.remove(os.path.join(dp, fn))
    size_of = {j[1]: s for j, s in zip(jobs, sizes)}
    index_cards = []
    PERSONAL = [('spinefall-gate', 'Spinefall Gate'), ('war-cry', 'War Cry'), ('circles-of-sin', 'Circles of Sin')]   # pages built by features.py
    for c in chars:
        sections = []; total = 0; cover = None
        for key, title, blurb in STAGES:
            its = sorted([i for i in c['items'] if i['stage'] == key], key=lambda i: i['sort'])
            imgs = []
            for i in its:
                big = os.path.join(OUT, 'img', c['slug'], i['key'] + '.webp')
                if not size_of.get(big): continue
                w, h = size_of[big]
                cap = ' · '.join(x for x in (i['label'], i['date']) if x)
                imgs.append({'full': f"../img/{c['slug']}/{i['key']}.webp", 'thumb': f"../img/{c['slug']}/{i['key']}_t.webp", 'w': w, 'h': h, 'cap': cap})
            if imgs: sections.append((title, blurb, imgs)); total += len(imgs)
            if imgs and key in ('final', 'render'): cover = cover or imgs[-1]['thumb']
        if not sections or all(t.startswith('References') for t, _, _ in sections): continue
        cover = cover or sections[-1][2][-1]['thumb']
        if OV.get('covers', {}).get(c['slug']): cover = f"../img/{c['slug']}/{OV['covers'][c['slug']]}_t.webp"
        body = f"<p class='crumb'><a href='../'>Process</a></p><h1>{esc(c['name'])}</h1>"
        body += "<nav class='jump'>" + ''.join(f"<a href='#s{n}'>{esc(t)} </a>" for n, (t, b, im) in enumerate(sections)) + "</nav>"
        for n, (t, b, im) in enumerate(sections):
            body += f"<section id='s{n}'><h2>{esc(t)}</h2>{gallery(im, t)}</section>"
        page(os.path.join(OUT, c['slug'], 'index.html'), c['name'] + ' process', body, depth=2, active='Process')
        index_cards.append((c['name'], c['slug'], cover.replace('../', ''), total, [t for t, _, _ in sections]))
    index_cards.sort(key=lambda c: ('Feedback and notes' not in c[4], c[1] != 'doctor-doom-infamous-iron-man', -len(c[4]), -c[3]))   # redlined characters on top, then   # Doctor Doom first (pose and thumbnail options), then the most complete stories
    cards = [('comps', 'Color comps for animation backgrounds', 'cover-comps.webp')] + [(s_, n_, cv) for n_, s_, cv, _, _ in index_cards] + [(s_, n_, f'cover-{s_}.webp') for s_, n_ in PERSONAL]
    order = {s_: n for n, s_ in enumerate(OV.get('card_order', []))}   # Andrew's own ordering from the review page; anything new goes after it
    cards = [c for c in cards if c[0] not in OV['drop_pages']]
    cards.sort(key=lambda c: order.get(c[0], len(order)))
    body = "<h1>Process</h1><p class='note'>Marvel Puzzle Quest. Broken Circle Studios, 505 Games, Marvel. Art direction: Amber Ansdell.</p><div class='cards'>"
    for s_, n_, cv in cards: body += f"<a class='card' href='{s_}/'><img loading='lazy' src='{cv}' alt=''><b>{esc(n_)}</b></a>"
    body += "</div>"
    page(os.path.join(OUT, 'index.html'), 'Process', body, depth=1, active='Process')
    Image.open(os.path.join(OUT, index_cards[0][2])).save(os.path.join(OUT, 'cover.webp'))
    import shutil
    for d in os.listdir(OUT):   # pages of characters no longer included
        if os.path.isdir(os.path.join(OUT, d)) and d not in {c[1] for c in index_cards} | {'img', 'comps'} | {x for x, _ in PERSONAL}: shutil.rmtree(os.path.join(OUT, d))
    for d in os.listdir(os.path.join(OUT, 'img')):
        if d not in {c[1] for c in index_cards}: shutil.rmtree(os.path.join(OUT, 'img', d))
    json.dump({'characters': [(n, s, t) for n, s, _, t, _ in index_cards], 'left_out_generated': skipped_ai}, open(os.path.join(OUT, 'summary.json'), 'w'), indent=1)
    print('characters', len(index_cards), 'images', sum(t for *_, t, _ in index_cards), 'left out (image-generator files):', len(skipped_ai))

if __name__ == '__main__': main()
