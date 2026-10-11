"""Gold-seal versions of the folder: closed, opening and closing. Reuses the drawing code in folder.py."""
import json
from PIL import Image
src=open('folder.py').read()
src=src[:src.index('ANGLES=[')]                       # the definitions only; nothing in folder.py is re-run or overwritten
src=src.replace("cover_color(a,int(round(d))) if n>8 else (TAN_D if j==n else (TAN if d<5 else TAN_L))","cover_color(a,int(round(d)))")
ns={}; exec(src,ns)
plain=ns['cover_color']
def gold(a,d):
    if 29<=a<=39 and 1<=d<=6:
        if d in (1,6) or a in (29,39): return (184,132,28)
        if (a,d) in ((32,3),(33,2),(34,3),(35,4),(36,5),(37,4)): return (150,96,20)
        return (250,214,96)
    return plain(a,d)
ns['cover_color']=gold
build,strip,FW,FH,UP=ns['build'],ns['strip'],ns['FW'],ns['FH'],ns['UP']
ANGLES=[0,12,24,40,60,80,100,106,102]; OUT='achievement_assets'
for tag,tint in (('',(1,1,1)),('_night',(0.55,0.52,0.66))):
    fr=[build(a,tint) for a in ANGLES]
    fr[0].crop((0,UP,FW,FH+UP)).save(f'{OUT}/folder_reviewed{tag}.png')
    strip(fr).save(f'{OUT}/folder_reviewed_open{tag}.png'); strip(fr[::-1]).save(f'{OUT}/folder_reviewed_close{tag}.png')
    if not tag: day=fr
a=json.load(open(f'{OUT}/achievements.json')); A=a['animations']
A['folder_reviewed']=dict(files=['folder_reviewed.png','folder_reviewed_night.png'],frame_w=FW,frame_h=FH,frames=1,ms_per_frame=0,loop=False,anchor=[23,20],placement={'x':160,'y':149},
  note='Reward 6. The closed folder with the gold seal already on it; use in place of folder once Case Closed is earned.')
for n,what in (('folder_reviewed_open','opens'),('folder_reviewed_close','closes')):
    A[n]=dict(files=[n+'.png',n+'_night.png'],frame_w=FW,frame_h=FH+UP,frames=9,ms_per_frame=110,loop=False,anchor=[23,20+UP],placement={'x':160,'y':149},
      note=f'Reward 6. The gold-seal folder {what}. Same size, anchor and timing as folder_open, so it is a drop-in swap; the seal stays on the cover as it tips.')
for ach in a['achievements']:
    if ach['id']=='case_closed': ach['assets']=['folder_reviewed','folder_reviewed_open','folder_reviewed_close']
json.dump(a,open(f'{OUT}/achievements.json','w'),indent=1)
p=f'{OUT}/achievements_brief.md'; s=open(p).read()
old="`folder_reviewed_overlay` is drawn over the closed folder"
assert old in s
s=s.replace(old,"The folder uses the gold-seal art everywhere: `folder_reviewed` at rest, `folder_reviewed_open` when it opens and `folder_reviewed_close` when it closes")
open(p,'w').write(s)
pv=Image.new('RGBA',(9*FW*5+40,(FH+UP)*5*2+60),(168,114,58,255))
for i,f in enumerate(day):
    pv.alpha_composite(f.resize((FW*5,(FH+UP)*5),Image.NEAREST),(20+i*FW*5,20))
    pv.alpha_composite(day[::-1][i].resize((FW*5,(FH+UP)*5),Image.NEAREST),(20+i*FW*5,40+(FH+UP)*5))
pv.save('/tmp/cabin/folder_gold_check.png')
