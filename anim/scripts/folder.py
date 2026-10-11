"""A thick brown-tan folder stuffed with papers: resting on the sill, arriving, and opening."""
import json, math, os, shutil
from PIL import Image
W,H=320,180
FW,FH,UP=52,22,18             # closed sprite is 52x22; the opening frames add 18 rows above for the raised cover
TAN=(206,170,116); TAN_M=(214,180,126); TAN_L=(224,192,140); TAN_H=(236,208,158); TAN_D=(160,124,80); TAN_B=(140,106,68)
SCORE=(188,152,100); INNER=(228,202,156); INNER_D=(204,174,126)
PAPER=(240,236,226); PAPER_D=(198,194,188); INK=(96,84,76); TEXT=(150,146,152); STAMP=(176,58,48)
X0,Y0,NA,ND=1,14,44,11        # cover: 44 px wide, 11 rows deep, leaning 1 px right every 3 rows as it recedes
THICK=6
AT=(160,149); ANCHOR=(23,20)
def cover_color(a,d):
    """Clean detailing instead of speckles: three flat light bands, two score lines by the spine, a lit far edge, a label and a stamp."""
    c=TAN if d<4 else (TAN_M if d<7 else TAN_L)
    if a in (2,4): c=SCORE
    if d==ND-1: c=TAN_H
    if d==0: c=TAN_D
    if 7<=a<=18 and 4<=d<=7: c=PAPER
    if 9<=a<=16 and d in (5,6) and (a+d)%2==0: c=INK
    if 30<=a<=38 and 2<=d<=5 and (d in (2,5) or a in (30,38)): c=STAMP
    if 32<=a<=36 and d in (3,4) and (a+d)%2==0: c=STAMP
    return c
def page_color(a,d):
    if a in (0,NA-1) or d==ND-1: return TAN_M                 # back cover showing round the page
    if d in (8,) and 3<=a<=14: return INK                     # heading
    if d in (2,4,6) and 3<=a<=39 and (a*7+d*3)%9 not in (0,1): return TEXT
    return PAPER
def build(theta=None, tint=(1,1,1)):
    im=Image.new("RGBA",(FW,FH+UP),(0,0,0,0)); px=im.load()
    def put(x,y,c,k=1.0):
        y+=UP
        if 0<=x<FW and 0<=y<FH+UP: px[x,y]=tuple(int(v*m*k) for v,m in zip(c,tint))+(255,)
    opened=bool(theta)
    cell={}
    for d in range(ND):
        for a in range(NA): cell[(X0+a+d//3, Y0-d)]=('cover',a,d)
        for a in (NA,NA+1):                                   # loose sheets poking out of the right side
            if 1<=d<=8 and not (a==NA+1 and d in (1,8)): cell[(X0+a+d//3, Y0-d)]=('sheet',a,d)
    for d in (ND,ND+1):                                       # the tab on the far edge
        for a in range(27,39): cell[(X0+a+d//3, Y0-d)]=('tab',a,d)
    for (x,y),(kind,a,d) in cell.items():
        if kind=='sheet': c=PAPER if (a+d)%3 else PAPER_D
        elif kind=='tab': c=TAN_H if d==ND+1 else TAN_L
        else: c=page_color(a,d) if opened else cover_color(a,d)
        put(x,y,c)
    for x in range(FW):                                       # the thick edge: cover, a stack of ragged paper, back cover
        ys=[y for (xx,y) in cell if xx==x]
        if not ys: continue
        y=max(ys); kind,a,d=cell[(x,y)]
        side=0.86 if d>0 else 1.0
        if kind=='sheet': put(x,y+1,PAPER_D,side); continue
        for k in range(1,THICK+1):
            if k==1: c=PAPER_D if opened else TAN_D
            elif k==THICK: c=TAN_B
            else: c=PAPER if (k%2==0) != ((x*3+k)%7==0) else PAPER_D
            put(x,y+k,c,side)
    if opened:                                                # the front cover, hinged along the far edge and swung up by theta degrees
        t=math.radians(theta); end=0.5*22*math.cos(t)-0.87*22*math.sin(t)
        hy=Y0-(ND-1); hs=(ND-1)//3
        n=max(1,round(abs(end)))
        for j in range(n+1):
            if end>0:                                         # still tipped toward us: we see the outside, squashed
                y=hy+j; d=(ND-1)-j*(ND-1)/n; sh=int(d)//3
                for a in range(NA): put(X0+a+sh,y,cover_color(a,int(round(d))) if n>8 else (TAN_D if j==n else (TAN if d<5 else TAN_L)))
            else:                                             # past upright: we see the plain inside
                y=hy-j
                for a in range(NA):
                    c=INNER if j<n*0.55 else INNER_D
                    if j==n: c=TAN_D
                    if a in (0,NA-1): c=TAN
                    if j==0: c=TAN_B
                    put(X0+a+hs,y,c)
    return im
def strip(fr):
    s=Image.new("RGBA",(len(fr)*fr[0].width,fr[0].height),(0,0,0,0))
    for i,f in enumerate(fr): s.paste(f,(i*f.width,0))
    return s
ANGLES=[0,12,24,40,60,80,100,106,102]
BOX=(130,110,196,180)
OUT={}
for tag,tint in (('',(1,1,1)),('_night',(0.55,0.52,0.66))):
    closed=build(None,tint).crop((0,UP,FW,FH+UP)); closed.save(f"anim/folder{tag}.png")
    op=[build(a,tint) for a in ANGLES]; strip(op).save(f"anim/folder_open{tag}.png"); op[-1].save(f"anim/folder_opened{tag}.png")
    fr=[]
    for dy in [50,34,20,9,2,0,-1,0,0,0]:                      # heavier than the pack: it lands with barely a bounce
        im=Image.new("RGBA",(W,H),(0,0,0,0)); im.alpha_composite(closed,(AT[0]-ANCHOR[0],AT[1]-ANCHOR[1]+dy)); fr.append(im.crop(BOX))
    strip(fr).save(f"anim/folder_place{tag}.png")
    OUT[tag]=(closed,op,fr)
m=json.load(open("anim/manifest.json"))
E={}
E["folder"]=dict(files=["folder.png","folder_night.png"],frame_w=FW,frame_h=FH,frames=1,ms_per_frame=0,loop=False,anchor=list(ANCHOR),
  placement={"x":AT[0],"y":AT[1],"region":"sill band"},note="Static sill item: a thick brown-tan folder full of papers, lying flat and closed. Anchor is the bottom-centre of the near edge.")
E["folder_place"]=dict(files=["folder_place.png","folder_place_night.png"],frame_w=BOX[2]-BOX[0],frame_h=BOX[3]-BOX[1],frames=10,ms_per_frame=120,loop=False,anchor=[0,0],
  placement={"x":BOX[0],"y":BOX[1]},note="The folder slides up onto the sill and lands with barely a bounce. The folder is part of these frames; show the static folder once it ends.")
E["folder_open"]=dict(files=["folder_open.png","folder_open_night.png"],frame_w=FW,frame_h=FH+UP,frames=len(ANGLES),ms_per_frame=110,loop=False,anchor=[ANCHOR[0],ANCHOR[1]+UP],
  placement={"x":AT[0],"y":AT[1],"region":"sill band"},note="The front cover swings up on its far edge, overshoots slightly and settles propped open, revealing the top page. Replaces the static folder while it plays; frame 0 matches the closed folder. Play backwards to close.")
E["folder_opened"]=dict(files=["folder_opened.png","folder_opened_night.png"],frame_w=FW,frame_h=FH+UP,frames=1,ms_per_frame=0,loop=False,anchor=[ANCHOR[0],ANCHOR[1]+UP],
  placement={"x":AT[0],"y":AT[1],"region":"sill band"},note="Static open folder: the last frame of folder_open, to show after it finishes.")
m["animations"].update(E); json.dump(m,open("anim/manifest.json","w"),indent=2)
# its own zip
shutil.rmtree("folder_assets",ignore_errors=True); os.makedirs("folder_assets")
for f in os.listdir("anim"):
    if f.startswith("folder") and f.endswith(".png"): shutil.copy("anim/"+f,"folder_assets/"+f)
json.dump({"canvas":[W,H],"note":"Sheets are single rows of equal frames. Position each so its anchor point lands on the placement x,y; sheets with anchor [0,0] are placed by their top-left corner.","animations":E},open("folder_assets/folder_manifest.json","w"),indent=2)
# previews
bg=Image.open("bg_day.png").convert("RGBA"); bg.alpha_composite(Image.open("anim/near_forest_day.png")); bg.alpha_composite(Image.open("cabin_window.png").convert("RGBA"))
bg.alpha_composite(Image.open("anim/mug.png").crop((0,0,32,44)),(205,106)); bg.alpha_composite(Image.open("anim/cig_pack.png"),(94,135))
closed,op,fr=OUT['']
def at(spr,up): 
    c=bg.copy(); c.alpha_composite(spr,(AT[0]-ANCHOR[0],AT[1]-ANCHOR[1]-up)); return c
out=Image.new("RGBA",(1280*2,720+420),(168,114,58,255))
out.paste(at(closed,0).resize((1280,720),Image.NEAREST),(0,0)); out.paste(at(op[-1],UP).resize((1280,720),Image.NEAREST),(1280,0))
for i,f in enumerate(op): out.alpha_composite(f.resize((FW*5,(FH+UP)*5),Image.NEAREST),(20+i*282,740))
out.save("anim/previews/folder_preview.png")
seq=[bg.copy() for _ in range(2)]
for f in fr:
    c=bg.copy(); c.alpha_composite(f,(BOX[0],BOX[1])); seq.append(c)
seq+=[at(closed,0)]*6+[at(f,UP) for f in op]+[at(op[-1],UP)]*12+[at(f,UP) for f in reversed(op)]+[at(closed,0)]*6
gf=[f.resize((640,360),Image.NEAREST).convert("RGB").quantize(128) for f in seq]
gf[0].save("anim/previews/preview_folder.gif",save_all=True,append_images=gf[1:],duration=115,loop=0)
