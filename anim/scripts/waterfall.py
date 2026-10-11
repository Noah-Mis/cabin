"""The waterfall in a classic 16-bit style: one straight fall drawn with a hand-placed streak pattern that scrolls,
a dark outline, a billowing foam mound with surges and arcing droplets where it lands, and ripple rings. Flat colours only: no transparency,
no soft gradients, 8 frames. Colours come from each time of day's own palette."""
import math, json, os, shutil
from PIL import Image
os.chdir('/tmp/cabin')
ns={}; exec(open('bg.py').read(),ns)                      # the scene map: what every background pixel is
g,hf,P,LAKE=ns['g'],ns['hf'],ns['P'],ns['LAKE']
NEAR=('near','nt_l','nt_d','trunk'); OLD=('wf1','wf2','mist'); ROCK=('rock_l','rock_s','rock_line'); WATER=('water','water_hi','water_d')
X0,Y0,PW,PH=146,94,31,47; N,MS=8,110; CX=160
def mix(a,b,t): return tuple(int(round(a[i]+(b[i]-a[i])*t)) for i in range(3))
# The streak tile: one string per column of the fall, left to right, read downward. 1 = bright, 2 = mid, D = deep.
# It scrolls down one pixel a frame and repeats every 8, which gives the classic marching-streaks look.
TILE=["DD22D222","2111W211","11121111","1W111221","12111112","2211211W","D22DD222"]     # W = a few pure highlights
FOAM=[["....M.M.M....","...MWMWMWM...","..MWWWWWWWM..",".MWMWWWWWMWM.","M.MWMWMWMWM.M","..M.M.M.M.M.."],
      [".....M.M.....","..M.MWMWM.M..","...MWWWWWM...","..MWWMWMWWM..",".M.MWMWMWM.M.","M...M.M.M...M"],
      ["...M.....M...","....MWMWM....","..MWWWWWWWM..",".M.WMWWWMW.M.","..M.MWMWM.M..",".M..M...M..M."]]
FOAM_SEQ=[0,0,1,1,2,2,1,1]; RIPPLE=[0,0,1,1,2,2,1,1]
def falls(x,y):
    if (x,y) in BULGE: return True
    if LAKE-4<=y<LAKE and abs(x-CX)==4: return True                                        # the fall flares one pixel wider at its foot
    return abs(x-CX)<=3 and (hf[x]-1+(1 if abs(x-CX)==3 else 0))<=y<LAKE                   # rounded shoulders at the lip
# A rock on the right side of the fall partway down: L = lit top, S = body, D = shadowed underside.
BOULDER={(162,110):'L',(163,110):'L',(161,111):'L',(162,111):'S',(163,111):'S',(161,112):'S',(162,112):'D',(163,112):'D'}
CREST=((162,109),(163,109),(161,110))                                                        # foam piling against its top
LEE={(161,113):0,(162,113):0,(163,113):0,(161,114):1,(162,114):0,(163,114):1,(162,115):0,(163,115):1,(162,116):1}   # thin water in its shelter, closing back up
SIDE=tuple((164,y) for y in range(109,116))                                                  # the water it pushes aside runs fast and bright down its right
BULGE=SIDE                                                                                   # so the fall swells outward on the right only; the left runs straight
MOSS=((155,104),(155,105),(165,108),(165,109),(155,116),(165,117),(154,110))                  # moss on the wet rock beside it
DROPS=[((152,120),(169,119)),((151,118),(170,117)),((150,119),(171,118)),((151,121),(170,120))]   # spray hopping off the foam
def build(t):
    p=P[t]; WF1,WF2,MIST=p['wf1'],p['wf2'],p['mist']
    WFD=mix(WF2,p['rock_s'],0.4); EDGE=p['rock_line']; WHITE=mix(WF1,(255,255,255),0.6 if t!='night' else 0.3)
    frames=[]
    for f in range(N):
        im=Image.new('RGBA',(PW,PH),(0,0,0,0)); px=im.load()
        def put(x,y,c):
            if X0<=x<X0+PW and Y0<=y<Y0+PH and g[y][x] not in NEAR: px[x-X0,y-Y0]=c+(255,)
        for y in range(Y0,Y0+PH):
            for x in range(X0,X0+PW):
                k=g[y][x]
                if k in NEAR: continue
                if falls(x,y):
                    ch=TILE[max(0,min(6,x-CX+3))][(y-f)%8]
                    c={'1':WF1,'2':WF2,'D':WFD,'W':WHITE}[ch]
                    top=hf[x]-1+(1 if abs(x-CX)==3 else 0)
                    if y==top: c=WHITE if abs(x-CX)<=2 else WF1                    # a bright cap where the water crests
                    elif y==top+1: c=WF1 if abs(x-CX)<=2 else WF2                  # and a second row easing it into the streaks
                    if abs(x-CX)==4: c=WF2 if (y+f)%2 else WF1                     # the flared foot shimmers
                    if (x,y) in BOULDER: c={'G':WHITE,'L':mix(p['rock_l'],WF1,0.3),'S':p['rock_s'],'D':EDGE}[BOULDER[(x,y)]]
                    elif (x,y) in CREST: c=WHITE if (f//2+x)%2 else WF1
                    elif (x,y) in LEE: c=WFD if (LEE[(x,y)]==0 or (y+f)%2) else WF2
                    elif (x,y) in SIDE: c={'1':WHITE,'W':WHITE,'2':WF1,'D':WF2}[TILE[5][(y-2*f)%8]]
                    put(x,y,c)
                elif k in ROCK or (k in OLD and y<LAKE):
                    if falls(x-1,y) or falls(x+1,y): put(x,y,EDGE)                 # dark outline down both sides
                    elif (x,y) in MOSS: put(x,y,p['ht_d'])
                    elif k in OLD: put(x,y,p['rock_l'] if ((x+(y//6)*3)//7)%2==0 else p['rock_s'])
                elif k in WATER or (k in OLD and y>=LAKE):
                    c=p['water']
                    if y==LAKE: c=p['water_d']
                    else:
                        rr=math.hypot(x-CX,(y-LAKE)*2.5)                              # rings spreading from the impact, one pixel a frame
                        if rr<26 and int(rr-f)%8==0: c=p['water_hi']
                        elif rr<18 and int(rr-f)%8==4 and (x+y)%2==0: c=p['water_hi']   # a fainter, broken ring between them
                    put(x,y,c)
        # --- the landing ---
        # 1. A foam mound that billows: its crest rises and falls in a travelling wave, white on top, checkered below.
        for dx in range(-8,9):
            h=max(0,5-abs(dx)*0.55)+(1 if (abs(dx)+f//2)%3==0 else 0)-(1 if (abs(dx)+f//2)%3==1 and abs(dx)>2 else 0)
            h=int(round(h))
            for j in range(h):
                y=LAKE+1-j; x=CX+dx
                c=WHITE if j>=h-1 else (WF1 if (x+y+f//2)%2 else MIST)
                if j==0 and abs(dx)>5: c=MIST
                put(x,y,c)
        # 2. Two surges of foam running outward along the water on each side, one behind the other.
        for ph in (0,4):
            d=5+(f+ph)%8
            for sgn in (-1,1):
                put(CX+sgn*d,LAKE,WHITE); put(CX+sgn*(d+1),LAKE,WF1); put(CX+sgn*(d-1),LAKE+1,MIST)
                if d<10: put(CX+sgn*d,LAKE-1,WF1)                                  # the surge stands a pixel proud while it is young
        # 3. Droplets thrown up and out in arcs, falling back into the pool.
        for sgn,vx,vy,off in ((-1,0.9,2.3,0),(1,1.0,2.5,3),(-1,1.5,1.8,5),(1,1.6,1.9,1),(-1,0.5,2.8,6),(1,0.6,2.9,4)):
            tt=(f+off)%8
            x=CX+sgn*(3+vx*tt); y=LAKE-4-vy*tt+0.42*tt*tt
            if y<LAKE: put(int(round(x)),int(round(y)),WHITE if tt<3 else WF1)
        frames.append(im)
    return frames
ALL={}
for t in P:
    fr=build(t); s=Image.new('RGBA',(PW*N,PH),(0,0,0,0))
    for i,f_ in enumerate(fr): s.paste(f_,(i*PW,0))
    s.save(f'anim/waterfall_{t}.png'); ALL[t]=fr
m=json.load(open('anim/manifest.json'))
m['animations']['waterfall']=dict(files=[f'waterfall_{t}.png' for t in ('morning','day','afternoon','night')],frame_w=PW,frame_h=PH,frames=N,ms_per_frame=MS,loop=True,anchor=[0,0],placement={'x':X0,'y':Y0},
  note='Always-on patch drawn over the background, before the near forest. Classic 16-bit style: a straight fall with scrolling streaks, a dark outline, chunky foam and two-tone ripples. Every pixel is fully opaque. It fully covers the waterfall baked into the background.')
json.dump(m,open('anim/manifest.json','w'),indent=2)
def scene(t,f_):
    c=Image.open(f'bg_{t}.png').convert('RGBA'); c.alpha_composite(f_,(X0,Y0)); c.alpha_composite(Image.open(f'anim/near_forest_{t}.png'))
    c.alpha_composite(Image.open('cabin_window_night.png' if t=='night' else 'cabin_window.png').convert('RGBA')); return c
Z=10; box=(126,88,196,134)
chk=Image.new('RGB',(4*70*Z,2*46*Z))
for i,(t,k) in enumerate((('day',0),('day',2),('day',4),('day',6),('morning',1),('afternoon',3),('night',5),('day',7))):
    chk.paste(scene(t,ALL[t][k]).crop(box).resize((70*Z,46*Z),Image.NEAREST).convert('RGB'),((i%4)*70*Z,(i//4)*46*Z))
chk.save('waterfall_check.png')
wide=Image.new('RGB',(960*2,540)); wide.paste(scene('day',ALL['day'][4]).resize((960,540),Image.NEAREST).convert('RGB'),(0,0)); wide.paste(scene('night',ALL['night'][4]).resize((960,540),Image.NEAREST).convert('RGB'),(960,0)); wide.save('waterfall_wide.png')
gf=[scene('day',f_).crop((96,70,224,142)).resize((640,360),Image.NEAREST).convert('RGB').quantize(160) for f_ in ALL['day']]
gf[0].save('anim/previews/preview_waterfall.gif',save_all=True,append_images=gf[1:],duration=MS,loop=0)
shutil.copy('waterfall.py','anim/scripts/waterfall.py')
