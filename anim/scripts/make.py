from PIL import Image
import random
random.seed(7)
W,H=320,180
img=Image.new("RGBA",(W,H),(0,0,0,0))
px=img.load()
OUT=(38,22,12,255); SH=(84,52,26,255); MID=(132,86,42,255); LT=(168,114,58,255); HI=(204,150,84,255)
ramp=[OUT,SH,MID,LT,HI]
def shade(i,T):
    if i==0 or i==T-1: return 0
    f=i/(T-1)
    if i==1: return 4
    if f<0.30: return 3
    if f<0.68: return 2
    return 1
def log(x,y,w,h,horiz=True,knots=1):
    L,T=(w,h) if horiz else (h,w)
    g=[[shade(t,T) for t in range(T)] for _ in range(L)]
    # grain streaks
    for _ in range(L*T//14):
        t=random.randint(2,T-3); s=random.randint(0,L-1); n=random.randint(4,16)
        d=random.choice([-1,-1,1])
        for l in range(s,min(L,s+n)):
            g[l][t]=max(1,min(4,g[l][t]+d))
    # knots
    for _ in range(knots):
        if L<30 or T<9: break
        cl=random.randint(8,L-9); ct=random.randint(4,T-5)
        for dl in range(-3,4):
            for dt in range(-2,3):
                r=(dl/3.2)**2+(dt/2.2)**2
                if r<=1 and 0<=cl+dl<L and 1<=ct+dt<T-1:
                    g[cl+dl][ct+dt]=1 if r>0.45 else 0
        g[cl][ct]=1
    for l in range(L):
        for t in range(T):
            c=ramp[g[l][t]]
            if l==0 or l==L-1: c=OUT
            X,Y=(x+l,y+t) if horiz else (x+t,y+l)
            if 0<=X<W and 0<=Y<H: px[X,Y]=c
# wall of horizontal logs
LH=18
for i in range(H//LH):
    log(-1,i*LH,W+2,LH,True,knots=random.randint(1,3))
# window geometry: frame logs around a recess through the thick wall
fx0,fy0,fx1,fy1=34,22,285,150      # front of recess (inner wall face)
bx0,by0,bx1,by1=40,24,279,130      # back of recess = see-through opening
FT=14; ST=22
for X in range(fx0-ST-2,fx1+ST+3):
    for Y in range(fy0-FT-2,fy1+FT+3):
        px[X,Y]=OUT
log(fx0-ST,fy0-1,ST,(fy1-fy0)+3,False,knots=2)
log(fx1+1,fy0-1,ST,(fy1-fy0)+3,False,knots=2)
log(fx0-ST-1,fy0-FT,(fx1-fx0)+1+2*ST+2,FT,True,knots=2)
log(fx0-ST-1,fy1+1,(fx1-fx0)+1+2*ST+2,FT,True,knots=2)
sd=fy1-by1; td=by0-fy0; wd=bx0-fx0
for Y in range(fy0,fy1+1):
    for X in range(fx0,fx1+1):
        if bx0<=X<=bx1 and by0<=Y<=by1:
            px[X,Y]=(0,0,0,0); continue
        # which face of the recess?
        if Y>by1 and fx0+wd*(fy1-Y)/sd<=X<=fx1-wd*(fy1-Y)/sd:
            px[X,Y]=LT                      # sill top, lit from outside
        elif Y<by0 and fx0+wd*(Y-fy0)/td<=X<=fx1-wd*(Y-fy0)/td:
            px[X,Y]=SH                      # underside of the top
        else:
            px[X,Y]=MID if (X*3+Y//5)%7 else SH   # side reveals
# sill grain
for _ in range(240):
    Y=random.randint(by1+2,fy1); t=(fy1-Y)/sd
    xl=int(fx0+wd*t)+2; xr=int(fx1-wd*t)-2
    X=random.randint(xl,xr-4); n=random.randint(5,20)
    c=random.choice([HI,HI,MID,MID,SH])
    if c==SH: n=min(n,7)
    for i in range(n):
        if X+i<xr: px[X+i,Y]=c
for cx,cy in ((78,142),(206,138),(255,145)):
    for dx in range(-3,4):
        for dy in range(-1,2):
            if (dx/3.2)**2+(dy/1.6)**2<=1: px[cx+dx,cy+dy]=SH
    px[cx,cy]=OUT
# shade the sill where it meets the side reveals, highlight its front lip
for Y in range(by1+1,fy1+1):
    t=(fy1-Y)/sd
    xl=round(fx0+wd*t); xr=round(fx1-wd*t)
    px[xl,Y]=OUT; px[xr,Y]=OUT
    for k in (1,2):
        if (k+Y)%2 or k==1: px[xl+k,Y]=MID; px[xr-k,Y]=MID
for X in range(fx0+1,fx1): px[X,fy1]=HI
# outlines: back opening and top corner creases
for X in range(bx0-1,bx1+2): px[X,by0-1]=OUT; px[X,by1+1]=OUT
for Y in range(by0-1,by1+2): px[bx0-1,Y]=OUT; px[bx1+1,Y]=OUT
for X in range(fx0-1,fx1+2): px[X,fy0-1]=OUT
for Y in range(fy0-1,fy1+1): px[fx0-1,Y]=OUT; px[fx1+1,Y]=OUT
# shadow under the bottom frame log
for Y in range(fy1+FT+3,fy1+FT+6):
    for X in range(fx0-ST,fx1+ST+3):
        if Y<H:
            c=px[X,Y]
            if c in ramp: px[X,Y]=ramp[max(0,ramp.index(c)-1)]
img.save("cabin_window.png")
img.resize((W*4,H*4),Image.NEAREST).save("cabin_window_4x.png")
