"""Night version of the cabin window: the same pixels, recoloured to dim, cool wood with faint moonlight on the sill."""
import json
from PIL import Image
DAY=[(38,22,12),(84,52,26),(132,86,42),(168,114,58),(204,150,84)]            # outline, shade, mid, light, highlight
NIGHT=[(14,10,16),(34,26,34),(54,42,50),(74,60,66),(98,84,92)]
MOON=[(16,14,24),(40,36,52),(64,58,78),(88,82,104),(116,112,136)]            # surfaces facing the open window
im=Image.open("cabin_window.png").convert("RGBA"); px=im.load(); other=0
for y in range(im.height):
    for x in range(im.width):
        r,g,b,a=px[x,y]
        if a==0: continue
        recess = 34<=x<=285 and 22<=y<=150                                   # sill top and the inner sides of the opening
        if (r,g,b) in DAY: px[x,y]=(MOON if recess else NIGHT)[DAY.index((r,g,b))]+(a,)
        else: other+=1; px[x,y]=(int(r*0.42),int(g*0.46),int(b*0.62),a)
print("pixels outside the wood palette:",other)
im.save("cabin_window_night.png"); im.save("anim/cabin_window_night.png")
m=json.load(open("anim/manifest.json"))
m["window"]={"files":["cabin_window.png","cabin_window_night.png"],"note":"Use the night file with bg_night and cross-fade between the two like every other time-of-day asset. Morning, day and afternoon share cabin_window.png."}
json.dump(m,open("anim/manifest.json","w"),indent=2)
def scene(t,win,tag):
    c=Image.open(f"bg_{t}.png").convert("RGBA"); c.alpha_composite(Image.open(f"anim/near_forest_{t}.png")); c.alpha_composite(Image.open(win).convert("RGBA"))
    c.alpha_composite(Image.open(f"anim/mug{tag}.png").crop((0,0,32,44)),(205,106)); c.alpha_composite(Image.open(f"anim/cig_pack{tag}.png"),(94,135)); c.alpha_composite(Image.open(f"anim/folder{tag}.png"),(137,129))
    return c
out=Image.new("RGBA",(1280*2,720))
out.paste(scene("night","cabin_window.png","_night").resize((1280,720),Image.NEAREST),(0,0)); out.paste(scene("night","cabin_window_night.png","_night").resize((1280,720),Image.NEAREST),(1280,0))
out.save("window_night_preview.png")
