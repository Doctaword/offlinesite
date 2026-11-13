"""Re-encodes very large still images (mostly lossless files made from PNGs) as high-quality WebP.
Keeps the same pixel size; cuts file size several times over, so lightboxes open faster and the
whole copy fits comfortably on an iPad. Usage: python3 optimize.py <captureDir>"""
import json, os, sys, io
from multiprocessing import Pool
from PIL import Image
cap = sys.argv[1]; opt = os.path.join(cap, 'opt'); os.makedirs(opt, exist_ok=True)
index = json.load(open(os.path.join(cap, 'index.json')))
def work(item):
    f, size = item; src = os.path.join(cap, 'files', f); dst = os.path.join(opt, f)
    if os.path.exists(dst) or os.path.exists(dst + '.skip'): return 0
    try:
        im = Image.open(src)
        if getattr(im, 'is_animated', False): open(dst + '.skip', 'w').close(); return 0
        im = im.convert('RGBA' if im.mode in ('RGBA', 'LA', 'P') else 'RGB')
        buf = io.BytesIO(); im.save(buf, 'WEBP', quality=90, method=4)
        if buf.tell() < size * 0.8: open(dst, 'wb').write(buf.getvalue()); return size - buf.tell()
        open(dst + '.skip', 'w').close(); return 0
    except Exception as e:
        print('skip', f, e); return 0
if __name__ == '__main__':
    todo = {v['f']: v['size'] for v in index.values() if v['type'].split(';')[0] in ('image/webp', 'image/png', 'image/jpeg') and v['size'] > 400000}
    with Pool(8) as p: saved = sum(p.map(work, todo.items()))
    print('checked', len(todo), 'saved', round(saved / 1e6, 1), 'MB')
