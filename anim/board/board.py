"""The achievement board: a small pin board hung on the window's right-hand log, and the pop-up it opens."""
import json, os
from PIL import Image, ImageDraw, ImageFont
os.chdir('/tmp/cabin'); OUT='achievement_assets/board'
OL=(38,22,12); SH=(84,52,26); MID=(132,86,42); LT=(168,114,58); HI=(204,150,84)
FELT=(38,78,60); FELT_L=(58,106,80); FELT_D=(26,56,46); GOLD=(236,186,54); GOLD_L=(255,236,140); GOLD_D=(170,116,24)
PAPER=(244,240,232); PAPER_D=(206,200,198); PAPER_E=(176,170,172); INK=(96,84,76); RED=(176,58,48); BRASS=(206,170,90)
def rect(im,x0,y0,x1,y1,c):
    for y in range(max(0,y0),min(im.height,y1+1)):
        for x in range(max(0,x0),min(im.width,x1+1)): im.putpixel((x,y),c+(255,))
def frame(im,x0,y0,x1,y1,c):
    rect(im,x0,y0,x1,y0,c); rect(im,x0,y1,x1,y1,c); rect(im,x0,y0,x0,y1,c); rect(im,x1,y0,x1,y1,c)
def tint(im,t):
    o=im.copy(); px=o.load()
    for y in range(o.height):
        for x in range(o.width):
            r,g,b,a=px[x,y]
            if a: px[x,y]=(int(r*t[0]),int(g*t[1]),int(b*t[2]),a)
    return o
# ---------------------------------------------------------------- the small board in the scene
BW,BH=18,31; BOARD_AT=(288,48)
b=Image.new('RGBA',(BW,BH),(0,0,0,0))
b.putpixel((8,0),(150,156,170,255)); b.putpixel((9,0),(96,100,112,255))                     # nail
for i in range(1,5):                                                                         # string down to both corners
    b.putpixel((8-i*2+1,i),(214,200,170,255)); b.putpixel((9+i*2-1,i),(214,200,170,255))
    b.putpixel((8-i*2+2,i),(214,200,170,255)); b.putpixel((9+i*2-2,i),(214,200,170,255))
rect(b,0,5,BW-1,BH-1,OL); rect(b,1,6,BW-2,BH-2,MID); rect(b,1,6,BW-2,6,HI); rect(b,1,6,1,BH-2,LT); rect(b,BW-2,7,BW-2,BH-2,SH); rect(b,2,BH-2,BW-2,BH-2,SH)
rect(b,3,8,BW-4,BH-4,OL); rect(b,4,9,BW-5,BH-5,FELT); rect(b,4,9,BW-5,9,FELT_D); rect(b,4,9,4,BH-5,FELT_D)
STAR=(7,10)                                                                                  # top slot: the final achievement
PINS=[(5+c*3+(1 if c else 0)*0, 15+r*3) for r in range(4) for c in range(3)]
PINS=[(5+c*3,15+r*3) for r in range(4) for c in range(3)]
for (x,y) in PINS: rect(b,x,y,x+1,y+1,FELT_D)                                                # empty pin holes
rect(b,STAR[0],STAR[1],STAR[0]+3,STAR[1]+2,FELT_D)
b.save(f'{OUT}/achievement_board.png'); tint(b,(0.45,0.45,0.6)).save(f'{OUT}/achievement_board_night.png')
pin=Image.new('RGBA',(2,2)); pin.putpixel((0,0),GOLD_L+(255,)); pin.putpixel((1,0),GOLD+(255,)); pin.putpixel((0,1),GOLD+(255,)); pin.putpixel((1,1),GOLD_D+(255,)); pin.save(f'{OUT}/board_pin_lit.png')
star=Image.new('RGBA',(4,3))
for x,y,c in ((1,0,GOLD_L),(2,0,GOLD_L),(0,1,GOLD_L),(1,1,(255,252,226)),(2,1,GOLD),(3,1,GOLD),(1,2,GOLD),(2,2,GOLD_D)): star.putpixel((x,y),c+(255,))
star.save(f'{OUT}/board_star_lit.png')
ol=Image.new('RGBA',(BW+2,BH+2),(0,0,0,0))                                                    # optional ready-made hover outline
for y in range(BH+2):
    for x in range(BW+2):
        inside=lambda xx,yy: 0<=xx<BW and 0<=yy<BH and b.getpixel((xx,yy))[3]>0
        if not inside(x-1,y-1) and any(inside(x-1+dx,y-1+dy) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))): ol.putpixel((x,y),(0,0,0,255))
ol.save(f'{OUT}/achievement_board_outline.png')
# ---------------------------------------------------------------- the pop-up
PW,PH=288,164; AT=(16,8)
GLY={'A':["010","101","111","101","101"],'C':["011","100","100","100","011"],'E':["111","100","110","100","111"],'H':["101","101","111","101","101"],
 'I':["1","1","1","1","1"],'M':["10001","11011","10101","10001","10001"],'N':["1001","1101","1011","1001","1001"],'S':["011","100","010","001","110"],
 'T':["111","010","010","010","010"],'V':["101","101","101","101","010"]}
def text(im,s,x,y,c,sc=1):
    for ch in s:
        g=GLY[ch]
        for j,row in enumerate(g):
            for i,bit in enumerate(row):
                if bit=='1': rect(im,x+i*sc,y+j*sc,x+i*sc+sc-1,y+j*sc+sc-1,c)
        x+=(len(g[0])+1)*sc
def tw(s,sc=1): return (sum(len(GLY[c][0])+1 for c in s)-1)*sc
p=Image.new('RGBA',(PW,PH),(0,0,0,0))
rect(p,0,0,PW-1,PH-1,OL); rect(p,1,1,PW-2,PH-2,MID)                                           # plank frame
for x in range(1,PW-1):
    for y in list(range(1,7))+list(range(PH-7,PH-1)):
        if (x*7+y*13)%31<3: p.putpixel((x,y),SH+(255,))
        if (x*5+y*3)%47==0: p.putpixel((x,y),LT+(255,))
for y in range(1,PH-1):
    for x in list(range(1,7))+list(range(PW-7,PW-1)):
        if (y*7+x*13)%31<3: p.putpixel((x,y),SH+(255,))
rect(p,1,1,PW-2,1,HI); rect(p,1,1,1,PH-2,LT); rect(p,PW-2,2,PW-2,PH-2,SH); rect(p,2,PH-2,PW-2,PH-2,SH)
for (x,y) in ((3,3),(PW-5,3),(3,PH-5),(PW-5,PH-5)): rect(p,x,y,x+1,y+1,BRASS); p.putpixel((x+1,y+1),OL+(255,))   # corner tacks
rect(p,7,7,PW-8,PH-8,OL); rect(p,8,8,PW-9,PH-9,FELT); rect(p,8,8,PW-9,9,FELT_D); rect(p,8,8,9,PH-9,FELT_D)
for y in range(10,PH-9):
    for x in range(10,PW-9):
        if (x*11+y*17)%53==0: p.putpixel((x,y),FELT_L+(255,))                                 # felt nap
title='ACHIEVEMENTS'; tx=(PW-tw(title,2))//2
rect(p,tx-9,10,tx+tw(title,2)+8,26,OL); rect(p,tx-8,11,tx+tw(title,2)+7,25,BRASS); rect(p,tx-8,11,tx+tw(title,2)+7,11,GOLD_L); rect(p,tx-8,25,tx+tw(title,2)+7,25,GOLD_D)
text(p,title,tx,13,OL,2)
for x in (tx-6,tx+tw(title,2)+4): rect(p,x,17,x+1,18,GOLD_D)
CLOSE=(264,11,274,21); rect(p,*CLOSE,OL); rect(p,CLOSE[0]+1,CLOSE[1]+1,CLOSE[2]-1,CLOSE[3]-1,RED)
for i in range(5):
    for x,y in ((CLOSE[0]+3+i,CLOSE[1]+3+i),(CLOSE[2]-3-i,CLOSE[1]+3+i)): p.putpixel((x,y),PAPER+(255,))
SLOT=26; ORIGIN=(15,34); STEP=(29,33)
def slot_pos(i):
    r,c=(i//5,i%5) if i<10 else (2,1+(i-10))
    return ORIGIN[0]+c*STEP[0],ORIGIN[1]+r*STEP[1]
SLOTS=[slot_pos(i) for i in range(13)]
for (x,y) in SLOTS:                                                                            # recessed squares for the 16x16 badges
    rect(p,x,y,x+SLOT-1,y+SLOT-1,FELT_D); rect(p,x+1,y+1,x+SLOT-1,y+SLOT-1,(30,64,50)); rect(p,x+SLOT-1,y,x+SLOT-1,y+SLOT-1,FELT_L); rect(p,x,y+SLOT-1,x+SLOT-1,y+SLOT-1,FELT_L)
sel=Image.new('RGBA',(SLOT+4,SLOT+4),(0,0,0,0)); frame(sel,0,0,SLOT+3,SLOT+3,OL); frame(sel,1,1,SLOT+2,SLOT+2,GOLD); frame(sel,2,2,SLOT+1,SLOT+1,GOLD_D)
for (x,y) in ((1,1),(SLOT+2,1),(1,SLOT+2),(SLOT+2,SLOT+2)): sel.putpixel((x,y),GOLD_L+(255,))
sel.save(f'{OUT}/board_slot_selected.png')
BAR=(15,138,157,147); rect(p,*BAR,OL); rect(p,BAR[0]+1,BAR[1]+1,BAR[2]-1,BAR[3]-1,FELT_D)       # progress trough, filled by code
NOTE=(170,32,276,152)                                                                          # the pinned note with details
rect(p,NOTE[0]+2,NOTE[1]+2,NOTE[2]+2,NOTE[3]+2,FELT_D); rect(p,*NOTE,OL); rect(p,NOTE[0]+1,NOTE[1]+1,NOTE[2]-1,NOTE[3]-1,PAPER)
rect(p,NOTE[0]+1,NOTE[3]-3,NOTE[2]-1,NOTE[3]-1,PAPER_D)
tk=((NOTE[0]+NOTE[2])//2,NOTE[1]-1); rect(p,tk[0]-1,tk[1]-1,tk[0]+2,tk[1]+2,OL); rect(p,tk[0],tk[1],tk[0]+1,tk[1]+1,RED); p.putpixel((tk[0],tk[1]),(236,120,104,255))
BIG=(178,40,209,71); rect(p,BIG[0]-1,BIG[1]-1,BIG[2]+1,BIG[3]+1,PAPER_E)                         # where the badge is drawn at 2x
rect(p,NOTE[0]+7,78,NOTE[2]-7,78,PAPER_D); rect(p,NOTE[0]+7,112,NOTE[2]-7,112,PAPER_D)
p.save(f'{OUT}/popup_board.png')
box=lambda r:{"x":r[0],"y":r[1],"w":r[2]-r[0]+1,"h":r[3]-r[1]+1}
LAY={"note":"Native pixels. Board numbers are on the 320x180 canvas; pop-up regions are relative to the top-left of popup_board.png.",
 "board":{"files":["achievement_board.png","achievement_board_night.png"],"w":BW,"h":BH,"canvas_x":BOARD_AT[0],"canvas_y":BOARD_AT[1],
   "outline_file":"achievement_board_outline.png","outline_offset":[-1,-1],
   "pin":{"file":"board_pin_lit.png","positions":[list(q) for q in PINS],"order":"achievements 0-11 in achievements.json order"},
   "star":{"file":"board_star_lit.png","position":list(STAR),"for":"woodsman"}},
 "popup":{"file":"popup_board.png","w":PW,"h":PH,"canvas_x":AT[0],"canvas_y":AT[1],
   "slots":[{"x":x,"y":y,"w":SLOT,"h":SLOT,"badge_x":x+5,"badge_y":y+5} for x,y in SLOTS],
   "selected_file":"board_slot_selected.png","selected_offset":[-2,-2],
   "regions":{"close":box(CLOSE),"progress_bar":box((BAR[0]+1,BAR[1]+1,BAR[2]-1,BAR[3]-1)),"progress_text":box((15,150,157,157)),
     "detail_badge_2x":box(BIG),"detail_name":box((214,40,270,71)),"detail_description":box((178,82,269,108)),"detail_reward":box((178,116,269,146))},
   "colors":{"ink":"#60544C","ink_dark":"#54341A","heading":"#B03A30","progress_fill":"#ECBA36","progress_fill_light":"#FFEC8C","text_on_felt":"#E6DCC0","backdrop":"rgba(20,12,6,0.6)"}}}
json.dump(LAY,open(f'{OUT}/board_layout.json','w'),indent=2)
# ---------------------------------------------------------------- mockups
A=json.load(open('achievement_assets/achievements.json'))['achievements']; badges=Image.open('achievement_assets/badges.png').convert('RGBA')
EARNED={0,1,3,5,6,8}; SELECT=1
def scene(t,win,tag,board):
    c=Image.open(f'bg_{t}.png').convert('RGBA'); c.alpha_composite(Image.open(f'anim/near_forest_{t}.png')); c.alpha_composite(Image.open(win).convert('RGBA'))
    c.alpha_composite(Image.open(f'anim/mug{tag}.png').crop((0,0,32,44)),(205,106)); c.alpha_composite(Image.open(f'anim/cig_pack{tag}.png'),(94,135)); c.alpha_composite(Image.open(f'anim/folder{tag}.png'),(137,129))
    c.alpha_composite(Image.open(f'{OUT}/{board}'),BOARD_AT)
    for i in sorted(EARNED):
        if i<12: c.alpha_composite(pin,(BOARD_AT[0]+PINS[i][0],BOARD_AT[1]+PINS[i][1]))
    return c
day=scene('day','cabin_window.png','','achievement_board.png'); hov=day.copy(); hov.alpha_composite(ol,(BOARD_AT[0]-1,BOARD_AT[1]-1))
ngt=scene('night','cabin_window_night.png','_night','achievement_board_night.png')
m=Image.new('RGB',(960*3,540)); 
for i,im in enumerate((day,hov,ngt)): m.paste(im.resize((960,540),Image.NEAREST).convert('RGB'),(i*960,0))
m.save(f'{OUT}/board_mockup_scene.png')
z=Image.new('RGB',(3*46*10,44*10))
for i,im in enumerate((day,hov,ngt)): z.paste(im.crop((276,42,322,86)).resize((460,440),Image.NEAREST).convert('RGB'),(i*460,0))
z.save('/tmp/cabin/board_zoom.png')
S=4; c=day.copy(); c.alpha_composite(Image.new('RGBA',c.size,(20,12,6,153))); pm=p.copy()
for i,(x,y) in enumerate(SLOTS):
    f=i if i in EARNED else 13; pm.alpha_composite(badges.crop((f*16,0,f*16+16,16)),(x+5,y+5))
pm.alpha_composite(sel,(SLOTS[SELECT][0]-2,SLOTS[SELECT][1]-2))
fill=int((BAR[2]-BAR[0]-1)*len(EARNED)/13); rect(pm,BAR[0]+1,BAR[1]+1,BAR[0]+fill,BAR[3]-1,GOLD); rect(pm,BAR[0]+1,BAR[1]+1,BAR[0]+fill,BAR[1]+2,GOLD_L)
pm.alpha_composite(badges.crop((SELECT*16,0,SELECT*16+16,16)).resize((32,32),Image.NEAREST),(BIG[0],BIG[1]))
c.alpha_composite(pm,AT); c=c.resize((320*S,180*S),Image.NEAREST); d=ImageDraw.Draw(c)
FP="/usr/share/fonts/truetype/dejavu/DejaVuSansMono"; F=lambda n,bo=False: ImageFont.truetype(FP+("-Bold" if bo else "")+".ttf",n)
def R(name):
    r=LAY['popup']['regions'][name]; return ((AT[0]+r['x'])*S,(AT[1]+r['y'])*S,r['w']*S,r['h']*S)
import textwrap
a=A[SELECT]
x,y,w,h=R('detail_name'); yy=y+8
for s in textwrap.wrap(a['name'],13): d.text((x,yy),s,font=F(20,True),fill=(84,52,26)); yy+=26
x,y,w,h=R('detail_description'); d.text((x,y),"HOW",font=F(13,True),fill=(176,58,48)); yy=y+20
for s in textwrap.wrap(a['desc'],40): d.text((x,yy),s,font=F(14),fill=(96,84,76)); yy+=19
x,y,w,h=R('detail_reward'); d.text((x,y),"REWARD",font=F(13,True),fill=(176,58,48)); yy=y+20
for s in textwrap.wrap(a['reward'],40): d.text((x,yy),s,font=F(14),fill=(96,84,76)); yy+=19
x,y,w,h=R('progress_text'); d.text((x,y+4),f"{len(EARNED)} of 13 earned",font=F(15,True),fill=(230,220,192))
c.convert('RGB').save(f'{OUT}/board_mockup_popup.png')
print(os.listdir(OUT))
