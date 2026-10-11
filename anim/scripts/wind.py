import math
from PIL import Image
FW,FH=64,24
def path(loop=True):
    pts=[]
    def add(x,y):
        p=(int(round(x)),int(round(y)))
        if not pts or pts[-1]!=p: pts.append(p)
    for i in range(200):
        u=i/199; add(3+u*31, 15-2*math.sin(u*math.pi))
    if loop:
        for i in range(300):
            f=i/299*2*math.pi; add(34+5*math.sin(f), 10+5*math.cos(f))
    for i in range(200):
        u=i/199; add(34+u*27, 15+2*math.sin(u*math.pi)*(1 if loop else -1))
    return pts
def frames(pts,L,n):
    N=len(pts); out=[]
    for k in range(n):
        s=int((k+1)/(n)*(N+L))
        im=Image.new("RGBA",(FW,FH),(0,0,0,0)); px=im.load()
        for i in range(max(0,s-L),min(N,s)):
            age=(s-1-i)/L
            a=255 if age<0.4 else (170 if age<0.75 else 90)
            x,y=pts[i]
            if 0<=x<FW and 0<=y<FH: px[x,y]=(255,255,255,a)
        out.append(im)
    return out
def sheet(fr,name):
    s=Image.new("RGBA",(FW*len(fr),FH),(0,0,0,0))
    for i,f in enumerate(fr): s.paste(f,(i*FW,0))
    s.save(name); return s
gust=frames(path(True),30,14); streak=frames(path(False),22,10)
sheet(gust,"wind_gust.png"); sheet(streak,"wind_streak.png")
# contact sheet for checking
cs=Image.new("RGBA",(FW*7,FH*4),(40,70,120,255))
for i,f in enumerate(gust): cs.alpha_composite(f,((i%7)*FW,(i//7)*FH))
for i,f in enumerate(streak): cs.alpha_composite(f,((i%7)*FW,(2+i//7)*FH))
cs.resize((FW*7*3,FH*4*3),Image.NEAREST).save("wind_check.png")
# preview gif in the scene
bg=Image.open("bg_day.png").convert("RGBA"); win=Image.open("cabin_window.png")
out=[]
T=28
for t in range(T):
    c=bg.copy()
    c.alpha_composite(gust[t%14] if t<14 else Image.new("RGBA",(FW,FH)),(70+t*5,38))
    if 8<=t<18: c.alpha_composite(streak[t-8],(150+(t-8)*4,70))
    if t>=14: c.alpha_composite(gust[t-14],(40+(t-14)*5,84))
    c.alpha_composite(win)
    out.append(c.resize((960,540),Image.NEAREST).convert("P",palette=Image.ADAPTIVE,colors=128))
out[0].save("wind_preview.gif",save_all=True,append_images=out[1:],duration=80,loop=0)
