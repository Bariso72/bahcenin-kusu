"""Cut feathered patches (creatures, water, fire) out of garden.jpg into one atlas.
Outputs: anim.webp (RGBA atlas) and anim.json (patch list), plus a contact sheet.
Usage: python3 -I tools/make_anim.py garden.jpg OUTDIR SHEET
"""
import sys, json
import numpy as np
from PIL import Image, ImageDraw

src, outdir, sheet_path = sys.argv[1], sys.argv[2], sys.argv[3]
IM = Image.open(src).convert('RGB')
A = np.asarray(IM).astype(np.float32)

# kind: sway (tilt from feet), bob (breathe/bob), gallop (bouncing, wave delay), fly, swim, water, fire
P = []
def add(name, cx, cy, hw, hh, kind):
    P.append(dict(n=name, cx=cx, cy=cy, hw=hw, hh=hh, k=kind))

# ---- Eden ----
add('fil', 316, 532, 64, 42, 'sway')
add('zurafa', 578, 594, 42, 90, 'sway')
add('tekboynuz', 196, 630, 58, 53, 'bob')
add('ayi', 482, 556, 20, 26, 'bob')
add('domuz', 678, 489, 34, 20, 'bob')
add('kirpi', 638, 522, 24, 18, 'bob')
add('antiloplar', 584, 432, 44, 18, 'gallop')
add('beyazkuslar', 216, 464, 76, 26, 'bob')
add('gokkuslari', 220, 204, 80, 64, 'fly')
# ---- Garden ----
add('grifon', 1005, 215, 62, 42, 'fly')
add('ucan2', 2245, 225, 55, 45, 'fly')
for i, x in enumerate(range(1290, 2050, 68)):
    add(f'atli_arka{i}', x, 652, 36, 50, 'gallop')
for i, x in enumerate(range(1260, 2080, 72)):
    add(f'atli_on{i}', x, 892, 38, 42, 'gallop')
add('atli_sol', 1228, 765, 45, 70, 'gallop')
add('atli_sag', 2035, 765, 45, 70, 'gallop')
add('denizkizi2', 1355, 535, 40, 20, 'swim')
add('yalicapkini', 965, 1010, 48, 62, 'sway')
add('saka', 1190, 960, 50, 45, 'sway')
add('ibibik', 1085, 890, 45, 40, 'sway')
add('ordek3', 1133, 1057, 40, 22, 'swim')
add('baykus1', 935, 1085, 35, 40, 'bob')
add('baykus2', 2195, 1050, 34, 42, 'bob')
add('baskakus', 1511, 1166, 30, 20, 'bob')
add('buyukbalik', 1480, 1565, 80, 28, 'swim')
add('balik', 1780, 1192, 40, 25, 'swim')
# ---- Hell ----
add('prens', 3010, 1000, 60, 95, 'bob')
add('kulaklar', 2650, 555, 88, 62, 'gallop')
add('patenciler', 2930, 985, 65, 42, 'bob')
add('canavar', 2830, 1450, 62, 42, 'bob')
add('sovalye', 2920, 1540, 50, 52, 'bob')
add('tavsan', 2705, 1310, 42, 52, 'bob')
# ---- Water (masked by blueness) ----
add('su_cennet', 468, 764, 152, 68, 'water')
add('su_cennet_sol', 212, 684, 112, 72, 'water')
add('su_irmak', 1630, 480, 690, 62, 'water')
add('su_havuz', 1640, 740, 200, 45, 'water')
add('su_alt', 1270, 1090, 330, 90, 'water')
add('su_cehennem', 2950, 940, 170, 60, 'water')
# ---- Fire (masked by orange/bright) ----
add('ates_ust', 2810, 330, 330, 280, 'fire')
add('ates_sol', 2575, 560, 85, 65, 'fire')

def feather(h, w, edge=0.35):
    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx + 0.5) / w * 2 - 1
    ny = (yy + 0.5) / h * 2 - 1
    d = np.sqrt(nx**2 + ny**2)
    return np.clip((1 - d) / edge, 0, 1) ** 1.5

def box_blur(m, r):
    if r <= 0: return m
    k = 2 * r + 1
    p = np.pad(m, r, mode='edge')
    c = p.cumsum(0); c = np.vstack([np.zeros((1, c.shape[1])), c]); m2 = (c[k:] - c[:-k]) / k
    c = m2.cumsum(1); c = np.hstack([np.zeros((c.shape[0], 1)), c]); return (c[:, k:] - c[:, :-k]) / k

patches = []
for p in P:
    x0, y0 = int(p['cx'] - p['hw']), int(p['cy'] - p['hh'])
    x1, y1 = int(p['cx'] + p['hw']), int(p['cy'] + p['hh'])
    rgb = A[y0:y1, x0:x1].copy()
    h, w = rgb.shape[:2]
    if p['k'] == 'water':
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        m = np.clip((b - np.maximum(r, g * 0.85)) / 22, 0, 1) * np.clip((b - 60) / 40, 0, 1)
        m = box_blur(m, 3) * feather(h, w, 0.12)
        # brighten slightly so the shimmer reads as light on water
        rgb = np.clip(rgb * 1.12 + 10, 0, 255)
    elif p['k'] == 'fire':
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        warm = np.clip((r - b * 1.2 - 20) / 45, 0, 1) * np.clip((r - 90) / 50, 0, 1)
        m = box_blur(warm, 6) * 1.4
        m = np.clip(m, 0, 1) * feather(h, w, 0.15)
        rgb = np.clip(rgb * np.array([1.7, 1.35, 0.9]) + np.array([40, 15, 0]), 0, 255)
    else:
        m = feather(h, w, 0.38)
    alpha = (np.clip(m, 0, 1) * 255).astype(np.uint8)
    img = Image.fromarray(np.dstack([rgb.astype(np.uint8), alpha]), 'RGBA')
    patches.append((p, (x0, y0, w, h), img))

# shelf pack, max width 2048
patches.sort(key=lambda t: -t[1][3])
AW, x, y, rowh, pos = 2048, 0, 0, 0, []
for p, (x0, y0, w, h), img in patches:
    if x + w > AW: x, y, rowh = 0, y + rowh + 2, 0
    pos.append((p, (x0, y0, w, h), img, (x, y)))
    x += w + 2; rowh = max(rowh, h)
AH = y + rowh
atlas = Image.new('RGBA', (AW, AH), (0, 0, 0, 0))
out = []
for p, (x0, y0, w, h), img, (ax, ay) in pos:
    atlas.paste(img, (ax, ay))
    out.append(dict(n=p['n'], k=p['k'], x=x0, y=y0, w=w, h=h, ax=ax, ay=ay))
atlas.save(f'{outdir}/anim.webp', 'WEBP', quality=82, method=6)
json.dump(dict(aw=AW, ah=AH, p=out), open(f'{outdir}/anim.json', 'w'), separators=(',', ':'))

# contact sheet: each creature patch on a checkerboard with its name
cre = [t for t in pos if t[0]['k'] not in ('water', 'fire')]
sel = [t for t in pos if t[0]['k'] in ('water', 'fire')]
cell, cols = 150, 9
rows = (len(cre) + cols - 1) // cols
sheet = Image.new('RGB', (cols * cell, rows * (cell + 20) + 380), (40, 40, 40))
d = ImageDraw.Draw(sheet)
for i, (p, (x0, y0, w, h), img, _) in enumerate(cre):
    cx, cy = (i % cols) * cell, (i // cols) * (cell + 20)
    s = min((cell - 6) / w, (cell - 6) / h)
    im2 = img.resize((max(1, int(w * s)), max(1, int(h * s))))
    bg = Image.new('RGBA', im2.size, (255, 0, 255, 255)); bg.alpha_composite(im2)
    sheet.paste(bg.convert('RGB'), (cx + 3, cy + 16))
    d.text((cx + 3, cy + 2), p['n'], fill=(255, 255, 0))
yb = rows * (cell + 20) + 4; xb = 0
for p, (x0, y0, w, h), img, _ in sel:
    s = min(360 / w, 180 / h)
    im2 = img.resize((max(1, int(w * s)), max(1, int(h * s))))
    bg = Image.new('RGBA', im2.size, (255, 0, 255, 255)); bg.alpha_composite(im2)
    if xb + im2.width > sheet.width: xb, yb = 0, yb + 190
    sheet.paste(bg.convert('RGB'), (xb, yb)); d.text((xb + 2, yb + 2), p['n'], fill=(255, 255, 0)); xb += im2.width + 6
sheet.save(sheet_path, quality=80)
import os
print('patches', len(out), 'atlas', AW, AH, 'bytes', os.path.getsize(f'{outdir}/anim.webp'))
