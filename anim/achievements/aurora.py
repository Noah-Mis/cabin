"""Northern lights: a slow 60-frame loop of layered curtains with rising rays, drawn with ordered dithering so the
gradients stay pixel art. Each curtain has a bright lower edge and fades upward from green through teal to violet."""
import math, json
from PIL import Image
FW,FH,N,MS=240,60,60,160
AT=(40,24)
BAYER=[[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]]
RAMP=[(206,255,220),(104,244,156),(70,214,170),(64,160,206),(108,104,214),(150,78,196),(178,70,168)]   # lower edge -> ray tips
STOPS=[0.0,0.10,0.34,0.56,0.74,0.90,1.0]
LEVELS=[0,42,80,118,156,196]                                                                         # alpha steps
# base height of lower edge, wave sizes and speeds (whole numbers of cycles per loop so it repeats seamlessly), brightness
CURTAINS=[dict(B=31,A1=7,k1=0.026,m1=1,p1=0.0,A2=3.0,k2=0.071,m2=1,p2=1.3,L=27,bright=1.00,drift=7,ph=0.0),
          dict(B=20,A1=5,k1=0.034,m1=1,p1=2.1,A2=2.5,k2=0.090,m2=2,p2=0.4,L=19,bright=0.80,drift=-5,ph=1.9),
          dict(B=38,A1=4,k1=0.019,m1=1,p1=4.0,A2=2.0,k2=0.055,m2=1,p2=2.6,L=18,bright=0.62,drift=9,ph=3.7)]
def frame(f):
    t=2*math.pi*f/N
    im=Image.new('RGBA',(FW,FH),(0,0,0,0)); px=im.load()
    cols=[]
    for c in CURTAINS:
        col=[]
        for x in range(FW):
            xs=x+c['drift']*math.sin(t+c['ph'])                                  # the whole curtain sways sideways
            yb=c['B']+c['A1']*math.sin(xs*c['k1']+c['m1']*t+c['p1'])+c['A2']*math.sin(xs*c['k2']-c['m2']*t+c['p2'])
            fold=0.55+0.45*math.sin(xs*0.021+t+c['ph']+1.8*math.sin(xs*0.008+t))  # broad bright and dim folds drifting along it
            ray=0.62+0.38*math.sin(xs*1.7+2.6*math.sin(xs*0.19+c['ph']))*math.sin(xs*0.53+c['ph'])   # fine vertical rays
            L=c['L']+8*math.sin(xs*0.043+t+c['ph'])+6*ray
            col.append((yb,max(0.0,fold)*c['bright']*(0.86+0.14*math.sin(t+c['ph'])),ray,max(8,L)))
        cols.append(col)
    for x in range(FW):
        for y in range(FH):
            best=0; bh=0
            for col in cols:
                yb,inten,ray,L=col[x]
                if y<=yb:
                    h=(yb-y)/L
                    if h>1: continue
                    a=inten*(0.45+0.55*ray)*(1-h)**0.9
                    if h<0.07: a*=1.3                                            # the crisp bright lower edge
                else:
                    d=y-yb
                    if d>3: continue
                    a=inten*0.30*(1-d/3); h=0.0                                  # soft glow just beneath it
                if a>best: best,bh=a,h
            if best<=0.03: continue
            th=(BAYER[y%4][x%4]+0.5)/16
            lv=min(len(LEVELS)-1,int(min(1.0,best)*(len(LEVELS)-1)+th))
            if lv==0: continue
            i=max(k for k,s in enumerate(STOPS) if s<=bh)
            if i<len(STOPS)-1 and (bh-STOPS[i])/(STOPS[i+1]-STOPS[i])>th: i+=1
            px[x,y]=RAMP[i]+(LEVELS[lv],)
    return im
frames=[frame(f) for f in range(N)]
sheet=Image.new('RGBA',(FW*N,FH),(0,0,0,0))
for i,f in enumerate(frames): sheet.paste(f,(i*FW,0))
sheet.save('achievement_assets/aurora.png')
a=json.load(open('achievement_assets/achievements.json'))
a['animations']['aurora']=dict(files=['aurora.png'],frame_w=FW,frame_h=FH,frames=N,ms_per_frame=MS,loop=True,anchor=[0,0],placement={'x':AT[0],'y':AT[1],'clip':'sky_mask.png'},
  note='Reward 8. Night only. A slow 60-frame loop (about 10 seconds) of three layered curtains with rising rays, green at the lower edge fading through teal to violet. Draw under the stars, clipped by the sky mask. Fade the whole layer in and out over several seconds; never cut it on or off.')
json.dump(a,open('achievement_assets/achievements.json','w'),indent=1)
sky=Image.open('anim/sky_mask.png').split()[3]
def scene(f):
    c=Image.open('bg_night.png').convert('RGBA'); l=Image.new('RGBA',c.size,(0,0,0,0)); l.alpha_composite(f,AT)
    c.alpha_composite(Image.composite(l,Image.new('RGBA',c.size,(0,0,0,0)),sky))
    c.alpha_composite(Image.open('achievement_assets/constellation_sasquatch.png'),(52,27))
    c.alpha_composite(Image.open('anim/near_forest_night.png')); c.alpha_composite(Image.open('cabin_window_night.png').convert('RGBA'))
    c.alpha_composite(Image.open('anim/mug_night.png').crop((0,0,32,44)),(205,106)); return c
chk=Image.new('RGB',(960*2,540*2))
for i,k in enumerate((0,15,30,45)): chk.paste(scene(frames[k]).resize((960,540),Image.NEAREST).convert('RGB'),((i%2)*960,(i//2)*540))
chk.save('aurora_check.png')
gf=[scene(f).resize((640,360),Image.NEAREST).convert('RGB').quantize(200) for f in frames]
gf[0].save('achievement_assets/aurora_preview.gif',save_all=True,append_images=gf[1:],duration=MS,loop=0)
