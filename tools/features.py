#!/usr/bin/env python3
"""Builds the features version (extra/features/): the same portfolio in a faster, simpler shell, reordered,
plus the art direction page, animation color comps and the tailored resume.
Run after build.js has produced docs/ once (it reads the mirrored pages), then run build.js again.
Usage: python3 features.py <stagedUploadsDir>      e.g. /mnt/user-data/uploads
"""
import os, re, sys, hashlib
from multiprocessing import Pool
from PIL import Image, ImageChops
Image.MAX_IMAGE_PIXELS = None
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mirror
from pagekit import page, gallery, esc
from resume_text import resume_body

ROOT = mirror.ROOT
OUT = os.path.join(ROOT, 'extra', 'features')
UP = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/uploads'

# ---------------------------------------------------------------- image plumbing
def _convert(job):
    src, dst, size, q, trim = job
    try:
        if os.path.exists(dst):
            with Image.open(dst) as im: return im.size
        im = Image.open(src)
        im = im.convert('RGBA' if im.mode in ('RGBA', 'LA', 'P') else 'RGB')
        if trim:   # review canvases are small artwork on a huge flat board: crop to the content
            rgb = im.convert('RGB'); bg = Image.new('RGB', rgb.size, rgb.getpixel((2, 2)))
            box = ImageChops.difference(rgb, bg).point(lambda v: 255 if v > 14 else 0).getbbox()
            if box:
                pad = int(max(rgb.size) * 0.015)
                box = (max(0, box[0] - pad), max(0, box[1] - pad), min(rgb.size[0], box[2] + pad), min(rgb.size[1], box[3] + pad))
                if (box[2] - box[0]) * (box[3] - box[1]) < 0.85 * rgb.size[0] * rgb.size[1]: im = im.crop(box)
        im.thumbnail((size, size), Image.LANCZOS)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        im.save(dst, 'WEBP', quality=q, method=4)
        return im.size
    except Exception as e:
        print('skip', src, e); return None

JOBS = []
def mirrored(f, pre):
    """An image already saved by the mirror (docs/m/…): full size is shared, only a thumbnail is added."""
    h = os.path.basename(f).split('.')[0]
    src = os.path.join(mirror.DOCS, f)
    with Image.open(src) as im: w, hgt = im.size
    if f.endswith('.gif'): return {'full': pre + '../' + f, 'thumb': pre + '../' + f, 'w': w, 'h': hgt}
    JOBS.append((src, os.path.join(OUT, 't', h + '.webp'), 640, 80, False))
    return {'full': pre + '../' + f, 'thumb': pre + 't/' + h + '.webp', 'w': w, 'h': hgt}

def staged(src, group, pre, trim=False):
    """A file copied from the PC: resized copy + thumbnail under features/img/<group>/."""
    key = hashlib.sha1(src.encode()).hexdigest()[:12]
    big = os.path.join(OUT, 'img', group, key + '.webp')
    JOBS.append((src, big, 2400, 86, trim)); JOBS.append((src, big.replace('.webp', '_t.webp'), 640, 80, trim))
    return {'full': f'{pre}img/{group}/{key}.webp', 'thumb': f'{pre}img/{group}/{key}_t.webp', '_big': big}

def run_jobs():
    with Pool(4) as p: sizes = p.map(_convert, JOBS, chunksize=2)
    return {j[1]: s for j, s in zip(JOBS, sizes)}

def sized(imgs, size_of):
    out = []
    for i in imgs:
        if '_big' in i:
            s = size_of.get(i['_big'])
            if not s: continue
            i['w'], i['h'] = s
        out.append(i)
    return out

# ---------------------------------------------------------------- portfolio pages (from the mirror)
WORK = [  # mirrored page, slug, title, credit line, group. Order = order on the Professional page:
 # licensed game illustration first (closest to the role), then animation backgrounds, ending on the feature film.
 ('marvel-puzzle-quest', 'marvel-puzzle-quest', 'Marvel Puzzle Quest', 'Illustration. 32 characters, 160+ poses. Broken Circle Studios for 505 Games and Marvel. Art direction: Amber Ansdell.', 'client'),
 ('back-4-blood', 'back-4-blood', 'Back 4 Blood', 'Card illustration. Liquid Development.', 'client'),
 ('halo-master-chief-collection', 'halo', 'Halo: The Master Chief Collection', 'Armor concept art. Liquid Development for 343 Industries. Art direction: Heather Nesheim.', 'client'),
 ('tinytina', 'tiny-tinas-wonderlands', "Tiny Tina's Wonderlands", 'UI icons. Liquid Development.', 'client'),
 ('pantheon-amc', 'pantheon-season-1', 'Pantheon, season 1', 'Background paint. Titmouse. 90 backgrounds painted.', 'client'),
 ('pantheon-season-2', 'pantheon-season-2', 'Pantheon, season 2', 'Background paint. Titmouse. 89 backgrounds painted.', 'client'),
 ('digman-1', 'digman', 'Digman!', 'Background paint. Titmouse for Comedy Central. Art director: Nathan Rico. 131 backgrounds in season 1, 146 in season 2.', 'client'),
 ('the-second-best-hospital-in-the-galaxy-1', 'second-best-hospital', 'The Second Best Hospital in the Galaxy', 'Background paint. Titmouse for Amazon Studios. Art director: Tyler Rice. 200 backgrounds in season 1, 115 in season 2.', 'client'),
 ('metalocalypse-army-of-the-doomstar', 'metalocalypse', 'Metalocalypse: Army of the Doomstar', 'Feature film. Background paint. Titmouse for Adult Swim. Art director: Arthur Tang. 82 backgrounds painted.', 'client'),
]
def professional():
    """All client work on one page, one section per project, in the order set by WORK."""
    out = []
    for src, slug, title, credit, group in WORK:
        if group != 'client': continue
        main = mirror.soup(src).find('main')
        imgs = [mirrored(i['file'], '../') for i in mirror.images(src)]
        paras = [p.get_text(' ', strip=True) for p in main.find_all('p')]
        paras = [p for p in paras if len(p) > 80]
        yt = list(dict.fromkeys(re.findall(r'youtube(?:-nocookie)?\.com/embed/([\w-]+)', str(main))))
        out.append((slug, title, credit, imgs, paras, yt))
    return out

# ---------------------------------------------------------------- animation color comps (Titmouse)
def comps():
    base = os.path.join(UP, 'ART/99_Archive/Duplicates/TITMOUSE DRIVE')
    seen = {}
    for dp, _, fns in os.walk(base):
        for fn in sorted(fns):
            if fn.lower().endswith('.png'): seen.setdefault(fn, os.path.join(dp, fn))
    BRIEF = 'Brief: storyboard and color key'
    # (title, [(file name pattern, caption or None for the automatic one)]) in the order the work happened
    GROUPS = [
      ('Pantheon: Chanda tower balcony, brief to final', [(r'^FOR ANDREW \(4\)', BRIEF), (r'_A159_.*ROUGH', None), (r'^chandatower_notes', 'Notes on the rough'), (r'_A153_.*CLEAN', None)]),
      ('Pantheon: headquarters gates at night', [(r'^FOR ANDREW1', BRIEF), (r'^FOR ANDREW4', BRIEF), (r'_A491_', None), (r'_A558_', None)]),
      ('Pantheon: sporting goods store, rough to clean', [(r'_A065_.*ROUGH', None), (r'_A065_.*CLEAN', None), (r'_A066_.*ROUGH', None), (r'_A066_.*CLEAN', None),
                                                          (r'_A067_.*ROUGH', None), (r'_A067_.*CLEAN', None), (r'_A068_', None), (r'_A076_.*ROUGH', None), (r'_A076_.*GUN_CASE_CLEAN', None)]),
      ('Pantheon: interrogation room', [(r'_A13[356]_.*ROUGH', None), (r'_A134_.*CLEAN', None)]),
      ("Pantheon: Joey's bedroom", [(r'^For Andrew \(6\)', BRIEF), (r'_A037_', None)]),
      ("Pantheon: Maddie's dining room", [(r'^FOR ANDREW \(5\)', BRIEF), (r'_A279_INT_MADDIES', None)]),
      ('Pantheon: night road, three lighting options', [(r'_(A291|A318|A288)_', None)]),
      ('Pantheon: server farm, option A, option B and the approved version', [(r'_A257_', None)]),
      ('Pantheon: office, lights off and on', [(r'_A262_', None)]),
      ('Pantheon: D.C. street pan', [(r'_A231_', None)]),
      ('Pantheon: Utopia city', [(r'^12341', 'Perspective block-in'), (r'_A025_', None), (r'_A639_', None)]),
      ('Digman!: gala ballroom, lighting pass', [(r'_A115_', None)]),
    ]
    def cap(fn):
        n = os.path.splitext(fn)[0]
        stage = 'Color rough' if 'ROUGH' in n else ('Clean paint' if 'CLEAN' in n or 'PAINT' in n else 'Color')
        v = re.search(r'_V0?(\d+)', n, re.I)
        opt = re.search(r'_(red|yellow|light|day|A|B|ON|boards?)$', n)
        optn = {'red': 'red light', 'yellow': 'yellow light', 'light': 'blast light', 'day': 'daylight', 'A': 'option A', 'B': 'option B', 'ON': 'lights on', 'boards': 'over the storyboard', 'board': 'over the storyboard'}
        return ', '.join(x for x in (stage, 'version ' + v.group(1) if v else '', optn[opt.group(1)] if opt else '') if x)
    out = []
    for title, parts in GROUPS:
        imgs = []; used = set()
        for pat, c in parts:
            for fn in sorted(seen, key=lambda f: (0 if 'board' in f.lower() else 1, f)):
                if fn in used or not re.search(pat, fn) or not re.search(r'_(AT|ADT)[_.]|ANDREW|Andrew|chandatower|^12341', fn): continue
                used.add(fn); i = staged(seen[fn], 'comps', '../../'); i['cap'] = c or cap(fn); imgs.append(i)
        out.append((title, '', imgs))
    return out

# ---------------------------------------------------------------- personal pieces with their working files
def personal():
    base = UP
    PAGES = [
      ('spinefall-gate', 'Spinefall Gate', 'Personal worldbuilding project.', 'finalcompfinalv2.png', 'WB sketches/', [
        ('Shape sketches', [('1.png', ''), ('1.1.png', ''), ('wk2.1.png', ''), ('1.1pres.png', 'Chosen silhouettes')]),
        ('Thumbnails', [('0pres.png', ''), ('comps.png', '')]),
        ('3D block-in', [('week3/week3front34.png', ''), ('week3/week3back34.png', ''), ('week3/week3interiorfront.png', ''), ('week3/week3interiorback.png', ''), ('week5/shoebox.png', 'Paintover tests')]),
        ('Exterior', [('week4frontgatesketch.png', 'Sketch over the block-in'), ('week4forwardwip.png', ''), ('week4forward.png', ''), ('week4forwardfinal.png', ''), ('54356.png', ''), ('654874.png', ''), ('week6v3.png', '')]),
        ('Interior', [('backwardv1.png', ''), ('backwardv2.png', ''), ('week4backflatwip.png', ''), ('week4backflatfinal.png', ''), ('121414.png', '')]),
        ('Props and kit', [('heroprop.png', ''), ('kit.png', ''), ('propsheet.png', '')]),
        ('Key frame: the crossing', [('comp1.png', 'First pass'), ('comp1v3.png', ''), ('comp1v5.png', ''), ('comp1v7.png', 'Final values')]),
        ('Key frame: beyond the gate', [('finalcompwip.png', 'Value rough'), ('finalcomp.png', ''), ('finalcompfinal.png', 'Final values'), ('finalcomp2.png', 'Color pass'), ('finalcompfinalv2.png', 'Final')]),
        ('Presentation', [(f'final presentation/JPEG/Hell_Vis_Dev_Final_v4-{n}.jpg', '') for n in range(1, 10)]),
      ]),
      ('war-cry', 'War Cry', 'Personal illustration.', 'warcry/warcry-nightfallmaster.png', 'WB sketches/', [
        ('Sketch', [('warcry/warcrywip00.png', '')]),
        ('Values', [('warcry/warcrywip01.png', ''), ('warcry/warcrywip03.png', ''), ('warcry/warcrywip05.png', ''), ('warcry/warcrywip08.png', ''), ('warcry/warcrywip09.png', '')]),
        ('Color', [('warcry/warcrywip09-3.png', ''), ('warcry/warcrywip09-5.png', ''), ('warcry/warcrywip09-6.png', '')]),
        ('Final', [('warcry/warcry-nightfallmaster.png', '')]),
      ]),
      ('circles-of-sin', 'Circles of Sin', 'Personal character design.', 'wrath/wrath.png', 'trevino/', [
        ('Sketches', [(f'{d}AmdrewTran_Week1_{n}_sketch.png', n) for d, n in (('', 'Pride'), ('', 'Greed'), ('', 'Lust'), ('envy/', 'Envy'), ('', 'Gluttony'), ('wrath/', 'Wrath'), ('sloth/', 'Sloth'))]),
        ('Envy', [('envy/envywip.png', 'Values'), ('envy/envy page.png', 'Painted')]),
        ('Sloth', [('sloth/slothpagewip.png', ''), ('sloth/slothpage.png', 'Painted'), ('sloth/1.png', ''), ('sloth/2.png', ''), ('sloth/3.png', ''), ('sloth/4.png', '')]),
        ('Wrath', [('wrath/wrath.png', 'Painted'), ('534215.webp', 'Final')]),
      ]),
      ('halo-asgardian-warrior', 'Halo: Asgardian Warrior', 'Armor concept. Liquid Development for 343 Industries.', 'bodyclean__revisedbodyv2.png', 'halo-aw/', [
        ('Sketches', [(f'{n} sketch.png', '') for n in 'ABC'] + [(f'IMG_2021030{n}.png', '') for n in ('2_014425__01', '2_014425__012', '3_004153__01__01', '3_215924__01')]
                     + [(f'PNGs__MCC_Asgardian Warrior sketches Feb 28, 2021-{n}.png', '') for n in (1, 2, 3, 4, 5, 6, 8)]),
        ('Rough', [('2021-03-01 - AsgardianWarrior -Rough.png', ''), ('2021-03-01 - AsgardianWarrior -Roughlineup.png', '')]),
        ('Helmets and shoulders', [(f'PNGs__Whiteboard Mar 01, 2021-{n}.png', '') for n in (1, 2)]
                     + [(f'ROUGHS__{n}.png', '') for n in ('odin', 'odinv2', 'valk', 'valkv2', 'antlers', 'longhorn', 'hornsdown', 'spikyshoulder', 'spikev2', 'dragonshoulder', 'dragonshoulderv2', 'wolfclean')]),
        ('First sheet', [('MCC_Asgardian_warrior_master.png', ''), ('MCC_Asgardian_warrior_master_feedback.png', 'Art director feedback')]),
        ('Revisions', [(f'bodyclean__Whiteboard Mar 15, 2021-{n}.png', '') for n in range(1, 6)] + [(f'scans__Whiteboard Mar 16, 2021-{n}.png', '') for n in range(1, 8)]
                     + [(f'scans__Whiteboard Mar 17, 2021-{n}.png', '') for n in range(1, 5)] + [(f'scans__Whiteboard Mar 17, 2021 (1)-{n}.png', '') for n in range(1, 9)]
                     + [('bodyclean__roughcolor.png', ''), ('bodyclean__revisedbody.png', ''), ('bodyclean__revisedbodyv2.png', ''),
                        ('MCC_Asgardian_warrior_master_03-19-21.png', 'Second sheet'), ('MCC_Asgardian_warrior_master_03-19-21v2.png', ''), ('2021-03-19 - VikingWarrior - Revised WIP.png', '')]),
        ('Shoulder round', [('2021-03-23 - VikingWarrior - Revised.png', ''), ('2021-03-25 - VikingWarrior - Revised Shoulder Feedback.png', 'Art director feedback'),
                     ('2021-03-25 - VikingWarrior - Revised Shoulderhelm.png', ''), ('helmsshoulder032621.png', ''), ('2021-03-30 - VikingWarrior - Revisedshouldershelms.png', 'Final')]),
      ]),
    ]
    out = []
    for slug, title, note, cover, pre, secs in PAGES:
        built = []; cov = None
        for t, files in secs:
            imgs = []
            for fn, c in files:
                src = os.path.join(base, pre + fn)
                if not os.path.exists(src): continue
                i = staged(src, 'personal', '../../'); i['cap'] = c; imgs.append(i)
                if fn == cover: cov = i
            built.append((t, imgs))
        out.append((slug, title, note, cov, built))
    return out

# ---------------------------------------------------------------- art direction (LCAD)
def direction():
    L = os.path.join(UP, 'LCAD/0_OLD')
    def ls(rel, pat=r'\.(png|jpe?g)$'):
        d = os.path.join(L, rel)
        return sorted(os.path.join(d, f) for f in os.listdir(d) if re.search(pat, f, re.I) and os.path.isfile(os.path.join(d, f)))
    def wk(f):
        m = re.search(r'week\s*(\d+)', f, re.I); return int(m.group(1)) if m else 99
    def mk(files, cap, trim=True):
        out = []
        for f in files:
            if not os.path.exists(f): print('missing', f); continue
            i = staged(f, 'direction', '../', trim); i['cap'] = cap(f) if callable(cap) else cap; out.append(i)
        return out
    S = []
    cd2 = sorted(ls('CD2/solo'), key=wk) + sorted([f for f in ls('CD2/team') if 'final' not in f], key=wk) + [os.path.join(L, 'CD2/team/final.png')]
    S.append(('briefs', 'Briefs and milestones', 'Character Design 2, one semester. Each board is the brief for that week: what to deliver, how many, and what the next review will look at. '
              'Weeks 1 to 8 are solo work; weeks 9 to 13 are a team project with five milestones, a shared reference sheet and a style guide the team keeps up to date.',
              mk(cd2, lambda f: ('Team project, ' if '/team/' in f else 'Solo, ') + ('final milestone' if 'final' in f else f'week {wk(f)} brief'))))
    other = [('ED241F22/ED241/Week1/demo.png', 'Character Design 1: world brief for the semester'), ('ED241F22/ED241/Week2/demo.hmk.png', 'Character Design 1: party brief and deliverables'),
             ('ED241F22/ED241/Week3/demo.png', 'Character Design 1: archetype, theme and art style brief'), ('ED241F22/ED241/Week4/wordmapdemo.png', 'Character Design 1: word map for finding a direction'),
             ('ED241S23/week2drawovers.png', 'Character Design 1: week 2 deliverables'), ('ED241S23/demolecture.png', 'Character Design 1: prop project brief'),
             ('FD163BS23/lecturedemohmk.png', 'Fundamentals: bedroom project brief, questions the design has to answer'), ('FD163BS23/Week 11/structuredemo.png', 'Fundamentals: three week building project plan'),
             ('Env Design 1/week2demo.png', 'Environment Design 1: research and thumbnail deliverables'), ('Sketching for ED/week4/week4demo.png', 'Sketching: story questions before design'),
             ('Sketching for ED/week12demo.png', 'Sketching: vehicle studies brief'), ('Sketching for ED/week10demolectcrit.png', 'Sketching: skull studies brief'),
             ('Sketching for ED/Week 11/studydemo.png', 'Sketching: study and imagination brief'), ('Sketching for ED/Week 7/demolecture.png', 'Sketching: midterm and organic props brief'),
             ('demo1.png', 'Sketching: perspective homework')]
    S.append(('more-briefs', 'More briefs', 'The same structure across character, environment and fundamentals classes: a clear ask, a count, and the question the design has to answer.',
              mk([os.path.join(L, f) for f, _ in other], lambda f: dict((os.path.join(L, a), b) for a, b in other)[f])))
    S.append(('redlines', 'Redlines', 'Week 2 review of silhouette sketches. Red marks are mine, drawn over each artist’s sheet during the review to show the fix directly: silhouette, proportion, weight and where the eye should land.',
              mk(ls('ED241F22/ED241/Week2/crit'), 'Sketch review with my redlines')))
    rounds = mk(ls('ED241F22/ED241/Week7/Drawovers'), 'Round 1, week 7: drawover') + mk(ls('ED241F22/ED241/Week9/paintovers'), 'Round 2, week 9: paintover') + mk(ls('ED241F22/ED241/Week11/paintovers'), 'Round 3, week 11: paintover')
    S.append(('rounds', 'Three review rounds', 'The same twelve artists at week 7, week 9 and week 11 of a character project. Each canvas holds their reference, their current pass and my drawover or paintover, so the direction given in one round can be checked against the next.', rounds))
    demos = [('Env Design 1/cavedemo.png', 'Environment demo: cave interior'), ('Env Design 1/roomdemo.png', 'Environment demo: room cutaway'), ('Env Design 1/week5/demo.png', 'Environment demo'),
             ('Env Design 1/demowk11.png', 'Environment demo: gate design'), ('Env Design 1/week7demo.png', 'Environment demo: prop and signage set'), ('Env Design 1/demo.png', 'Environment demo: value and proportion'),
             ('FD163BS23/critdemo.png', 'Review demo: interior cutaway'), ('FD163BS23/critdemo2.png', 'Review demo: interior cutaway, second pass'), ('FD163BS23/week12/Emily Alvarez/drawoversdemo.png', 'Drawover demo'),
             ('Dynamic Sketching/week 11/crit.png', 'Review board: sea animals'), ('Dynamic Sketching Thursday/week 11/demo.png', 'Demo: sea animals'), ('Dynamic Sketching Thursday/week 12/demo.png', 'Demo: animals from reference and imagination')]
    S.append(('demos', 'Demos', 'When a note is hard to put into words I paint the answer. These are demos made live during reviews.',
              mk([os.path.join(L, f) for f, _ in demos], lambda f: dict((os.path.join(L, a), b) for a, b in demos)[f])))
    return S

# ---------------------------------------------------------------- assemble
def main():
    pro = professional()
    comp_groups = comps()
    dir_sections = direction()
    pers = personal()
    slides = [mirrored(i['file'], '../') for i in mirror.images('academic')]
    resume_img = mirrored(mirror.images('resume')[0]['file'], '../')
    size_of = run_jobs()

    # professional
    body = ("<h1>Professional work</h1>"
            "<nav class='jump'>" + ''.join(f"<a href='#{s}'>{esc(t)}</a>" for s, t, *_ in pro) + "</nav>")
    for slug, title, credit, imgs, paras, yt in pro:
        body += f"<section id='{slug}'><h2>{esc(title)}</h2><p class='note'>{esc(credit)}</p>"
        if slug == 'marvel-puzzle-quest': body += "<nav class='jump tight'><a href='../process/'>Process</a></nav>"
        body += gallery(imgs)
        body += "</section>"
    page(os.path.join(OUT, 'professional', 'index.html'), 'Professional work', body, depth=1, active='Professional')
    open(os.path.join(OUT, 'index.html'), 'w').write("<!doctype html><meta charset='utf-8'><title>Andrew Dat Tran</title>"
        "<script>location.replace(location.pathname.replace(/\\/?(index\\.html)?$/, '/') + 'site/')</script><noscript><a href='site/'>Open</a></noscript>")

    # color comps
    body = ("<p class='crumb'><a href='../'>Process</a></p>"
            "<p class='note'>Background paint at Titmouse.</p>")
    cover = None
    for n, (t, b, imgs) in enumerate(comp_groups):
        imgs = sized(imgs, size_of)
        if not imgs: continue
        if 'server farm' in t or cover is None: cover = imgs[-1]
        body += f"<section><h2>{esc(t)}</h2>{gallery(imgs)}</section>"
    page(os.path.join(OUT, 'process', 'comps', 'index.html'), 'Color comps', body, depth=2, active='Process')
    Image.open(os.path.join(OUT, cover['thumb'].replace('../../', ''))).save(os.path.join(OUT, 'process', 'cover-comps.webp'))

    # personal pieces
    for slug, title, note, cov, secs in pers:
        body = f"<p class='crumb'><a href='../'>Process</a></p><h1>{esc(title)}</h1><p class='note'>{esc(note)}</p>"
        for t, imgs in secs:
            imgs = sized(imgs, size_of)
            if imgs: body += f"<section><h2>{esc(t)}</h2>{gallery(imgs)}</section>"
        page(os.path.join(OUT, 'process', slug, 'index.html'), title, body, depth=2, active='Process')
        Image.open(os.path.join(OUT, cov['thumb'].replace('../../', ''))).save(os.path.join(OUT, 'process', f'cover-{slug}.webp'))

    # art direction
    body = ("<h1>Art direction</h1><p class='note'>Laguna College of Art + Design, 2022 to present. Student work shown with my marks on top.</p>"
            "<nav class='jump'><a href='#team'>Team project</a>" + ''.join(f"<a href='#{k}'>{esc(t)}</a>" for k, t, _, _ in dir_sections) + "</nav>"
            "<section id='team'><h2>Team project</h2>" + gallery(slides) + "</section>")
    dcover = None
    for k, t, b, imgs in dir_sections:
        imgs = sized(imgs, size_of)
        if k == 'redlines' and imgs: dcover = imgs[0]
        body += f"<section id='{k}'><h2>{esc(t)}</h2>{gallery(imgs)}</section>"
    page(os.path.join(OUT, 'direction', 'index.html'), 'Art direction', body, depth=1, active='Direction')
    Image.open(os.path.join(OUT, dcover['thumb'].replace('../', ''))).save(os.path.join(OUT, 'direction', 'cover.webp'))

    # resume
    page(os.path.join(OUT, 'resume', 'index.html'), 'Resume', resume_body(resume_img, gallery), depth=1, active='Resume')

    # drop images no longer referenced
    keep = {j[1] for j in JOBS}
    for sub in ('t', 'img/comps', 'img/direction', 'img/personal'):
        d = os.path.join(OUT, sub)
        for f in os.listdir(d) if os.path.isdir(d) else []:
            if os.path.join(d, f) not in keep: os.remove(os.path.join(d, f))
    print('professional', sum(len(x[3]) for x in pro), 'comps', sum(len(g[2]) for g in comp_groups), 'direction', sum(len(s[3]) for s in dir_sections))

if __name__ == '__main__': main()
