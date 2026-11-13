"""Folds marks from the keep-or-delete review page into tools/overrides.json, which process.py reads.
Usage: python3 apply_marks.py <dir of marks/*.json exported from the review page's database>"""
import os, sys, json, glob
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, 'overrides.json')
STAGE = {'references': 'ref', 'sketches-and-thumbnails': 'sketch', 'clean-line': 'line', 'color-flats': 'flats', 'progress-rounds': 'render', 'feedback-and-notes': 'notes', 'final-deliverables': 'final'}
ov = json.load(open(P)) if os.path.exists(P) else {'drop_pages': [], 'process': {}, 'other': {}}
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.json'))):
    pid = os.path.basename(f)[:-5]; m = json.load(open(f)); m = m.get('data', m)
    dl = m.get('del', []); mv = m.get('mv', {})
    if pid == 'process':
        ov['drop_pages'] = sorted(set(ov['drop_pages']) | {d[5:] for d in dl if d.startswith('card-')})
    elif pid.startswith('process.') and pid != 'process.comps':
        o = ov['process'].setdefault(pid[8:], {'del': [], 'mv': {}})
        o['del'] = sorted(set(o['del']) | set(dl))
        o['mv'].update({k: STAGE[v] for k, v in mv.items() if v in STAGE and k not in o['del']})
    elif dl or mv:
        o = ov['other'].setdefault(pid, {'del': [], 'mv': {}}); o['del'] = sorted(set(o['del']) | set(dl)); o['mv'].update(mv)
ov['process'] = {k: v for k, v in ov['process'].items() if v['del'] or v['mv']}
json.dump(ov, open(P, 'w'), indent=1)
print('drop', ov['drop_pages'], 'process pages with marks', len(ov['process']), 'other', list(ov['other']))
