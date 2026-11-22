import sys
from PIL import Image, ImageDraw
src=sys.argv[1]; out=sys.argv[2]; specs=sys.argv[3:]
tiles=[]
for s in specs:
    name,x0,y0,x1,y1=s.split(',');x0,y0,x1,y1=map(int,(x0,y0,x1,y1))
    im=Image.open(src).crop((x0,y0,x1,y1)); k=480/max(x1-x0,y1-y0)
    im=im.resize((int((x1-x0)*k),int((y1-y0)*k)),Image.LANCZOS); d=ImageDraw.Draw(im)
    for x in range((x0//20+1)*20,x1,20):
        X=(x-x0)*k; d.line([(X,0),(X,im.height)],fill=(255,255,0) if x%100==0 else (255,255,255),width=1)
        if x%40==0: d.text((X+2,2),str(x),fill=(255,255,0))
    for y in range((y0//20+1)*20,y1,20):
        Y=(y-y0)*k; d.line([(0,Y),(im.width,Y)],fill=(255,255,0) if y%100==0 else (255,255,255),width=1)
        if y%40==0: d.text((2,Y+2),str(y),fill=(255,255,0))
    d.text((4,im.height-14),name,fill=(255,80,80)); tiles.append(im)
W=sum(t.width for t in tiles[:3])+12; rows=(len(tiles)+2)//3
sheet=Image.new('RGB',(max(W,1),rows*490),(30,30,30)); x=y=0
for i,t in enumerate(tiles):
    if i and i%3==0: x=0;y+=490
    sheet.paste(t,(x,y)); x+=t.width+6
sheet.save(out,quality=88)
