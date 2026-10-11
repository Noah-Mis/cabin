"""Sipping the coffee, first person and with no hands: the mug lifts off the sill, comes toward the viewer and tips,
then goes back down with a little less coffee in it."""
import math, json, os, shutil
from PIL import Image
W,H=320,180; BOX=(120,90,264,180); MS=120
SILL=(218,146)                                   # where the mug's base rests
RED=dict(l=(214,96,78),m=(172,60,56),d=(118,40,46),rim=(236,220,200),inside=(204,188,172),foot=(118,40,46),drink=(70,40,28),drink_h=(112,72,46))
CAMP=dict(l=(246,242,232),m=(224,220,210),d=(178,176,180),rim=(44,66,120),inside=(226,222,212),foot=(44,66,120),drink=(70,40,28),drink_h=(112,72,46),pine=(30,88,60),pine_d=(20,62,48))
NIGHT=(0.55,0.52,0.66)
def mug(cx,base_y,S,t,level,pal,tint):
    """S = size (1 on the sill), t = how far it is tipped toward the viewer (0 upright, 1 at the lips), level = how full it looks."""
    im=Image.new('RGBA',(W,H),(0,0,0,0)); px=im.load()
    Hb=16-9*t; ry=3.2+5.5*t; k=1-0.5*t; rim_y=base_y-(Hb+2)*S
    x0,x1=max(0,int(cx-16*S)),min(W,int(cx+18*S)+1); y0,y1=max(0,int(rim_y-(ry+1)*S)),min(H,int(base_y+2*S)+1)
    def col(c): return tuple(int(v*m) for v,m in zip(c,tint))+(255,)
    for y in range(y0,y1):
        for x in range(x0,x1):
            lx=(x+0.5-cx)/S; ly=(y+0.5-rim_y)/S; c=None
            w=9-0.9*max(0,ly)/Hb; u=lx/w
            if ly>=0 and abs(u)<=1:
                edge=2.4*k*math.sqrt(max(0,1-u*u))
                if ly<=Hb-0.7+edge:
                    c=pal['l'] if u<-0.62 else (pal['d'] if u>0.42 else pal['m'])
                    if ly>Hb-1.4+edge: c=pal['foot']
                    if 'pine' in pal:                                   # emblem on the camp mug
                        ey=(ly*16/Hb-4); ex=lx+2
                        if 0<=ey<10 and abs(ex)<=[0,1,1,2,1,2,3,2,3,4][int(ey)]+0.5: c=pal['pine'] if ex<=0 else pal['pine_d']
            hx,hy=lx-10.5,(ly-7.5*Hb/16)/(Hb/16)
            if lx>w and (hx/5.2)**2+(hy/6.2)**2<=1 and (hx/3.0)**2+(hy/4.0)**2>1:
                c=pal['d'] if (hy>2 or hx>3.4) else pal['m']
            if (lx/9)**2+(ly/ry)**2<=1:
                c=pal['rim']; iry=ry-0.9
                if (lx/7.6)**2+((ly-0.2)/iry)**2<=1:
                    c=pal['inside'] if ly<0.2 else tuple(int(v*0.86) for v in pal['inside'])     # inner wall, darker on the near side
                    sh=iry*(1-level); e=(lx/(7.6*(0.5+0.5*level)))**2+((ly-0.2-sh)/(iry*level))**2
                    if e<=1: c=pal['drink_h'] if (lx<-2 and ly<sh and e>0.45) else pal['drink']
            if c: px[x,y]=col(c)
    return im
# (dx, dy, size, tip, level) for each frame, relative to the resting place
PATH=[(0,-3,1.0,0,0.92),(0,-6,1.0,0,0.92),(-6,2,1.25,0.10,0.92),(-16,14,1.6,0.22,0.92),(-28,30,2.0,0.38,0.94),(-38,46,2.35,0.55,0.96),
      (-44,57,2.55,0.80,1.0),(-46,60,2.6,1.0,1.0),(-46,60,2.6,1.0,1.0),(-44,57,2.55,0.80,0.9),
      (-38,46,2.35,0.50,0.78),(-28,30,2.0,0.32,0.78),(-16,14,1.6,0.18,0.78),(-6,2,1.25,0.06,0.78),(0,-5,1.0,0,0.78),(0,-1,1.0,0,0.78),(0,0,1.0,0,0.78)]
def strip(fr):
    s=Image.new('RGBA',(len(fr)*fr[0].width,fr[0].height),(0,0,0,0))
    for i,f in enumerate(fr): s.paste(f,(i*f.width,0))
    return s
SH={}
for name,pal,dest in (('mug_sip',RED,'anim'),('mug_camp_sip',CAMP,'achievement_assets')):
    for tag,tt in (('',(1,1,1)),('_night',NIGHT)):
        fr=[mug(SILL[0]+dx,SILL[1]+dy,S,t,lv,pal,tt) for dx,dy,S,t,lv in PATH]
        strip([f.crop(BOX) for f in fr]).save(f'{dest}/{name}{tag}.png'); SH[name+tag]=fr
entry=lambda n,note:dict(files=[n+'.png',n+'_night.png'],frame_w=BOX[2]-BOX[0],frame_h=BOX[3]-BOX[1],frames=len(PATH),ms_per_frame=MS,loop=False,anchor=[0,0],placement={'x':BOX[0],'y':BOX[1]},note=note)
NOTE='Plays once when the mug is clicked. Hide the static mug and its steam while it plays, then show them again. The mug lifts, comes toward the viewer, tips at the bottom edge of the screen, and returns. Draw above everything else.'
m=json.load(open('anim/manifest.json')); m['animations']['mug_sip']=entry('mug_sip',NOTE); json.dump(m,open('anim/manifest.json','w'),indent=2)
a=json.load(open('achievement_assets/achievements.json')); a['animations']['mug_camp_sip']=entry('mug_camp_sip','The same sip for the enamel camp mug. '+NOTE); json.dump(a,open('achievement_assets/achievements.json','w'),indent=1)
bg=Image.open('bg_day.png').convert('RGBA'); bg.alpha_composite(Image.open('anim/near_forest_day.png')); bg.alpha_composite(Image.open('cabin_window.png').convert('RGBA'))
bg.alpha_composite(Image.open('anim/cig_pack.png'),(94,135)); bg.alpha_composite(Image.open('anim/folder.png'),(137,129))
rest=bg.copy(); rest.alpha_composite(Image.open('anim/mug.png').crop((0,0,32,44)),(205,106))
def sc(f):
    c=bg.copy(); c.alpha_composite(f); return c
seq=[rest]*5+[sc(f) for f in SH['mug_sip']]+[rest]*8
gf=[f.resize((640,360),Image.NEAREST).convert('RGB').quantize(128) for f in seq]
gf[0].save('anim/previews/preview_mug_sip.gif',save_all=True,append_images=gf[1:],duration=MS,loop=0)
sheet=Image.new('RGB',(640*4,360*2))
for i,k in enumerate((0,3,5,6,7,10,13,16)): sheet.paste(sc(SH['mug_sip'][k]).resize((640,360),Image.NEAREST).convert('RGB'),((i%4)*640,(i//4)*360))
sc(SH['mug_camp_sip'][5]).resize((640,360),Image.NEAREST).convert('RGB').save('/tmp/cabin/sip_camp_check.png')
sheet.save('anim/previews/mug_sip_frames.png')
shutil.copy('sip.py','anim/scripts/sip.py')
