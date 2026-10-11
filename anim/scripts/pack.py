import json
from PIL import Image
FW,FH=20,14
RED=(200,32,40); RED_D=(146,22,34); RED_L=(228,62,60)
WH=(244,240,232); WH_D=(206,200,198); WH_E=(170,164,168); EDGE=(168,162,162); TXT=(44,38,42); GOLD=(214,170,70)
X0,Y0,NA,ND=1,10,13,10    # printed face: 13 px across, 10 rows deep (19 long, foreshortened); lid end far from the viewer
def face(a,d):
    u=(ND-1-d)*2                            # distance from the lid end
    if d==5 and a==6: return GOLD
    if d==2 and a in (2,3,5,6,7,9,10): return TXT
    if d==1 and 4<=a<=8: return EDGE
    return WH if u>=4+abs(a-6) else RED_L
def build(tint=(1,1,1)):
    im=Image.new("RGBA",(FW,FH),(0,0,0,0)); px=im.load()
    def put(x,y,c): px[x,y]=tuple(int(c_*m) for c_,m in zip(c,tint))+(255,)
    cell={}
    for d in range(ND):                     # each row farther back leans 1 px right every 2 rows
        for a in range(NA):
            cell[(X0+a+d//2, Y0-d)]=(a,d)
    for (x,y),(a,d) in cell.items(): put(x,y,face(a,d))
    for x in range(FW):                     # 3 px of thickness below the lowest face pixel in each column
        ys=[y for (xx,y) in cell if xx==x]
        if not ys: continue
        y=max(ys); a,d=cell[(x,y)]
        col=WH_D if d==0 else (RED_D if d>5 else WH_E)      # near end, or the long right side
        for k in (1,2,3): put(x,y+k, col if k<3 else tuple(int(q*0.8) for q in col))
    return im
base=build(); night=build((0.55,0.52,0.66))
base.save("anim/cig_pack.png"); night.save("anim/cig_pack_night.png")
m=json.load(open("anim/manifest.json"))
m["animations"]["cig_pack"]=dict(files=["cig_pack.png","cig_pack_night.png"],frame_w=FW,frame_h=FH,frames=1,ms_per_frame=0,loop=False,
  anchor=[7,13],placement={"x":101,"y":148,"region":"sill band"},
  note="Static sill item: red and white flip-top cigarette pack. Lying flat on its back, pointing away from the viewer toward the window and leaning slightly right; lid end farthest. Anchor is the bottom-centre of the near end. Draw after cabin_window, like the mug.")
m["draw_order"][-1]="mug, cig_pack"
json.dump(m,open("anim/manifest.json","w"),indent=2)
bg=Image.open("bg_day.png").convert("RGBA"); bg.alpha_composite(Image.open("anim/near_forest_day.png"))
bg.alpha_composite(Image.open("cabin_window.png"))
mug=Image.open("anim/mug.png").crop((0,0,32,44)); bg.alpha_composite(mug,(218-13,146-40))
bg.alpha_composite(base,(101-7,148-13))
out=Image.new("RGBA",(1280,720+280),(104,164,226,255))
out.paste(bg.resize((1280,720),Image.NEAREST),(0,0))
out.paste((168,114,58,255),(0,720,1280,1000))
out.alpha_composite(base.resize((200,140),Image.NEAREST),(300,790)); out.alpha_composite(night.resize((200,140),Image.NEAREST),(700,790))
out.save("anim/previews/cig_pack_preview.png")
