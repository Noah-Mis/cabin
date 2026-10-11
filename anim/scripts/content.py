"""Resume content reshaped for the folder pop-up, plus mockups that draw it over the art."""
import json, textwrap
from PIL import Image, ImageDraw, ImageFont
C={
 "card":{"header":"PROFILE","name":"Noah A. Misukonis","lines":["B.S. Computer Science","Missouri S&T, Rolla MO","Expected May 2028 · GPA 3.52"]},
 "stamp":"CLASS OF 2028",
 "sticky":{"title":"find me:","links":[{"label":"misukonisn@gmail.com","href":"mailto:misukonisn@gmail.com"},
            {"label":"linkedin.com/in/noah-misukonis","href":"https://www.linkedin.com/in/noah-misukonis/"},
            {"label":"[ resume.pdf ]","href":"Noah_Misukonis_2026_Resume.pdf"}]},
 "tabs":{
  "about":[
   {"heading":"About","text":["Computer Science student with hands-on software engineering experience building cloud infrastructure, CI/CD pipelines, and enterprise integrations at State Farm.","I combine strong technical fundamentals with leadership across technical and athletic teams."]},
   {"heading":"Outside the terminal","items":[
     {"title":"Varsity Track and Field, Pole Vault","meta":"Aug 2024 – Present","points":["NCAA Division II pole vaulter for Missouri S&T"]},
     {"title":"Intercollegiate Knights, service organization","meta":"Aug 2024 – Present","points":[]},
     {"title":"Hasselman Alumni House Assistant","meta":"Jan 2025 – Present","points":["Welcome and assist alumni guests at weekly on-campus events"]}]},
   {"heading":"Honors & awards","bullets":["2026 GLVC Conference Pole Vault Champion","2024 State Farm Scholar Athlete of the Year","2024 Illinois State Scholar","Seal of Biliteracy in French"]}],
  "resume":[
   {"heading":"Education","items":[{"title":"Missouri University of Science & Technology","meta":"Expected May 2028","points":["B.S. Computer Science · GPA 3.52/4.0","Coursework: Algorithms, Database Systems, Operating Systems, Data Structures, Discrete Mathematics"]}]},
   {"heading":"Experience","items":[
     {"title":"Software Engineering Intern, State Farm","meta":"May – Aug 2026 · Bloomington, IL","points":[
       "Engineered and maintained internal applications on AWS (ROSA, ECR, ECS) with Docker and GitLab CI/CD, streamlining build and deployment workflows",
       "Built and scaled integrations across Slack, Jira, and Confluence, and led the migration of Slack integrations from test to production",
       "Independently architected and shipped two company-wide Slack applications",
       "Designed and deployed a company-wide outage notification system, cutting mean-time-to-detect by 14 minutes"]},
     {"title":"House Manager, Lambda Chi Alpha","meta":"Dec 2025 – Dec 2026 · Rolla, MO","points":[
       "Oversaw the fraternity house, keeping it clean and well-maintained",
       "Planned and led house-wide improvement projects with fraternity leadership and members"]},
     {"title":"iGEM Design Team Lead","meta":"Jan 2025 – May 2026 · Rolla, MO","points":["International Genetically Engineered Machine team; see Projects"]}]},
   {"heading":"Skills","tags":["C++","Python","Go","AWS (ROSA, ECR, ECS)","Docker","Kubernetes/OpenShift","GitLab CI/CD","Slack API Integrations","Jira & Confluence","Management","Problem Solving"]}],
  "projects":[
   {"heading":"At State Farm","items":[
     {"title":"TESA","meta":"Slack application","points":["AI-powered knowledge management connector, independently architected and shipped company-wide"]},
     {"title":"Jake Bot","meta":"Slack application","points":["General-purpose knowledge and information assistant used across the organization"]},
     {"title":"Service outage notifications","meta":"Company-wide system","points":["Real-time alerts that cut mean-time-to-detect by 14 minutes; shaped with cross-functional teams from concept through launch"]}]},
   {"heading":"With iGEM","items":[
     {"title":"Virtual cell biology lab","meta":"Simulation","points":["Simulates chemical reaction kinetics, cell growth and decay, and ion uptake, so the team can run experiments without physical reagents"]},
     {"title":"Cadmium-uptake E. coli","meta":"Team lead","points":["Led a team engineering nonpathogenic E. coli to take up cadmium from water supplies; inspected and coded nucleic acids to create a fusion protein"]}]}],
  "contact":[
   {"heading":"Get in touch","links":[{"label":"Email","value":"misukonisn@gmail.com","href":"mailto:misukonisn@gmail.com"},
       {"label":"LinkedIn","value":"linkedin.com/in/noah-misukonis","href":"https://www.linkedin.com/in/noah-misukonis/"}]},
   {"heading":"Resume","text":["The full one-page resume is available as a PDF."],"links":[{"label":"Download","value":"Noah_Misukonis_2026_Resume.pdf","href":"Noah_Misukonis_2026_Resume.pdf"}]}]}}
json.dump(C,open("folder_assets/popup/folder_content.json","w"),indent=2,ensure_ascii=False)

# ---------------- mockups at 4x with real text ----------------
L=json.load(open("folder_assets/popup/popup_layout.json")); S=4; AX,AY=L["popup"]["canvas_x"],L["popup"]["canvas_y"]
FP="/usr/share/fonts/truetype/dejavu/DejaVuSansMono"
F=lambda n,b=False: ImageFont.truetype(FP+("-Bold" if b else "")+".ttf",n)
INK=(96,84,76); DARK=(84,52,26); RED=(176,58,48); PAPER=(244,240,232)
bg=Image.open("bg_day.png").convert("RGBA"); bg.alpha_composite(Image.open("anim/near_forest_day.png")); bg.alpha_composite(Image.open("cabin_window.png").convert("RGBA"))
bg.alpha_composite(Image.open("anim/mug.png").crop((0,0,32,44)),(205,106)); bg.alpha_composite(Image.open("anim/cig_pack.png"),(94,135))
bg.alpha_composite(Image.open("anim/folder_opened.png"),(160-23,149-38)); bg.alpha_composite(Image.new("RGBA",bg.size,(20,12,6,153)))
def R(name):
    r=L["regions"][name]; return ((AX+r["x"])*S,(AY+r["y"])*S,r["w"]*S,r["h"]*S)
def mock(tab):
    im=bg.copy(); im.alpha_composite(Image.open("folder_assets/popup/popup_folder.png"),(AX,AY))
    t=[t for t in L["tabs"] if t["name"]==tab][0]; im.alpha_composite(Image.open("folder_assets/popup/"+t["active_file"]),(AX+t["x"],AY+t["y"]))
    im=im.resize((320*S,180*S),Image.NEAREST); d=ImageDraw.Draw(im)
    x,y,w,h=R("card"); d.text((x+2,y-34),C["card"]["header"],font=F(13,True),fill=PAPER)
    d.text((x,y+2),C["card"]["name"],font=F(17,True),fill=DARK)
    for i,l in enumerate(C["card"]["lines"]): d.text((x,y+36+i*32),l,font=F(13),fill=INK)
    x,y,w,h=R("sticky"); d.text((x,y),C["sticky"]["title"],font=F(13,True),fill=DARK)
    yy=y+26
    for l in C["sticky"]["links"]:
        for part in textwrap.wrap(l["label"],24): d.text((x,yy),part,font=F(12),fill=(110,80,40)); yy+=17
        yy+=8
    x,y,w,h=R("stamp"); tw=d.textlength(C["stamp"],font=F(15,True)); d.text((x+(w-tw)/2,y+3),C["stamp"],font=F(15,True),fill=RED)
    x,y,w,h=R("page"); yy=y; cols=int(w/7.9)
    def line(s,font,fill,dy=17,indent=0):
        nonlocal yy
        if yy+dy<=y+h: d.text((x+indent,yy),s,font=font,fill=fill)
        yy+=dy
    for sec in C["tabs"][tab]:
        line(sec["heading"].upper(),F(15,True),RED,24)
        for p in sec.get("text",[]):
            for s in textwrap.wrap(p,cols): line(s,F(13),INK)
            yy+=6
        for it in sec.get("items",[]):
            for s in textwrap.wrap(it["title"],cols-2): line(s,F(13,True),DARK)
            line(it["meta"],F(12),(140,126,116))
            for p in it["points"]:
                for k,s in enumerate(textwrap.wrap(p,cols-3)): line(("› " if k==0 else "  ")+s,F(13),INK)
            yy+=8
        for b in sec.get("bullets",[]): line("› "+b,F(13),INK)
        if "tags" in sec:
            for s in textwrap.wrap("  ·  ".join(sec["tags"]),cols): line(s,F(13),INK)
        for l in sec.get("links",[]): line(f'{l["label"]}: {l["value"]}',F(13),(60,90,150))
        yy+=12
    im.convert("RGB").save(f"folder_assets/popup/popup_mockup_{tab}.png")
for t in C["tabs"]: mock(t)
