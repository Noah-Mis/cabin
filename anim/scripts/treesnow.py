import math, random
from PIL import Image
exec(open('/tmp/cabin/bg.py').read().split('win=Image.open')[0])   # g, P, W, H (no re-save/composite)
NEAR={'nt_l','nt_d','trunk'}; FARF={'ht_l','ht_d'}
TIMESL=('morning','day','afternoon','night')

def exposed(x,y,group):
    if g[y][x] not in group: return False
    return (y==0) or (g[y-1][x] not in group)                      # a top surface of a tier

def build(group,seed,depth,skip):
    """
    Snow capping the sunny tops of this tree group, piled `depth` px down each tier.
    Deterministic and monotonic (depth up / skip down) so each heavier stage is a
    superset of the lighter one -> cycling the stages up looks like snow piling on.
    """
    caps=[]; seen=set()
    def lay(x,y,k):
        if 0<=x<W and 0<=y<H and (x,y) not in seen and g[y][x] in group:
            seen.add((x,y)); caps.append((x,y,'l' if k<=1 else 's')); return True
        return False
    for y in range(H):
        for x in range(W):
            if not exposed(x,y,group): continue
            if random.Random(x*131+y*17+seed).random()<skip: continue
            for k in range(depth):                                 # pile straight down the tier top
                if not lay(x,y+k,k): break
            for k in range(1,depth):                               # spread along the sunward (left) edge
                if x-k>=0 and g[y][x-k] in group and g[y-1][x-k] not in group: lay(x-k,y,0)
                else: break
            if x+1<W and g[y][x+1] in group and g[y-1][x+1] not in group: lay(x+1,y,0)
    return caps

# accumulation stages: light dusting -> heavy blanket (each a superset of the previous)
STAGES=[dict(depth=2,skip=0.34),dict(depth=3,skip=0.16),dict(depth=4,skip=0.06),dict(depth=6,skip=0.0)]
for si,st in enumerate(STAGES,1):
    NC=build(NEAR,1,**st); FC=build(FARF,2,**st)
    for t in TIMESL:
        sl=P[t]['snow_l']; ss=P[t]['snow_s']
        for caps,layer in ((NC,'near'),(FC,'far')):
            im=Image.new('RGBA',(W,H),(0,0,0,0))
            for x,y,k in caps: im.putpixel((x,y),(sl if k=='l' else ss)+(255,))
            im.save(f'/tmp/cabin/anim/tree_snow_{layer}_{t}_s{si}.png')
    print(f"stage {si}: near {len(NC)} far {len(FC)}")

from PIL import ImageDraw
def compose(t,si):
    b=Image.open(f'/tmp/cabin/bg_{t}.png').convert('RGBA')
    b.alpha_composite(Image.open(f'/tmp/cabin/anim/tree_snow_far_{t}_s{si}.png'))
    b.alpha_composite(Image.open(f'/tmp/cabin/anim/near_forest_{t}.png'))
    b.alpha_composite(Image.open(f'/tmp/cabin/anim/tree_snow_near_{t}_s{si}.png'))
    try: b.alpha_composite(Image.open('/tmp/cabin/cabin_window.png').convert('RGBA'))
    except: pass
    return b
cols=2; rows=(len(STAGES)+1)//2
pv=Image.new('RGB',(W*2*cols,H*2*rows),(20,20,24)); d=ImageDraw.Draw(pv)
for i in range(len(STAGES)):
    r,c=divmod(i,cols); pv.paste(compose('day',i+1).resize((W*2,H*2),Image.NEAREST).convert('RGB'),(c*W*2,r*H*2))
    d.text((c*W*2+6,r*H*2+4),f"stage {i+1}",fill=(255,255,255))
pv.save('/tmp/cabin/tree_snow_stages.png')
compose('night',len(STAGES)).resize((W*2,H*2),Image.NEAREST).save('/tmp/cabin/_snow_night.png')
