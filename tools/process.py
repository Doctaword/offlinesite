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
SKIP_DIRS = {'Templates', '_loose'}
STAGES = [('ref', 'References and existing game art', 'Material I worked from, not my art: comic sources, costume details, in-game screenshots and earlier assets I had to match.'),
          ('sketch', 'Sketches and thumbnails', 'Pose and composition options sent for a first pick.'),
          ('line', 'Clean line', 'The chosen poses tightened up for approval before color.'),
          ('flats', 'Color flats', 'Local color and costume read, checked against the character model.'),
          ('render', 'Progress rounds', 'Each numbered version is a round sent for review, from rough to finished render.'),
          ('notes', 'Feedback and notes', 'Art director redlines and my own revision notes between rounds.'),
          ('final', 'Final deliverables', 'The approved poses as delivered to the game.')]
EXT = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.avif')
AI_NAME = re.compile(r'doctaword-.*[0-9a-f]{8}-[0-9a-f]{4}-|chatgpt|midjourney|dall-?e|_elektra_0a07a776', re.I)   # image-generator downloads and unrelated files: never shown

def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

def classify(name, rel):
    n = name.lower(); low = '/' + rel.lower().replace('\\', '/')
    dated = re.match(r'(\d{4})-(\d{2})-\d{2}_', n)
    # Andrew joined the project in May 2022: anything older is existing game art he was matching, not his work
    if dated and (int(dated.group(1)), int(dated.group(2))) < (2022, 5): return 'ref'
    if re.search(r'/og/|/ref[^/]*/|/mpq shots/|/reference', low): return 'ref'
    if re.search(r'feedback|notat|notes|rejected|paintover|redline|drawover', n): return 'notes'
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
                items.append({'stage': classify(fn, rel), 'label': lab, 'date': date, 'sort': fn.lower(), 'key': key, 'src': src})
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
        body = f"<p class='crumb'><a href='../'>Process</a></p><h1>{esc(c['name'])}</h1>"
        body += f"<p class='lede'>{total} working files, in the order the work happened. Tap any image to open it, then swipe.</p>"
        body += "<nav class='jump'>" + ''.join(f"<a href='#s{n}'>{esc(t)} <span>{len(im)}</span></a>" for n, (t, b, im) in enumerate(sections)) + "</nav>"
        for n, (t, b, im) in enumerate(sections):
            body += f"<section id='s{n}'><h2>{esc(t)}</h2><p class='note'>{esc(b)}</p>{gallery(im, t)}</section>"
        page(os.path.join(OUT, c['slug'], 'index.html'), c['name'] + ' process', body, depth=2, active='Process')
        index_cards.append((c['name'], c['slug'], cover.replace('../', ''), total, [t for t, _, _ in sections]))
    index_cards.sort(key=lambda c: (c[1] != 'doctor-doom-infamous-iron-man', -len(c[4]), -c[3]))   # Doctor Doom first (pose and thumbnail options), then the most complete stories
    body = "<h1>Process: from reference to final</h1><p class='lede'>Marvel Puzzle Quest, illustration for Broken Circle Studios, 505 Games and Marvel. Art direction: Amber Ansdell. " \
           "Each character below keeps every stage I sent for review: references, sketches and pose options, clean line, color flats, render rounds, feedback and the final poses.</p><div class='cards'>" \
           "<a class='card' href='comps/'><img loading='lazy' src='cover-comps.webp' alt=''><b>Color comps for animation backgrounds</b><span>Pantheon and Digman!: lighting options, rough to clean</span></a>"
    for name, s, cover, total, stages in index_cards:
        body += f"<a class='card' href='{s}/'><img loading='lazy' src='{cover}' alt=''><b>{esc(name)}</b><span>{total} files · {len(stages)} stages</span></a>"
    body += "</div>"
    page(os.path.join(OUT, 'index.html'), 'Process', body, depth=1, active='Process')
    Image.open(os.path.join(OUT, index_cards[0][2])).save(os.path.join(OUT, 'cover.webp'))
    import shutil
    for d in os.listdir(os.path.join(OUT, 'img')):
        if d not in {c[1] for c in index_cards}: shutil.rmtree(os.path.join(OUT, 'img', d))
    json.dump({'characters': [(n, s, t) for n, s, _, t, _ in index_cards], 'left_out_generated': skipped_ai}, open(os.path.join(OUT, 'summary.json'), 'w'), indent=1)
    print('characters', len(index_cards), 'images', sum(t for *_, t, _ in index_cards), 'left out (image-generator files):', len(skipped_ai))

if __name__ == '__main__': main()
