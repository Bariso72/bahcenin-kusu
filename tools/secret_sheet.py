import sys, json
from PIL import Image, ImageDraw
src, spec, out = sys.argv[1], sys.argv[2], sys.argv[3]
S = json.load(open(spec)); im = Image.open(src)
cell, cols = 150, 8; rows = (len(S)+cols-1)//cols
sheet = Image.new('RGB', (cols*cell, rows*(cell+14)), (30,30,30)); d = ImageDraw.Draw(sheet)
for i, s in enumerate(S):
    r = s.get('r', 60); c = im.crop((s['x']-r, s['y']-r, s['x']+r, s['y']+r)).resize((cell-4, cell-4))
    dc = ImageDraw.Draw(c); dc.ellipse((cell/2-8, cell/2-8, cell/2+4, cell/2+4), outline=(255,0,255), width=2)
    x, y = (i%cols)*cell, (i//cols)*(cell+14)
    sheet.paste(c, (x+2, y+14)); d.text((x+2, y+1), f"{i} {s['id']}", fill=(255,255,0))
sheet.save(out, quality=85)
