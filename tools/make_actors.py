"""Actors for code-driven behaviours + 'cover' patches that hide the original spot
(filled by diffusion inpainting from the surrounding paint) when an actor moves away.
Usage: python3 -I tools/make_actors.py garden.jpg OUTDIR SHEET
"""
import sys, json
import numpy as np
from PIL import Image, ImageDraw

src, outdir, sheet_path = sys.argv[1], sys.argv[2], sys.argv[3]
A = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
rng = np.random.default_rng(7)

# name, actor rect (x0,y0,x1,y1), pivot (world), needs cover, feather edge
ACT = [
    ('zurafa_boyun', (546, 516, 598, 610), (579, 606), True, 0.30),
    ('baykus_ucan', (902, 1044, 964, 1154), (933, 1150), True, 0.22),
    ('saka_kus', (1138, 922, 1228, 1038), (1180, 1034), True, 0.22),
    ('antilop', (536, 418, 590, 458), (563, 456), True, 0.30),
    ('armadillo', (638, 468, 718, 512), (678, 510), True, 0.28),
    ('cift_kadin', (1096, 1088, 1128, 1150), (1110, 1146), False, 0.35),
    ('cift_erkek', (1074, 1100, 1102, 1150), (1090, 1146), False, 0.35),
    ('havuz_kadin1', (1548, 704, 1612, 768), (1580, 766), False, 0.35),
]

def feather(h, w, edge):
    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx + 0.5) / w * 2 - 1; ny = (yy + 0.5) / h * 2 - 1
    d = np.sqrt(nx ** 2 + ny ** 2)
    return np.clip((1 - d) / edge, 0, 1) ** 1.5

def inpaint(region, hole):
    """Diffuse surrounding colours into the hole (coarse-to-fine), then add paint grain."""
    out = region.copy()
    known = ~hole
    ring = out[known & (np.roll(hole, 3, 0) | np.roll(hole, -3, 0) | np.roll(hole, 3, 1) | np.roll(hole, -3, 1))]
    fill = ring.mean(0) if len(ring) else out[known].mean(0)
    out[hole] = fill
    for it in range(900):
        avg = (np.roll(out, 1, 0) + np.roll(out, -1, 0) + np.roll(out, 1, 1) + np.roll(out, -1, 1)) / 4
        out[hole] = avg[hole]
    grain = rng.normal(0, 5, out.shape[:2])[..., None]
    out[hole] = np.clip(out[hole] + grain[hole], 0, 255)
    return out

items = []
for name, (x0, y0, x1, y1), (px, py), cover, edge in ACT:
    w, h = x1 - x0, y1 - y0
    rgb = A[y0:y1, x0:x1]
    a = (feather(h, w, edge) * 255).astype(np.uint8)
    items.append(dict(n=name, role='actor', x=x0, y=y0, w=w, h=h, px=px, py=py,
                      img=Image.fromarray(np.dstack([rgb.astype(np.uint8), a]), 'RGBA')))
    if cover:
        m = 10  # margin of real paint around the hole for the diffusion to draw from
        cx0, cy0, cx1, cy1 = x0 - m, y0 - m, x1 + m, y1 + m
        reg = A[cy0:cy1, cx0:cx1].copy()
        H2, W2 = reg.shape[:2]
        hole = feather(H2 - 2 * m + 8, W2 - 2 * m + 8, 0.5) > 0.02
        full = np.zeros((H2, W2), bool); full[m - 4:m - 4 + hole.shape[0], m - 4:m - 4 + hole.shape[1]] = hole
        filled = inpaint(reg, full)
        ca = (np.clip(feather(H2, W2, 0.35) * 1.15, 0, 1) * 255).astype(np.uint8)
        items.append(dict(n=name + '_ort', role='cover', x=cx0, y=cy0, w=W2, h=H2, px=px, py=py,
                          img=Image.fromarray(np.dstack([filled.astype(np.uint8), ca]), 'RGBA')))

AW, x, y, rowh = 1024, 0, 0, 0
for it in sorted(items, key=lambda t: -t['h']):
    if x + it['w'] > AW: x, y, rowh = 0, y + rowh + 2, 0
    it['ax'], it['ay'] = x, y; x += it['w'] + 2; rowh = max(rowh, it['h'])
atlas = Image.new('RGBA', (AW, y + rowh), (0, 0, 0, 0))
for it in items: atlas.paste(it['img'], (it['ax'], it['ay']))
atlas.save(f'{outdir}/actors.webp', 'WEBP', quality=85, method=6)
json.dump([{k: v for k, v in it.items() if k != 'img'} for it in items], open(f'{outdir}/actors.json', 'w'), separators=(',', ':'))

# contact sheet: actor | cover | cover pasted over the painting (what the viewer sees when the actor leaves)
rows = [it for it in items if it['role'] == 'actor']
sheet = Image.new('RGB', (3 * 200, len(rows) * 180), (40, 40, 40)); d = ImageDraw.Draw(sheet)
base = Image.open(src).convert('RGBA')
for r, act in enumerate(rows):
    def put(im, col):
        s = min(180 / im.width, 165 / im.height); im2 = im.resize((int(im.width * s), int(im.height * s)))
        bg = Image.new('RGBA', im2.size, (255, 0, 255, 255)); bg.alpha_composite(im2)
        sheet.paste(bg.convert('RGB'), (col * 200 + 4, r * 180 + 12))
    put(act['img'], 0)
    cov = next((c for c in items if c['n'] == act['n'] + '_ort'), None)
    if cov:
        put(cov['img'], 1)
        crop = base.crop((cov['x'], cov['y'], cov['x'] + cov['w'], cov['y'] + cov['h'])); crop.alpha_composite(cov['img'])
        put(crop, 2)
    d.text((4, r * 180), act['n'], fill=(255, 255, 0))
sheet.save(sheet_path, quality=85)
import os
print(len(items), 'parca', atlas.size, os.path.getsize(f'{outdir}/actors.webp'), 'bayt')
