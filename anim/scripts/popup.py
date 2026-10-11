"""The pop-up shown when the folder is clicked: the folder lying open, seen from above.
The art leaves blank areas; the site draws real text over them (see popup_layout.json)."""
import json, os
from PIL import Image
PW,PH=288,164; AT=(16,8)                 # size, and top-left position on the 320x180 canvas
OUTL=(84,52,26); TAN=(206,170,116); TAN_M=(214,180,126); TAN_L=(224,192,140); TAN_H=(236,208,158); TAN_D=(160,124,80); TAN_B=(140,106,68)
INNER=(228,202,156); SCORE=(188,152,100)
PAPER=(244,240,232); PAPER_D=(206,200,198); PAPER_E=(176,170,172); RULE=(214,222,232); INK=(96,84,76)
STAMP=(176,58,48); NOTE=(244,220,120); NOTE_D=(212,184,88); CLIP=(150,156,170); CLIP_L=(206,212,222)
GLY={'A':["010","101","111","101","101"],'B':["110","101","110","101","110"],'C':["011","100","100","100","011"],
 'E':["111","100","110","100","111"],'J':["001","001","001","101","010"],'M':["10001","11011","10101","10001","10001"],
 'N':["1001","1101","1011","1001","1001"],'O':["010","101","101","101","010"],'P':["110","101","110","100","100"],
 'R':["110","101","110","101","101"],'S':["011","100","010","001","110"],'T':["111","010","010","010","010"],'U':["101","101","101","101","111"]}
def text_w(s): return sum(len(GLY[c][0])+1 for c in s)-1
def text(im,s,x,y,c):
    for ch in s:
        g=GLY[ch]
        for j,row in enumerate(g):
            for i,b in enumerate(row):
                if b=='1': im.putpixel((x+i,y+j),c+(255,))
        x+=len(g[0])+1
def rect(im,x0,y0,x1,y1,c):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1):
            if 0<=x<im.width and 0<=y<im.height: im.putpixel((x,y),c+(255,))
def frame(im,x0,y0,x1,y1,c):
    rect(im,x0,y0,x1,y0,c); rect(im,x0,y1,x1,y1,c); rect(im,x0,y0,x0,y1,c); rect(im,x1,y0,x1,y1,c)
TABS=[('ABOUT',118),('RESUME',160),('PROJECTS',202),('CONTACT',244)]; TW,TH=40,13
def tab(im,x,label,active):
    body=TAN_H if active else TAN_D
    rect(im,x+1,1,x+TW-2,TH,body); rect(im,x+2,0,x+TW-3,0,OUTL); rect(im,x,2,x,TH,OUTL); rect(im,x+TW-1,2,x+TW-1,TH,OUTL)
    im.putpixel((x+1,1),OUTL+(255,)); im.putpixel((x+TW-2,1),OUTL+(255,))
    if not active: rect(im,x,TH,x+TW-1,TH,OUTL)
    else: rect(im,x+1,TH,x+TW-2,TH,TAN_H)
    text(im,label,x+(TW-text_w(label))//2,4,OUTL if active else TAN_H)
im=Image.new("RGBA",(PW,PH),(0,0,0,0))
# back of the folder and the inside of the front cover
rect(im,0,TH,PW-1,PH-1,OUTL); rect(im,1,TH+1,PW-2,PH-2,TAN_M)
rect(im,1,TH+1,142,PH-2,INNER); rect(im,1,TH+1,142,TH+1,TAN_H); rect(im,1,PH-4,PW-2,PH-2,TAN)
rect(im,143,TH+1,144,PH-2,TAN_D); rect(im,141,TH+1,141,PH-2,SCORE); rect(im,146,TH+1,146,PH-2,SCORE)   # the spine
for x,_ in [(t[1],0) for t in TABS]: pass
for label,x in TABS: tab(im,x,label,False)
# right: a stack of pages, the top one blank for the site's text
rect(im,152,20,283,159,PAPER_E); rect(im,151,19,281,157,PAPER_D); rect(im,149,17,279,155,OUTL); rect(im,150,18,278,154,PAPER)
PAGE=(155,26,273,150)
# paperclip on the page
for (x0,y0,x1,y1) in ((160,13,166,24),(162,15,164,22)): frame(im,x0,y0,x1,y1,CLIP)
rect(im,160,13,160,24,CLIP_L)
# left: photo held by a clip, an index card, a sticky note, a coffee ring and the stamp
rect(im,13,25,58,78,OUTL); rect(im,14,26,57,77,PAPER); rect(im,18,30,53,65,(120,150,170)); frame(im,18,30,53,65,PAPER_E)
PHOTO=(18,30,53,65)
frame(im,30,21,36,31,CLIP); rect(im,30,21,30,31,CLIP_L)
rect(im,65,25,136,78,OUTL); rect(im,66,26,135,77,PAPER); rect(im,66,26,135,33,(214,92,84))
for y in range(42,76,8): rect(im,69,y,132,y,RULE)
CARD=(69,36,132,75)
rect(im,15,90,74,142,NOTE_D); rect(im,14,89,72,140,NOTE); rect(im,14,89,72,91,NOTE_D)
STICKY=(18,95,69,137)
import math
for a in range(0,360,3):                                   # coffee ring, a nod to the mug on the sill
    for r_,c in ((13,TAN_D),(12,TAN)):
        if a%72<60:
            x=int(108+r_*math.cos(math.radians(a))); y=int(118+r_*0.8*math.sin(math.radians(a))); im.putpixel((x,y),c+(255,))
frame(im,84,144,132,156,STAMP); frame(im,86,146,130,154,STAMP)
# close button
rect(im,4,TH+4,14,TH+14,OUTL); rect(im,5,TH+5,13,TH+13,STAMP)
for i in range(5):
    for x,y in ((7+i,TH+7+i),(11-i,TH+7+i)): im.putpixel((x,y),PAPER+(255,))
CLOSE=(4,TH+4,14,TH+14)
os.makedirs("folder_assets/popup",exist_ok=True)
im.save("folder_assets/popup/popup_folder.png")
for label,x in TABS:
    t=Image.new("RGBA",(TW,TH+1),(0,0,0,0)); tab(t,0,label,True); t.save(f"folder_assets/popup/popup_tab_{label.lower()}_active.png")
box=lambda r:{"x":r[0],"y":r[1],"w":r[2]-r[0]+1,"h":r[3]-r[1]+1}
layout={"note":"All numbers are native pixels. Regions are relative to the top-left of popup_folder.png; multiply by the canvas scale for screen pixels.",
 "popup":{"file":"popup_folder.png","w":PW,"h":PH,"canvas_x":AT[0],"canvas_y":AT[1]},
 "tabs":[{"name":l.lower(),"active_file":f"popup_tab_{l.lower()}_active.png","x":x,"y":0,"w":TW,"h":TH+1} for l,x in TABS],
 "regions":{"page":box(PAGE),"photo":box(PHOTO),"card":box(CARD),"sticky":box(STICKY),"stamp":box((87,147,129,153)),"close":box(CLOSE)},
 "colors":{"ink":"#60544C","ink_dark":"#54341A","stamp_red":"#B03A30","paper":"#F4F0E8","rule":"#D6DEE8","tan":"#CEAA74","backdrop":"rgba(20,12,6,0.6)"}}
json.dump(layout,open("folder_assets/popup/popup_layout.json","w"),indent=2)
# mockup: how it could look filled in, with grey bars standing in for text
bg=Image.open("bg_day.png").convert("RGBA"); bg.alpha_composite(Image.open("anim/near_forest_day.png")); bg.alpha_composite(Image.open("cabin_window.png").convert("RGBA"))
bg.alpha_composite(Image.open("anim/mug.png").crop((0,0,32,44)),(205,106)); bg.alpha_composite(Image.open("anim/cig_pack.png"),(94,135))
bg.alpha_composite(Image.open("anim/folder_opened.png"),(160-23,149-38))
bg.alpha_composite(Image.new("RGBA",bg.size,(20,12,6,153)))
mock=im.copy(); mock.alpha_composite(Image.open("folder_assets/popup/popup_tab_resume_active.png"),(160,0))
def bars(x0,y0,x1,y1,step,c,seed=3):
    y=y0; k=seed
    while y<=y1-1:
        k=(k*37+11)%17; w=int((x1-x0)*(0.55+0.45*(k/16)))
        rect(mock,x0,y,x0+w,y+1,c); y+=step
rect(mock,PAGE[0],PAGE[1],PAGE[0]+60,PAGE[1]+3,INK); bars(PAGE[0],PAGE[1]+9,PAGE[2],PAGE[1]+40,5,PAPER_E)
rect(mock,PAGE[0],PAGE[1]+46,PAGE[0]+40,PAGE[1]+48,STAMP); bars(PAGE[0],PAGE[1]+53,PAGE[2],PAGE[1]+84,5,PAPER_E,5)
rect(mock,PAGE[0],PAGE[1]+90,PAGE[0]+48,PAGE[1]+92,STAMP); bars(PAGE[0],PAGE[1]+97,PAGE[2],PAGE[3],5,PAPER_E,9)
bars(CARD[0],CARD[1]+1,CARD[2],CARD[3],8,INK,4); bars(STICKY[0],STICKY[1],STICKY[2],STICKY[3],7,TAN_B,6)
bg.alpha_composite(mock,AT)
bg.resize((1280,720),Image.NEAREST).save("folder_assets/popup/popup_mockup.png")
