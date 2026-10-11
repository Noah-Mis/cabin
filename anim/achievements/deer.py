"""Extra art for the deer's new route: a small far-off deer for the clifftop, a tree cover it walks behind,
and a strip of bank at the pool so the near deer stands on land."""
import json, os
from PIL import Image
os.chdir('/tmp/cabin'); OUT='achievement_assets'
ns={}; exec(open('bg.py').read(),ns); g,hf,P,LAKE=ns['g'],ns['hf'],ns['P'],ns['LAKE']
TIMES=['morning','day','afternoon','night']
T={'day':(1,1,1),'morning':(1.0,0.84,0.88),'afternoon':(1.04,0.95,0.80),'night':(0.34,0.40,0.62)}
DE={'M':(156,108,64),'D':(104,70,44),'L':(210,174,132),'W':(250,246,236),'A':(84,58,40)}
def mix(a,b,t): return tuple(int(round(a[i]+(b[i]-a[i])*t)) for i in range(3))
def art(rows,t):
    im=Image.new('RGBA',(len(rows[0]),len(rows)),(0,0,0,0))
    for j,r in enumerate(rows):
        for i,ch in enumerate(r):
            if ch in DE: im.putpixel((i,j),tuple(min(255,int(v*m)) for v,m in zip(DE[ch],T[t]))+(255,))
    return im
FAR=[[".....AA",".....MM","WMMMMM.",".MLLLM.",".D...D.",".D...D."],
     [".....AA",".....MM","WMMMMM.",".MLLLM.","..D.D..","..D.D.."]]
for t in TIMES:
    s=Image.new('RGBA',(14,6),(0,0,0,0))
    for i,f in enumerate(FAR): s.paste(art(f,t),(i*7,0))
    s.save(f'{OUT}/deer_far_{t}.png')
# clifftop path: the rim of the cliff to the left of the falls
PATH=[[x,hf[x]+2] for x in range(128,151)]
# cover: the far trees to the left of the cliff, redrawn over the far deer so it walks behind them
CX0,CY0,CX1,CY1=120,90,135,112
for t in TIMES:
    im=Image.new('RGBA',(CX1-CX0+1,CY1-CY0+1),(0,0,0,0))
    for y in range(CY0,CY1+1):
        for x in range(CX0,CX1+1):
            if g[y][x] in ('ht_l','ht_d','hill'): im.putpixel((x-CX0,y-CY0),P[t][g[y][x]]+(255,))
    im.save(f'{OUT}/far_trees_cover_{t}.png')
# bank: grass over earth along the pool's left edge, ending in a point where the deer drinks
BX0,BY0=118,124
ROWS=[(118,151,'grass'),(118,152,'earth'),(121,151,'dark'),(125,149,'shade')]
for t in TIMES:
    p=P[t]; im=Image.new('RGBA',(36,4),(0,0,0,0))
    for j,(x0,x1,kind) in enumerate(ROWS):
        for x in range(x0,x1+1):
            if kind=='grass': c=p['ht_l'] if (x*3)%7<4 else p['ht_d']
            elif kind=='earth': c=p['rock_s'] if (x*5)%9<6 else p['rock_l']
            elif kind=='dark': c=p['rock_line']
            else: c=p['water_d']
            if kind=='grass' and x>=150: c=p['rock_l']                                   # bare stone at the tip
            im.putpixel((x-BX0,j),c+(255,))
    for x in (126,139,147): im.putpixel((x-BX0,0),p['ht_l']+(255,))
    im.save(f'{OUT}/pond_bank_{t}.png')
a=json.load(open(f'{OUT}/achievements.json')); A=a['animations']
A['deer_far']=dict(files=[f'deer_far_{t}.png' for t in TIMES],frame_w=7,frame_h=6,frames=2,ms_per_frame=240,loop=True,anchor=[3,5],
  placement={'path':PATH,'path_note':'each entry is [x, y] for the feet; walk it one entry per frame','cover':'far_trees_cover_<time>.png'},
  note='A small, distant deer for the clifftop. Faces right; mirror to walk left. Frame 0 is also the standing pose.')
A['far_trees_cover']=dict(files=[f'far_trees_cover_{t}.png' for t in TIMES],frame_w=CX1-CX0+1,frame_h=CY1-CY0+1,frames=1,ms_per_frame=0,loop=False,anchor=[0,0],placement={'x':CX0,'y':CY0},
  note='Draw immediately after deer_far, only while it is on screen. It repaints the far trees left of the cliff so the small deer passes behind them.')
A['pond_bank']=dict(files=[f'pond_bank_{t}.png' for t in TIMES],frame_w=36,frame_h=4,frames=1,ms_per_frame=0,loop=False,anchor=[0,0],placement={'x':BX0,'y':BY0},
  note='Always drawn, for every visitor, straight after the waterfall and before the deer and near forest. A strip of grassy bank along the left of the pool, so the deer stands on land.')
bank={'start_x':97,   # 100 showed an ear tip above the front trees on the first frame
      'stop_x':144,'faces':'right','feet_y':123}
for k in ('deer_walk','deer_graze'):
    A[k]['placement']={'feet_y':123,'bank':bank,'forbidden_x':[152,320],'on':'pond_bank_<time>.png','behind':'near_forest_<time>.png'}
for ach in a['achievements']:
    if ach['id']=='cabin_fever': ach['assets']=['deer_far','far_trees_cover','deer_walk','deer_graze']
json.dump(a,open(f'{OUT}/achievements.json','w'),indent=1)
# check picture
def scene(t,far=None,near=None,cover=True):
    c=Image.open(f'bg_{t}.png').convert('RGBA'); c.alpha_composite(Image.open(f'anim/waterfall_{t}.png').crop((0,0,31,47)),(146,94))
    c.alpha_composite(Image.open(f'{OUT}/pond_bank_{t}.png'),(BX0,BY0))
    if far:
        x,fl,fr=far; y=dict((q[0],q[1]) for q in PATH)[x]; s=Image.open(f'{OUT}/deer_far_{t}.png').crop((fr*7,0,fr*7+7,6))
        if fl: s=s.transpose(Image.FLIP_LEFT_RIGHT)
        c.alpha_composite(s,(x-3,y-5)); c.alpha_composite(Image.open(f'{OUT}/far_trees_cover_{t}.png'),(CX0,CY0))
    if near:
        sheet,fr,x=near; c.alpha_composite(Image.open(f'{OUT}/{sheet}_{t}.png').crop((fr*14,0,fr*14+14,10)),(x-6,123-9))
    c.alpha_composite(Image.open(f'anim/near_forest_{t}.png')); return c.crop((104,88,184,134)).resize((640,368),Image.NEAREST).convert('RGB')
tiles=[scene('day',far=(138,False,0)),scene('day',far=(149,False,1)),scene('day',far=(133,True,1)),scene('day'),
       scene('day',near=('deer_walk',0,128)),scene('day',near=('deer_graze',0,144)),scene('day',near=('deer_graze',2,144)),scene('night',near=('deer_graze',2,144))]
o=Image.new('RGB',(2560,736))
for i,tl in enumerate(tiles): o.paste(tl,((i%4)*640,(i//4)*368))
o.save('deer_route_check.png'); print(PATH[0],PATH[-1])
