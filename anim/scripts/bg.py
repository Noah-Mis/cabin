import math, random
from PIL import Image
random.seed(11)
W,H=320,180
g=[[None]*W for _ in range(H)]
BAYER=[[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]]
for y in range(H):
    for x in range(W):
        f=min(4.999,max(0,y/105*5)); b=int(f); fr=f-b
        t=(fr-0.55)/0.45
        if t>(BAYER[y%4][x%4]+0.5)/16: b+=1
        g[y][x]='sky%d'%min(b,5)
def interp(pts,x):
    for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
        if x0<=x<=x1: return y0+(y1-y0)*(x-x0)/(x1-x0)
    return pts[-1][1]
def heights(pts,amp,ph):
    return [int(round(interp(pts,x)+amp*(1.2*math.sin(x*0.9+ph)+math.sin(x*0.37+ph*2)+0.8*math.sin(x*0.19+ph*3)))) for x in range(W)]
rowjit=[random.choice([-1,0,0,1]) for _ in range(H)]
def fill_mtn(hs,L,S,shear,snow=None):
    for x in range(W):
        for y in range(max(0,hs[x]),H):
            d=y-hs[x]
            xs=int(x-d*shear)+rowjit[y]; xs=max(2,min(W-3,xs))
            lit=(hs[xs+2]-hs[xs-2])<=0
            c=L if lit else S
            if snow:
                sd=(72-hs[x])*0.55+[0,2,1,3,1,2][x%6]
                if d<sd: c=snow[0] if lit else snow[1]
            g[y][x]=c
far=heights([(0,82),(30,70),(55,80),(85,62),(110,76),(135,66),(160,78),(190,60),(215,74),(245,64),(275,78),(300,68),(320,80)],0.7,1.0)
fill_mtn(far,'far_l','far_s',0.4)
main=heights([(0,96),(35,80),(62,92),(100,50),(126,74),(148,62),(172,84),(205,44),(238,78),(262,66),(290,88),(320,76)],0.8,2.3)
fill_mtn(main,'mt_l','mt_s',0.45,('snow_l','snow_s'))
# far forested hill
hf=[int(round(99+3*math.sin(x*0.045+1)+2*math.sin(x*0.11))) for x in range(W)]
for x in range(W):
    for y in range(hf[x],H): g[y][x]='hill'
# cliff
LAKE=124
for y in range(90,LAKE):
    j=[0,1,2,1,0,2,3,1][y%8]
    for x in range(134+j,187-j):
        if y>=hf[x]+3+[0,1,0,2][x%4]:
            c='rock_l' if ((x+(y//6)*3)//7)%2==0 else 'rock_s'
            if y%7==3 and random.random()<0.6: c='rock_line'
            g[y][x]=c
# waterfall
colph=[random.randint(0,5) for _ in range(W)]
for x in range(157,164):
    for y in range(hf[x]-1,LAKE):
        c='wf2' if (y+colph[x])%6<2 else 'wf1'
        if x in (157,163) and (y+colph[x])%3!=0: c='wf2'
        g[y][x]=c
def pine(xc,base,h,L,D,tier=3,trunk=None):
    top=base-h
    for r in range(h):
        hw=(r%tier)+r//tier; y=top+r
        if not 0<=y<H: continue
        for dx in range(-hw,hw+1):
            x=xc+dx
            if 0<=x<W and g[y][x] not in ('wf1','wf2'):
                g[y][x]=L if (dx<0 or hw==0) else D
    if trunk and 0<=base<H and 0<=xc<W: g[base][xc]=trunk
x=0
while x<W:
    if not 153<=x<=167: pine(x,hf[x]+1,random.randint(5,8),'ht_l','ht_d')
    x+=random.randint(3,5)
body=[]
for _ in range(700):
    x=random.randrange(W); y=random.randint(hf[x]+4,LAKE-1); body.append((y,x))
for y,x in sorted(body):
    if g[y][x]=='hill' or g[y][x] in('ht_l','ht_d'): pine(x,y,random.randint(4,7),'ht_l','ht_d')
# lake
for y in range(LAKE,H):
    for x in range(W): g[y][x]='water'
for _ in range(140):
    y=random.randint(LAKE+1,150); x=random.randrange(W); n=random.randint(3,9)
    c='water_hi' if random.random()<0.55 else 'water_d'
    for i in range(n):
        if x+i<W: g[y][x+i]=c
for x in range(W): g[LAKE][x]='water_d'
for y in range(LAKE,138):
    for x in range(155,166):
        if (y%2==0 and (x+y)%3!=0): g[y][x]='water_hi'
# mist
for dy in range(-5,3):
    for dx in range(-10,11):
        r=(dx/10)**2+((dy+1)/4)**2
        if r<=1 and (r<0.35 or (dx+dy)%2==0): g[LAKE+dy][160+dx]='mist'
# near hills
hn=[int(round(136-30*min(1.4,abs(x-160)/100)**1.2+2*math.sin(x*0.13))) for x in range(W)]
for x in range(W):
    for y in range(hn[x],H): g[y][x]='near'
x=0
while x<W:
    pine(x,hn[x]+2,random.randint(10,16),'nt_l','nt_d',4,'trunk'); x+=random.randint(4,7)
body=[]
for _ in range(500):
    x=random.randrange(W); y=random.randint(min(H-1,hn[x]+5),H-1); body.append((y,x))
for y,x in sorted(body): pine(x,y,random.randint(9,15),'nt_l','nt_d',4)
P={
'day':dict(sky=[(58,120,200),(78,142,214),(104,164,226),(134,186,236),(168,208,242),(200,226,246)],
 far_l=(150,176,208),far_s=(128,156,194),mt_l=(120,134,160),mt_s=(86,98,130),snow_l=(244,248,252),snow_s=(188,206,230),
 hill=(44,96,72),ht_l=(64,124,84),ht_d=(34,80,64),rock_l=(140,132,124),rock_s=(98,92,96),rock_line=(74,68,76),
 wf1=(250,252,255),wf2=(176,216,240),mist=(214,234,246),water=(62,128,176),water_hi=(126,184,216),water_d=(44,100,150),
 near=(22,60,44),nt_l=(40,92,56),nt_d=(16,46,38),trunk=(48,34,24)),
'morning':dict(sky=[(92,96,160),(140,116,172),(196,136,168),(236,160,148),(250,190,140),(254,218,160)],
 far_l=(206,160,170),far_s=(170,136,166),mt_l=(190,140,140),mt_s=(112,96,138),snow_l=(255,226,206),snow_s=(190,170,200),
 hill=(60,84,88),ht_l=(96,116,92),ht_d=(46,68,80),rock_l=(176,138,124),rock_s=(112,92,108),rock_line=(84,68,88),
 wf1=(255,244,232),wf2=(220,196,210),mist=(248,222,214),water=(150,130,160),water_hi=(250,196,160),water_d=(104,100,144),
 near=(30,46,56),nt_l=(58,74,66),nt_d=(22,34,46),trunk=(40,30,34)),
'afternoon':dict(sky=[(70,128,196),(104,152,204),(150,178,206),(200,200,190),(236,212,160),(250,214,130)],
 far_l=(196,180,170),far_s=(160,156,176),mt_l=(176,150,124),mt_s=(102,100,128),snow_l=(255,240,206),snow_s=(196,190,206),
 hill=(52,92,62),ht_l=(104,132,70),ht_d=(38,74,60),rock_l=(176,150,116),rock_s=(112,98,96),rock_line=(80,68,72),
 wf1=(255,250,236),wf2=(206,214,220),mist=(244,236,214),water=(84,130,160),water_hi=(236,214,160),water_d=(56,98,136),
 near=(26,56,40),nt_l=(62,92,48),nt_d=(18,42,36),trunk=(48,34,24)),
'night':dict(sky=[(8,12,34),(12,18,46),(16,26,60),(22,34,74),(28,44,88),(36,56,102)],
 far_l=(40,58,100),far_s=(32,48,88),mt_l=(48,62,100),mt_s=(26,36,70),snow_l=(150,172,214),snow_s=(84,104,156),
 hill=(16,36,52),ht_l=(26,52,64),ht_d=(12,28,44),rock_l=(58,66,92),rock_s=(36,42,66),rock_line=(24,28,48),
 wf1=(190,210,240),wf2=(110,140,196),mist=(130,156,206),water=(20,40,80),water_hi=(70,100,160),water_d=(14,28,60),
 near=(8,18,28),nt_l=(14,32,40),nt_d=(6,12,22),trunk=(10,10,16)),
}
stars=[(random.randrange(W),random.randrange(92),random.random()<0.35) for _ in range(110)]
win=Image.open("cabin_window.png")
sheet=Image.new("RGBA",(W*6,H*6))
for i,name in enumerate(['morning','day','afternoon','night']):
    p=P[name]; img=Image.new("RGBA",(W,H)); px=img.load()
    for y in range(H):
        for x in range(W):
            k=g[y][x]
            c=p['sky'][int(k[3])] if k.startswith('sky') else p[k]
            px[x,y]=c+(255,)
    if name=='night':
        for x,y,b in stars:
            if g[y][x].startswith('sky'): px[x,y]=(230,236,255,255) if b else (120,140,196,255)
    img.save(f"bg_{name}.png")
    c=img.copy(); c.alpha_composite(win)
    sheet.paste(c.resize((W*3,H*3),Image.NEAREST),((i%2)*W*3,(i//2)*H*3))
sheet.save("bg_preview.png")
