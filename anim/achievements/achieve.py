"""Sprites for the achievement rewards and badges. Everything is saved into achievement_assets/."""
import math, json, os
from PIL import Image
os.chdir('/tmp/cabin')
OUT='achievement_assets'; W,H=320,180
TIMES=['morning','day','afternoon','night']
T={'day':(1,1,1),'morning':(1.0,0.84,0.88),'afternoon':(1.04,0.95,0.80),'night':(0.34,0.40,0.62)}
SOFT={'day':(1,1,1),'morning':(1.0,0.9,0.92),'afternoon':(1.03,0.97,0.86),'night':(0.72,0.74,0.86)}   # for things that glow
IN_NIGHT=(0.55,0.52,0.66)
def tint(c,t): return tuple(min(255,int(v*m)) for v,m in zip(c[:3],t))+((c[3],) if len(c)>3 else (255,))
def art(rows,mp,w=None,h=None,x0=0,y0=0,im=None,t=(1,1,1),keep=()):
    w=w or max(len(r) for r in rows); h=h or len(rows)
    im=im or Image.new('RGBA',(w,h),(0,0,0,0))
    for j,row in enumerate(rows):
        for i,ch in enumerate(row):
            if ch in mp and 0<=x0+i<im.width and 0<=y0+j<im.height:
                im.putpixel((x0+i,y0+j), (mp[ch]+(255,))[:4] if ch in keep else tint(mp[ch],t))
    return im
def strip(fr):
    s=Image.new('RGBA',(sum(f.width for f in fr),fr[0].height),(0,0,0,0)); x=0
    for f in fr: s.paste(f,(x,0)); x+=f.width
    return s
ANIM={}
def reg(name,files,fw,fh,n,ms,loop,anchor,place,note): ANIM[name]=dict(files=files,frame_w=fw,frame_h=fh,frames=n,ms_per_frame=ms,loop=loop,anchor=anchor,placement=place,note=note)
def save_times(name,build,tints=T):
    fl=[]
    for t in TIMES:
        strip(build(t,tints[t])).save(f'{OUT}/{name}_{t}.png'); fl.append(f'{name}_{t}.png')
    return fl

# ---------- 1 and 3: sasquatch wave, yeti peek, yeti wave ----------
SQ={'L':(128,92,62),'M':(88,60,42),'D':(44,30,24),'F':(156,118,90),'E':(20,12,10)}
YT={'L':(250,252,255),'M':(222,230,240),'D':(168,186,210),'F':(150,172,204),'E':(30,40,70)}
def fig(look):
    eyes={'c':"..MEFED...",'l':"..EFEFD...",'r':"..MFEFE...",'b':"..MFFFD..."}[look]
    return ["...LMM....","..LMMMD...",eyes,"..MFFFD...",".LMMMMMD..","LMMMMMMMD."]+["LMMMMMMMD."]*6
PEEK=[(2,'c'),(4,'c'),(6,'c'),(7,'c'),(7,'l'),(7,'l'),(7,'c'),(7,'r'),(7,'r'),(7,'b'),(7,'c'),(5,'c'),(3,'c'),(1,'c')]
WAVE=[(2,'c',0),(4,'c',0),(6,'c',0),(7,'c',0),(7,'c',1),(7,'c',2),(7,'c',1),(7,'c',2),(7,'c',1),(7,'b',2),(7,'c',0),(5,'c',0),(3,'c',0),(1,'c',0)]
def creature(pal,eye_night,seq,fw):
    def build(tname,tt):
        p=dict(pal); fr=[]
        for s in seq:
            shown,look=s[0],s[1]; arm=s[2] if len(s)>2 else 0
            im=Image.new('RGBA',(fw,16),(0,0,0,0)); rows=fig(look)[:shown+2]
            art(rows,p,im=im,x0=1,y0=16-(shown+2),t=tt)
            top=16-(shown+2)
            if arm:                                   # raised arm on the right, hand swinging between two positions
                pts=[(10,top+4),(11,top+3),(11,top+2),(12,top+1)] if arm==1 else [(10,top+4),(10,top+3),(11,top+2),(11,top+1)]
                for k,(x,y) in enumerate(pts): im.putpixel((x,y),tint(p['F'] if k==3 else p['M'],tt))
            if tname=='night':                        # eyes glow in the dark
                for j,row in enumerate(rows):
                    for i,ch in enumerate(row):
                        if ch=='E': im.putpixel((1+i,top+j),eye_night+(255,))
            fr.append(im)
        return fr
    return build
f=save_times('sasquatch_wave',creature(SQ,(214,200,120),WAVE,14))
reg('sasquatch_wave',f,14,16,14,160,False,[5,15],'same spots as sasquatch_peek','Reward 1. Replaces sasquatch_peek after the first click: he rises, waves twice, blinks and sinks.')
YTINT={'day':(1,1,1),'morning':(1.0,0.9,0.92),'afternoon':(1.03,0.97,0.88),'night':(0.5,0.56,0.76)}
f=save_times('yeti_peek',creature(YT,(150,230,255),PEEK,12),YTINT)
reg('yeti_peek',f,12,16,14,160,False,[5,15],'same spots as sasquatch_peek','Reward 3. A rare white yeti that peeks in place of the sasquatch.')
f=save_times('yeti_wave',creature(YT,(150,230,255),WAVE,14),YTINT)
reg('yeti_wave',f,14,16,14,160,False,[5,15],'same spots as sasquatch_peek','Reward 3 with reward 1: the yeti waves too.')

# ---------- 2: shiny birds and sparkle ----------
BG_={'D':(156,98,18),'M':(240,184,50),'L':(255,240,156),'B':(255,120,60)}
body=[".....MMMMMDD....","..DDMMMMMMDDB...","....LLLLLL......"]
up=["....DD..........","....DDD.........",".....DDD........","......DDD......."]
down=["....LLLDDD......",".....DDD........","....DDD.........","....DD.........."]
def bird(kind,tt):
    im=Image.new('RGBA',(16,12),(0,0,0,0)); art(body,BG_,im=im,y0=5,t=tt)
    if kind=='u': art(up,BG_,im=im,y0=1,t=tt)
    if kind=='m': art(["..DDDDDD........"],BG_,im=im,y0=4,t=tt)
    if kind=='d': art(down,BG_,im=im,y0=7,t=tt)
    return im
f=save_times('bird_flap_shiny',lambda n,tt:[bird(k,tt) for k in 'umdm'],SOFT)
reg('bird_flap_shiny',f,16,12,4,100,True,[8,6],'as bird_flap','Reward 2. Golden bird; use instead of bird_flap once unlocked. Leave a sparkle behind it every few frames.')
sa=["........","D.....D.",".D...D..","..DDD..."]; sb=["........","........","..DDD...","DD...DD."]
FAR={'D':(244,196,70)}
f=save_times('bird_far_shiny',lambda n,tt:[art(sa,FAR,8,6,t=tt),art(sb,FAR,8,6,t=tt)],SOFT)
reg('bird_far_shiny',f,8,6,2,180,True,[3,3],'as bird_far','Reward 2. Golden far bird.')
SP={'W':(255,255,240),'Y':(255,224,120),'y':(255,224,120,150)}
sp=[[".......",".......",".......","...W...",".......",".......","......."],
    [".......",".......","...Y...","..YWY..","...Y...",".......","......."],
    [".......","...y...","..yYy..",".yYWYy.","..yYy..","...y...","......."],
    [".......",".......","...y...","..yYy..","...y...",".......","......."]]
strip([art(r,SP,7,7) for r in sp]).save(f'{OUT}/sparkle.png')
reg('sparkle',['sparkle.png'],7,7,4,90,False,[3,3],'spawned in code','A twinkle that plays once and disappears. Used for the shiny bird trail and on the trophy.')

# ---------- 4: enamel camp mug ----------
CM={'mug_l':(246,242,232),'mug_m':(224,220,210),'mug_d':(178,176,180),'mug_r':(44,66,120),'drink':(70,40,28),'drink_h':(112,72,46),'pine':(30,88,60),'pine_d':(20,62,48),'chip':(60,60,70)}
def mug(fr,tt):
    MW,MH,MCX=32,44,13; im=Image.new('RGBA',(MW,MH),(0,0,0,0))
    def put(x,y,k): im.putpixel((x,y),tint(CM[k],tt))
    for y in range(MH):
        for x in range(MW):
            px_,py_=x+0.5,y+0.5; w=9-0.06*(y-22); u=(px_-MCX)/w
            if 22<=y and abs(u)<=1 and py_<=37.3+2.4*math.sqrt(max(0,1-u*u)):
                put(x,y,'mug_l' if u<-0.62 else ('mug_d' if u>0.42 else 'mug_m'))
                if py_>36.6+2.4*math.sqrt(max(0,1-u*u)): put(x,y,'mug_r')            # navy foot ring
            hx_,hy_=px_-(MCX+10.5),py_-29.5
            if px_>MCX+w and (hx_/5.2)**2+(hy_/6.2)**2<=1 and (hx_/3.0)**2+(hy_/4.0)**2>1:
                put(x,y,'mug_d' if (hy_>2 or hx_>3.4) else 'mug_m')
            e=((px_-MCX)/9)**2+((py_-22)/3.2)**2
            if e<=1:
                put(x,y,'mug_r'); ei=((px_-MCX)/7.6)**2+((py_-22.2)/2.3)**2
                if ei<=1: put(x,y,'drink_h' if (px_<MCX-2 and py_<21.5 and ei>0.45) else 'drink')
    for j,hw in enumerate([0,1,1,2,1,2,3,2,3,4]):                                   # pine tree emblem
        for dx in range(-hw,hw+1): put(11+dx,26+j,'pine' if dx<=0 else 'pine_d')
    put(11,36,'pine_d'); put(6,31,'chip'); put(18,34,'chip')                         # trunk, and two chips in the enamel
    for cx,off in ((9,0),(14,5),(18,9)):
        for y in range(2,20):
            hgt=19-y
            if (hgt-2*fr+off)%12<6:
                x=cx+round(1.7*math.sin((hgt-2*fr)*2*math.pi/12+off)); im.putpixel((x,y),(255,255,255,max(45,215-hgt*10)))
    return im
for tag,tt in (('',(1,1,1)),('_night',IN_NIGHT)): strip([mug(i,tt) for i in range(6)]).save(f'{OUT}/mug_camp{tag}.png')
reg('mug_camp',['mug_camp.png','mug_camp_night.png'],32,44,6,150,True,[13,40],{'x':218,'y':146},'Reward 4. White enamel camp mug with a navy rim and a pine tree; drop-in replacement for mug.')

# ---------- 5: ashtray  /  13: trophy  /  6: reviewed seal ----------
def ashtray(tt):
    """A heavy slate-blue ceramic ashtray seen from above and in front: thick rim with three rests, a well of ash, two butts. 22x14."""
    im=Image.new('RGBA',(22,14),(0,0,0,0)); cx,cy=11,5.5
    RIM=(96,114,146); RIM_H=(158,178,208); RIM_D=(60,74,102); WALL=(48,58,84); WALL_D=(34,40,60); WELL=(38,42,56); WELL_L=(54,60,78)
    ASH=[(98,96,102),(128,126,132),(158,156,160),(196,194,196)]
    def put(x,y,c,keep=False):
        if 0<=x<22 and 0<=y<14: im.putpixel((x,y),(c+(255,)) if keep else tint(c,tt))
    for y in range(14):
        for x in range(22):
            px_,py_=x+0.5,y+0.5
            top=((px_-cx)/10.5)**2+((py_-cy)/5.2)**2
            side=((px_-cx)/10.5)**2+((py_-cy-3.2)/5.2)**2
            if top>1 and side<=1:                                   # outer wall below the rim
                put(x,y,WALL_D if (py_>cy+6.2 or px_>cx+6) else WALL)
            if top<=1:
                ang=math.degrees(math.atan2(py_-cy,px_-cx))%360
                well=((px_-cx)/7.6)**2+((py_-cy-0.5)/3.3)**2
                if well<=1:
                    put(x,y,WELL_L if py_<cy-1 else WELL)           # inner wall catches a little light at the back
                else:
                    c=RIM_H if (200<=ang<=320 and top<0.78) else (RIM_D if (20<=ang<=160 and top>0.62) else RIM)
                    if any(abs((ang-n+180)%360-180)<8 for n in (35,145,270)): c=WELL_L if top<0.8 else RIM_D   # cigarette rests cut into the rim
                    put(x,y,c)
    for (x,y,k) in ((8,6,1),(9,6,2),(10,6,1),(11,6,2),(9,7,0),(10,7,1),(11,7,2),(12,7,1),(8,7,0),(10,5,2),(11,5,1),(12,6,0),(10,8,0),(11,8,1),(13,7,0),(9,5,3),(12,5,0)):
        put(x,y,ASH[k])                                             # the ash pile
    for (x,y,c) in ((5,5,(214,156,96)),(6,5,(214,156,96)),(7,6,(240,236,228)),(8,6,(206,200,198)),(6,6,(176,122,72))): put(x,y,c)   # a crushed butt, bent in the middle
    for (x,y,c) in ((13,6,(98,96,102)),(14,7,(240,236,228)),(15,7,(240,236,228)),(16,8,(206,200,198)),(17,8,(214,156,96)),(18,9,(214,156,96)),(19,9,(176,122,72))): put(x,y,c)   # one left in a rest, filter over the edge
    put(13,6,(236,110,40),keep=True)                                # its tip still glowing
    for (x,y) in ((4,3),(5,2),(6,2)): put(x,y,(214,226,244))        # glint on the rim
    return im
for tag,tt in (('',(1,1,1)),('_night',IN_NIGHT)): ashtray(tt).save(f'{OUT}/ashtray{tag}.png')
reg('ashtray',['ashtray.png','ashtray_night.png'],22,14,1,0,False,[11,13],{'x':124,'y':147},'Reward 5. Static sill item between the pack and the folder: a ceramic ashtray with ash, two butts and one tip still glowing.')
TR={'G':(236,186,54),'L':(255,236,140),'D':(170,116,24),'W':(255,252,226),'B':(96,60,30),'b':(132,86,42)}
tro=["..GGGGGG..","DGLWGGGGGD","D.LWGGGG.D","DGLGGGGGGD","..LGGGGD..","...LGGD...","....GD....","....GD....","...GGGD...","..bbbbbb..",".BBBBBBBB.",".BbbbbbbB.","BBBBBBBBBB"]
def trophy(tt):
    """The sill trophy: a two-handled gold cup on a stepped wooden base with a gold plate. 18x24."""
    im=Image.new('RGBA',(18,24),(0,0,0,0)); cx=9
    def put(x,y,c):
        if 0<=x<18 and 0<=y<24: im.putpixel((x,y),tint(c,tt))
    BOWL={0:6.5,1:6.5,2:6,3:6,4:6,5:6,6:6,7:5.5,8:4.5,9:3.5,10:2.5}
    for y in range(1,8):                                   # handles, drawn first so the bowl overlaps them
        for x in range(18):
            for hcx in (cx-7.5,cx+7.5):
                dx,dy=x+0.5-hcx,y+0.5-4.5
                if (dx/3.2)**2+(dy/3.6)**2<=1 and (dx/1.6)**2+(dy/2.0)**2>1: put(x,y,TR['D'] if (dy>1 or hcx>cx) else TR['G'])
    for y,hw in BOWL.items():
        for x in range(18):
            u=(x+0.5-cx)/hw
            if abs(u)<=1:
                c=TR['L'] if u<-0.55 else (TR['W'] if (-0.55<=u<-0.25 and 1<=y<=7) else (TR['D'] if u>0.45 else TR['G']))
                if y==0: c=TR['L']
                put(x,y,c)
    for x,y in ((8,3),(9,3),(7,4),(8,4),(9,4),(10,4),(8,5),(9,5),(8,6),(9,2)): put(x,y,TR['D'])   # embossed star
    for y in range(11,16):
        hw=2 if y==13 else 1
        for x in range(cx-hw,cx+hw): put(x,y,TR['L'] if x<cx else TR['D'])
    for y,hw in ((16,4),(17,5)):
        for x in range(cx-hw,cx+hw): put(x,y,TR['L'] if x<cx-hw+2 else (TR['D'] if x>=cx+hw-2 else TR['G']))
    for y,hw in ((18,6),(19,7),(20,7),(21,7),(22,7),(23,8)):
        for x in range(cx-hw,cx+hw):
            c=TR['b']
            if y==18 or x==cx-hw: c=(168,114,58)
            if x==cx+hw-1 or y==23: c=TR['B']
            if y in (20,21) and cx-4<=x<cx+4: c=TR['G'] if y==20 else TR['D']
            put(x,y,c)
    return im
for tag,tt in (('',(1,1,1)),('_night',(0.7,0.66,0.7))): trophy(tt).save(f'{OUT}/trophy{tag}.png')
reg('trophy',['trophy.png','trophy_night.png'],18,24,1,0,False,[9,23],{'x':72,'y':147},'Reward 13. A two-handled gold cup on a wooden base, at the left of the sill; its top stands in front of the bottom of the view. Spawn a sparkle on it now and then.')
for tag,tt in (('',(1,1,1)),('_night',(0.72,0.68,0.7))):
    im=Image.new('RGBA',(52,22),(0,0,0,0))
    for d in range(1,7):
        for a in range(29,40):
            edge=d in (1,6) or a in (29,39)
            c=(184,132,28) if edge else (250,214,96)
            if not edge and (a,d) in ((32,3),(33,2),(34,3),(35,4),(36,5),(37,4)): c=(150,96,20)     # tick mark
            im.putpixel((1+a+d//3,14-d),tint(c,tt))
    im.save(f'{OUT}/folder_reviewed_overlay{tag}.png')
reg('folder_reviewed_overlay',['folder_reviewed_overlay.png','folder_reviewed_overlay_night.png'],52,22,1,0,False,[23,20],{'x':160,'y':149},'Reward 6. A gold seal with a tick; draw it directly over the closed folder sprite (same size and anchor). Hide it while the folder is open.')

# ---------- 7: shooting star  /  8: aurora  /  9: rainbow  /  10: constellation ----------
fr=[]
for f_ in range(8):
    im=Image.new('RGBA',(40,20),(0,0,0,0)); u=f_/5; hx,hy=36-32*u,2+16*u; fade=1 if f_<5 else (0.55 if f_==5 else (0.25 if f_==6 else 0))
    for k in range(14):
        x,y=int(round(hx+k*2)),int(round(hy-k)); a=int((255 if k==0 else max(0,210-k*17))*fade)
        if 0<=x<40 and 0<=y<20 and a>0: im.putpixel((x,y),((255,255,255) if k<2 else (190,210,255))+(a,))
    fr.append(im)
strip(fr).save(f'{OUT}/shooting_star.png')
reg('shooting_star',['shooting_star.png'],40,20,8,60,False,[0,0],{'region':'night sky, x 60-240, y 26-50','clip':'sky_mask.png'},'Reward 7. Night only. A streak falling down and to the left, then fading. Plays once at a random spot.')
fr=[]
for f_ in range(8):
    ph=2*math.pi*f_/8; im=Image.new('RGBA',(240,46),(0,0,0,0))
    for x in range(240):
        top=7+5*math.sin(x*0.05+ph)+3*math.sin(x*0.13-2*ph); hgt=18+8*math.sin(x*0.031+ph+1.0)
        inten=0.5+0.5*math.sin(x*0.09+ph+1.7*math.sin(x*0.021))
        for y in range(46):
            fq=(y-top)/hgt
            if not 0<=fq<=1: continue
            c=(96,236,156) if fq<0.4 else ((64,180,196) if fq<0.72 else (136,96,206))
            a=120*inten*(1-fq)**0.7*(0.6 if x%3==0 else 1.0)
            q=105 if a>88 else (70 if a>52 else (38 if a>22 else 0))
            if q==38 and (x+y)%2: q=0
            if q: im.putpixel((x,y),c+(q,))
    fr.append(im)
# the aurora is now drawn by aurora.py (60 frames); this registers its metadata only
reg('aurora',['aurora.png'],240,60,60,160,True,[0,0],{'x':40,'y':24,'clip':'sky_mask.png'},'Reward 8. Night only. Wavering green, teal and violet curtains across the top of the sky. Draw under the stars; show on some nights, fading in and out.')
im=Image.new('RGBA',(128,64),(0,0,0,0)); RB=[(230,70,70),(240,150,60),(245,225,90),(90,200,110),(80,140,230),(140,90,200)]
for y in range(64):
    for x in range(128):
        r=math.hypot(x+0.5-64,y+0.5-64); k=int((60-r)//2)
        if 0<=k<6 and r<=60:
            a=112 if 0<k<5 else 70
            if (k in (0,5)) and (x+y)%2: continue
            im.putpixel((x,y),RB[k]+(a,))
im.save(f'{OUT}/rainbow.png')
reg('rainbow',['rainbow.png'],128,64,1,0,False,[0,0],{'x':96,'y':60},'Reward 9. A translucent arc over the waterfall. Fade it in when rain stops and out after about 20 seconds. Draw after the waterfall and before the near forest.')
sky=Image.open('anim/sky_mask.png'); CX,CY=52,27
PTS={'head':(16,2),'neck':(16,7),'shl':(11,9),'shr':(21,9),'hl':(6,17),'hr':(26,15),'hip':(16,18),'kl':(11,25),'kr':(22,24),'fl':(7,31),'fr':(27,30)}
LINES=[('head','neck'),('neck','shl'),('neck','shr'),('shl','hl'),('shr','hr'),('neck','hip'),('hip','kl'),('hip','kr'),('kl','fl'),('kr','fr')]
im=Image.new('RGBA',(34,34),(0,0,0,0))
for a,b in LINES:
    (x0,y0),(x1,y1)=PTS[a],PTS[b]; n=max(abs(x1-x0),abs(y1-y0))
    for i in range(1,n):
        if i%2==0: im.putpixel((round(x0+(x1-x0)*i/n),round(y0+(y1-y0)*i/n)),(110,130,190,150))
for k,(x,y) in PTS.items():
    im.putpixel((x,y),(236,240,255,255))
    if k in ('head','hip','fl','fr'):
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)): im.putpixel((x+dx,y+dy),(130,150,206,255))
im.save(f'{OUT}/constellation_sasquatch.png')
print('constellation stars off the sky:',sum(1 for x,y in PTS.values() if sky.getpixel((CX+x,CY+y))[3]==0))
reg('constellation_sasquatch',['constellation_sasquatch.png'],34,34,1,0,False,[0,0],{'x':CX,'y':CY,'clip':'sky_mask.png'},'Reward 10. Night only. A striding figure picked out in stars and faint lines, in the upper left of the sky.')
night=Image.open('bg_night.png').convert('RGB')
STARS=[[x,y] for y in range(24,131) for x in range(40,280) if night.getpixel((x,y)) in ((230,236,255),(120,140,196))]

# ---------- 12: deer ----------
DE={'M':(156,108,64),'D':(104,70,44),'L':(210,174,132),'W':(250,246,236),'A':(84,58,40),'E':(24,16,14)}
stand=["..........A.A.","..........AA..",".........MMEM.",".........MM...","W.MMMMMMMM....",".MMMMMMMMM....",".MLLLLLLMM....",".M.M...M.M....",".D.D...D.D....",".D.D...D.D...."]
walk2=["..........A.A.","..........AA..",".........MMEM.",".........MM...","W.MMMMMMMM....",".MMMMMMMMM....",".MLLLLLLMM....","..MM...MM.....","..DD...DD.....","..D.D..D.D...."]
graze=["..............","..............","..............",".........M....","W.MMMMMMMMM...",".MMMMMMMMMM...",".MLLLLLLMMMA..",".M.M...M.MMMA.",".D.D...D.D.MEM",".D.D...D.D..MM"]
flick=[r for r in stand]; flick[3]="W........MM..."; flick[4]="..MMMMMMMM...."
f=save_times('deer_walk',lambda n,tt:[art(r,DE,14,10,t=tt) for r in (stand,walk2,stand,walk2)])
reg('deer_walk',f,14,10,4,170,True,[6,9],{'path':'feet on y=123, enters from x 128 and stops near x 148','behind':'near_forest_<time>.png'},'Reward 12. Faces right; mirror to walk left.')
f=save_times('deer_graze',lambda n,tt:[art(r,DE,14,10,t=tt) for r in (stand,graze,graze,graze,stand,flick)])
reg('deer_graze',f,14,10,6,320,False,[6,9],{'x':148,'y':123,'behind':'near_forest_<time>.png'},'Reward 12. Stands, lowers its head to the water, looks up, flicks its tail. Then walk on or back.')

# ---------- badges and the unlock sign ----------
OL=(38,22,12); SH=(84,52,26); MID=(132,86,42); LT=(168,114,58); HI=(204,150,84); GOLD=(236,186,54)
def plaque(locked=False):
    im=Image.new('RGBA',(16,16),OL+(255,))
    for y in range(1,15):
        for x in range(1,15):
            c=(SH if locked else (38,78,60))                 # unlocked badges sit on dark green felt so every icon reads
            if not locked and (x==1 or y==1): c=(58,106,80)
            if x==14 or y==14: c=(60,36,18) if locked else (26,56,46)
            im.putpixel((x,y),c+(255,))
    if not locked:
        for x,y in ((1,1),(14,1),(1,14),(14,14)): im.putpixel((x,y),GOLD+(255,))
    return im
def badge(icon):
    p=plaque(); p.alpha_composite(icon,((16-icon.width)//2,(16-icon.height)//2)); return p
ICN={}
ICN['sasquatch']=art(fig('c')[:7],SQ)
ICN['bird']=bird('u',(1,1,1)).crop((2,1,14,9))
ICN['yeti']=art(fig('c')[:7],YT)
ICN['mug']=art(["..RRRRRRR...",".RCCCCCCCR..",".LRRRRRRRD..",".LMMMMMMMDMM",".LMMPMMMMD.M",".LMPPPMMMD.M",".LMMPMMMMDM.","..LMMMMMD...","...DDDDD...."],{'R':CM['mug_r'],'C':CM['drink'],'L':CM['mug_l'],'M':CM['mug_m'],'D':CM['mug_d'],'P':CM['pine']})
ICN['smoke']=art(["..........S.",".........S..","..........S.","........EE..",".......AA...","......PP....",".....PP.....","....PP......","...FF.......","..FF........"],{'S':(226,226,232),'E':(250,150,48),'A':(150,148,150),'P':(244,240,232),'F':(214,156,96)})
ICN['folder']=art([".......TTTT.","TTTTTTTTTTTT","TtttttttttLT","TtPPPPttSStT","TtPPPPttSStT","TttttttttttT","PPPPPPPPPPPP","pPpPpPpPpPpP","BBBBBBBBBBBB"],{'T':(224,192,140),'t':(206,170,116),'L':(236,208,158),'P':(244,240,232),'p':(198,194,188),'S':GOLD,'B':(140,106,68)})
ICN['moon']=art(["...YYYY...","..YYY.....",".YYY......",".YYY.....W",".YYY......",".YYY......","..YYY..W..","...YYYY...","....YY...."],{'Y':(240,232,190),'W':(255,255,255)})
ICN['clock']=art(["...WWWW...","..W....W..",".W..D...W.","W...D....W","W...DDD..W","W........W",".W......W.","..W....W..","...WWWW..."],{'W':(240,236,226),'D':(84,52,26)})
ICN['storm']=art(["...WWW......",".WWWWWWW....","WWWWWWWWWW..","WWWWWWWWWW..","..B..Y..S...",".B..YY...S..","....Y..S....","...Y....S..."],{'W':(214,222,236),'B':(110,160,230),'Y':(255,224,90),'S':(255,255,255)})
ICN['star']=art(["....W....","....W....","...WYW...","WWWYYYWWW","...WYW...","....W....","....W...."],{'W':(230,236,255),'Y':(255,244,170)})
ICN['terminal']=art(["KKKKKKKKKKKK","KGGKKKKKKKKK","KKGGKKKKKKKK","KKKGGKKKKKKK","KKGGKKKKKKKK","KGGKKGGGGKKK","KKKKKKKKKKKK"],{'K':(18,28,20),'G':(90,240,130)})
ICN['deer']=art(stand,DE).crop((7,0,14,7))
ICN['trophy']=art(tro,TR)
ORDER=[('first_sighting','sasquatch'),('bird_watcher','bird'),('cryptid_hunter','yeti'),('caffeinated','mug'),('smoke_break','smoke'),('case_closed','folder'),
       ('night_owl','moon'),('around_the_clock','clock'),('storm_chaser','storm'),('stargazer','star'),('power_user','terminal'),('cabin_fever','deer'),('woodsman','trophy')]
lock=plaque(True); art([".HHH.","H...H","...H.","..H..",".....","..H.."],{'H':(120,84,48)},im=lock,x0=5,y0=5)
strip([badge(ICN[i]) for _,i in ORDER]+[lock]).save(f'{OUT}/badges.png')
sign=Image.new('RGBA',(132,24),(0,0,0,0))
for y in range(24):
    for x in range(132):
        if (x in (0,131) and y in (0,23)): continue
        c=OL if (x in (0,131) or y in (0,23)) else (LT if y<3 else (MID if y<20 else SH))
        if 1<=y<=22 and 1<=x<=130 and (x*7+y*3)%29==0 and y not in (1,22): c=SH if y<20 else OL
        sign.putpixel((x,y),c+(255,))
for x,y in ((4,4),(127,4),(4,19),(127,19)): sign.putpixel((x,y),HI+(255,)); sign.putpixel((x+1,y+1),OL+(255,))
for y in range(3,21):
    for x in range(3,23): 
        if x in (3,22) or y in (3,20): sign.putpixel((x,y),SH+(255,))
sign.save(f'{OUT}/achievement_sign.png')

# ---------- data file ----------
A=[
 dict(id='first_sighting',name='Something in the Trees',desc='Spot the sasquatch',stat='sasquatchClicks',goal=1,reward='He waves on every later visit',assets=['sasquatch_wave']),
 dict(id='bird_watcher',name='Bird Watcher',desc='Click 50 birds',stat='birdClicks',goal=50,reward='All birds turn shiny gold and leave sparkles',assets=['bird_flap_shiny','bird_far_shiny','sparkle']),
 dict(id='cryptid_hunter',name='Cryptid Hunter',desc='Spot the sasquatch 10 times',stat='sasquatchClicks',goal=10,reward='A rare white yeti sometimes peeks instead',assets=['yeti_peek','yeti_wave']),
 dict(id='caffeinated',name='Caffeinated',desc='Take 25 sips of coffee',stat='mugClicks',goal=25,reward='The cup becomes an enamel camp mug',assets=['mug_camp']),
 dict(id='smoke_break',name='Smoke Break',desc='Finish a whole cigarette',stat='smokesFinished',goal=1,reward='An ashtray appears on the sill',assets=['ashtray']),
 dict(id='case_closed',name='Case Closed',desc='Read every tab in the folder',stat='tabsSeen',goal=4,reward='The folder gets a gold REVIEWED seal',assets=['folder_reviewed_overlay']),
 dict(id='night_owl',name='Night Owl',desc='Visit at night',stat='timesSeen',goal='night',reward='Shooting stars cross the night sky',assets=['shooting_star']),
 dict(id='around_the_clock',name='Around the Clock',desc='See morning, day, afternoon and night',stat='timesSeen',goal=4,reward='Northern lights appear on some nights',assets=['aurora']),
 dict(id='storm_chaser',name='Storm Chaser',desc='See both rain and snow',stat='weatherSeen',goal=2,reward='A rainbow shows over the falls after rain',assets=['rainbow']),
 dict(id='stargazer',name='Stargazer',desc='Click 10 stars',stat='starClicks',goal=10,reward='A sasquatch constellation appears',assets=['constellation_sasquatch']),
 dict(id='power_user',name='Power User',desc='Use every terminal command',stat='commandsUsed',goal='all',reward='A green-screen terminal theme',assets=[]),
 dict(id='cabin_fever',name='Cabin Fever',desc='Stay for 10 minutes',stat='secondsOpen',goal=600,reward='A deer visits the water now and then',assets=['deer_walk','deer_graze']),
 dict(id='woodsman',name='Woodsman',desc='Earn every other achievement',stat='unlocked',goal=12,reward='A gold trophy on the sill',assets=['trophy','sparkle']),
]
for i,a in enumerate(A): a['badge_frame']=i
json.dump({'canvas':[W,H],'badges':{'file':'badges.png','frame_w':16,'frame_h':16,'locked_frame':13},
           'sign':{'file':'achievement_sign.png','w':132,'h':24,'badge_slot':{'x':5,'y':4},'text_area':{'x':27,'y':4,'w':100,'h':16}},
           'terminal_theme_green':{'background':'#0C140E','text':'#5AF082','dim':'#2E8A4A','cursor':'#B6FFC8'},
           'star_click_targets':STARS,'achievements':A,'animations':ANIM},open(f'{OUT}/achievements.json','w'),indent=1)
print(len(os.listdir(OUT)),'files;',len(STARS),'stars')

# ---------- preview ----------
def scene(t,layers_back,layers_front,sill):
    c=Image.open(f'bg_{t}.png').convert('RGBA')
    skyl=Image.new('RGBA',(W,H),(0,0,0,0))
    for im,pos in layers_back: skyl.alpha_composite(im,pos)
    c.alpha_composite(Image.composite(skyl,Image.new('RGBA',(W,H),(0,0,0,0)),sky.split()[3]))
    for im,pos in layers_front: c.alpha_composite(im,pos)
    c.alpha_composite(Image.open(f'anim/near_forest_{t}.png')); c.alpha_composite(Image.open('cabin_window.png').convert('RGBA'))
    for im,pos in sill: c.alpha_composite(im,pos)
    return c
L=lambda n,i=0,fw=None: (lambda s: s.crop((i*fw,0,(i+1)*fw,s.height)) if fw else s)(Image.open(f'{OUT}/{n}.png').convert('RGBA'))
ni='_night'
night_s=scene('night',[(L('aurora',2,240),(40,24)),(L('constellation_sasquatch'),(CX,CY)),(L('shooting_star',3,40),(170,30))],
   [(L('yeti_wave_night',5,14),(246-5,109-15)),(L('deer_graze_night',2,14),(148-6,123-9))],
   [(L('mug_camp_night',0,32),(205,106)),(Image.open('anim/cig_pack_night.png'),(94,135)),(L('ashtray_night'),(113,134)),(L('trophy_night'),(63,124)),
    (Image.open('anim/folder_night.png'),(137,129)),(L('folder_reviewed_overlay_night'),(137,129))])
day_s=scene('day',[(L('bird_far_shiny_day',0,8),(230,40))],
   [(L('rainbow'),(96,60)),(L('deer_walk_day',0,14),(150-6,123-9)),(L('sasquatch_wave_day',6,14),(72-5,109-15))],
   [(L('mug_camp',0,32),(205,106)),(Image.open('anim/cig_pack.png'),(94,135)),(L('ashtray'),(113,134)),(L('trophy'),(63,124)),
    (Image.open('anim/folder.png'),(137,129)),(L('folder_reviewed_overlay'),(137,129)),(L('bird_flap_shiny_day',0,16),(120,50)),(L('sparkle',2,7),(108,52)),(L('sparkle',1,7),(98,56)),
    (L('achievement_sign'),(94,28)),(L('badges',1,16),(99,32))])
pv=Image.new('RGBA',(1280*2,720+330),(60,40,24,255))
pv.paste(day_s.resize((1280,720),Image.NEAREST),(0,0)); pv.paste(night_s.resize((1280,720),Image.NEAREST),(1280,0))
b=Image.open(f'{OUT}/badges.png'); pv.alpha_composite(b.resize((b.width*6,96),Image.NEAREST),(20,740))
x=20
for n,i,fw in (('sasquatch_wave_day',5,14),('yeti_peek_day',6,12),('bird_flap_shiny_day',0,16),('mug_camp',0,32),('ashtray',0,None),('trophy',0,None),('deer_walk_day',0,14),('deer_graze_day',2,14),('sparkle',2,7)):
    s=L(n,i,fw); s=s.resize((s.width*8,s.height*8),Image.NEAREST); pv.alpha_composite(s,(x,860+(180-s.height)//2 if s.height<180 else 700)); x+=s.width+30
pv.save(f'{OUT}/achievements_preview.png')
