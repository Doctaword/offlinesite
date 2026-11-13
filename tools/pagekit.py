"""Shared page shell for the features version (docs/features/): its own pages next to the untouched mirror."""
import os, html, json
def esc(s): return html.escape(str(s), quote=True)

NAV = [('Home', 'site/'), ('Professional', 'professional/'), ('Process', 'process/'), ('Direction', 'direction/'), ('Resume', 'resume/')]

def page(path, title, body, depth, active=None, extra_head=''):
    pre = '../' * depth or './'
    nav = ''.join(f"<a href='{pre}{href}'{' class=on' if name == active else ''}>{name}</a>" for name, href in NAV)
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)} | Andrew Dat Tran</title>
<meta name="robots" content="noindex">
<link rel="manifest" href="{pre}manifest.webmanifest">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Andrew Tran"><meta name="theme-color" content="#000000">
<link rel="apple-touch-icon" href="{pre}../icon-180.png"><meta name="ofl-home" content="{pre}site/">
<link rel="stylesheet" href="{pre}x/site.css">{extra_head}
<script defer src="{pre}x/site.js"></script><script defer src="{pre}../offline.js"></script>
</head><body>
<header class="top"><a class="name" href="{pre}site/">Andrew Dat Tran</a><nav>{nav}</nav></header>
<main>{body}</main>
</body></html>"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(doc)

def gallery(imgs, group=''):
    """imgs: [{full, thumb, w, h, cap}] -> justified rows of thumbnails that open in the lightbox."""
    out = "<div class='gal'>"
    for i in imgs:
        r = i['w'] / max(i['h'], 1)
        out += (f"<a class='shot' href='{esc(i['full'])}' data-cap='{esc(i.get('cap', ''))}' style='flex-grow:{r:.3f};flex-basis:{r * 230:.0f}px;aspect-ratio:{i['w']}/{i['h']}'>"
                f"<img loading='lazy' decoding='async' src='{esc(i['thumb'])}' alt='{esc(i.get('cap', ''))}'>"
                + (f"<span>{esc(i['cap'])}</span>" if i.get('cap') else '') + "</a>")
    return out + "</div>"
