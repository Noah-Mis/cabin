import math, random, json, os, shutil
from PIL import Image
os.chdir('/tmp/cabin')
W, H = 320, 180
TIMES = ['morning', 'day', 'afternoon', 'night']
OUT = 'anim'
os.makedirs(OUT + '/previews', exist_ok=True)

# ---- rebuild the scene from bg.py, recording the near-forest trees ----
src = open('bg.py').read()
iA = src.index('# near hills'); iB = src.index('P={')
ns = {}
exec(src[:iA], ns)
g = ns['g']
g_before = [r[:] for r in g]
trees = []
orig_pine = ns['pine']
def rec(xc, base, h, L, D, tier=3, trunk=None):
    trees.append((xc, base, h, tier, trunk)); orig_pine(xc, base, h, L, D, tier, trunk)
ns['pine'] = rec
exec(src[iA:iB], ns)
ns['pine'] = orig_pine
exec(src[iB:], ns)
P, stars, hf, hn, colph, LAKE = ns['P'], ns['stars'], ns['hf'], ns['hn'], ns['colph'], ns['LAKE']
NEARSET = ('near', 'nt_l', 'nt_d', 'trunk')

# ---- palettes ----
TINT = {'day': (1, 1, 1), 'morning': (1.0, 0.84, 0.88), 'afternoon': (1.04, 0.95, 0.80), 'night': (0.34, 0.40, 0.62)}
NEW = dict(bird_d=(40, 44, 60), bird_m=(76, 84, 108), bird_l=(204, 210, 224), beak=(232, 160, 60),
           sq_d=(44, 30, 24), sq_m=(88, 60, 42), sq_l=(128, 92, 62), sq_f=(156, 118, 90), sq_e=(20, 12, 10))
CLOUD = {'day': [(255, 255, 255), (232, 240, 250), (196, 212, 236)],
         'morning': [(255, 236, 220), (246, 200, 190), (206, 160, 184)],
         'afternoon': [(255, 248, 226), (246, 226, 186), (214, 190, 170)],
         'night': [(70, 84, 128), (52, 64, 104), (38, 48, 84)]}
RAIN = {'day': (200, 220, 245), 'morning': (240, 214, 220), 'afternoon': (236, 226, 200), 'night': (120, 140, 190)}
FP = {}
for t in TIMES:
    p = {k: v for k, v in P[t].items() if k != 'sky'}
    for i, c in enumerate(P[t]['sky']): p['sky%d' % i] = c
    for k, v in NEW.items(): p[k] = tuple(min(255, int(c * m)) for c, m in zip(v, TINT[t]))
    p['cl_l'], p['cl_m'], p['cl_d'] = CLOUD[t]
    FP[t] = p
INDOOR = dict(wax_l=(240, 228, 200), wax_m=(212, 194, 160), wax_d=(168, 146, 120), wick=(50, 36, 30),
              mug_l=(214, 96, 78), mug_m=(172, 60, 56), mug_d=(118, 40, 46), mug_r=(236, 220, 200),
              drink=(70, 40, 28), drink_h=(112, 72, 46))
FP['base'] = dict(INDOOR)
FP['in_night'] = {k: tuple(int(c * m) for c, m in zip(v, (0.55, 0.52, 0.66))) for k, v in INDOOR.items()}
for k in ('wax_l', 'wax_m', 'wax_d'):   # candle stays lit by its own flame
    FP['in_night'][k] = tuple(int(c * m) for c, m in zip(INDOOR[k], (0.80, 0.70, 0.58)))

def img_from(grid, pal):
    h = len(grid); w = len(grid[0]); im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); px = im.load()
    for y in range(h):
        for x in range(w):
            k = grid[y][x]
            if k is None: continue
            px[x, y] = (FP[pal][k] + (255,)) if isinstance(k, str) else k
    return im
def strip(frames):
    w, h = frames[0].size; s = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames): s.paste(f, (i * w, 0))
    return s
def blank(w, h): return [[None] * w for _ in range(h)]
def ascii_grid(rows, w, h, mp, y0=0, grid=None):
    grid = grid or blank(w, h)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row[:w]):
            if ch in mp: grid[y0 + j][i] = mp[ch]
    return grid
M = {'canvas': [W, H], 'window_opening': {'x': 40, 'y': 24, 'w': 240, 'h': 107},
     'sill_band': {'x0': 42, 'x1': 277, 'y0': 132, 'y1': 149},
     'draw_order': ['bg_<time>', 'stars / clouds / far birds (clipped by sky_mask)', 'waterfall', 'sasquatch',
                    'near_forest_<time>', 'treetops', 'bird', 'rain or snow', 'wind', 'cabin_window', 'mug'],
     'animations': {}}
def entry(name, files, fw, fh, n, ms, loop, anchor, place, note):
    M['animations'][name] = dict(files=files, frame_w=fw, frame_h=fh, frames=n, ms_per_frame=ms, loop=loop,
                                 anchor=anchor, placement=place, note=note)
SHEETS = {}
def save_times(name, build, pals=TIMES):
    for t in pals:
        s = strip([img_from(fr, t) for fr in build]); s.save(f'{OUT}/{name}_{t}.png'); SHEETS[(name, t)] = s
    return [f'{name}_{t}.png' for t in pals]

# ---- 1. masks ----
sky = Image.new('RGBA', (W, H), (0, 0, 0, 0))
for y in range(H):
    for x in range(W):
        if g[y][x].startswith('sky'): sky.putpixel((x, y), (255, 255, 255, 255))
sky.save(f'{OUT}/sky_mask.png')
near_grid0 = [[g[y][x] if g[y][x] in NEARSET else None for x in range(W)] for y in range(H)]
NEAR = {}
for t in TIMES:
    NEAR[t] = img_from(near_grid0, t); NEAR[t].save(f'{OUT}/near_forest_{t}.png')
M['masks'] = {'sky_mask.png': 'opaque where the background is sky; use as a clip for clouds, stars, sun, far birds',
              'near_forest_<time>.png': 'the front forest only; draw it after the sasquatch so he comes out from behind it'}

# ---- 2a. waterfall ----
X0, Y0, PW, PH = 148, 96, 25, 44
def wf_frame(f):
    grid = blank(PW, PH)
    def put(x, y, k):
        if X0 <= x < X0 + PW and Y0 <= y < Y0 + PH and g[y][x] not in NEARSET: grid[y - Y0][x - X0] = k
    for x in range(157, 164):
        for y in range(hf[x] - 1, LAKE):
            c = 'wf2' if (y - f + colph[x]) % 6 < 2 else 'wf1'
            if x in (157, 163) and (y - f + colph[x]) % 3 != 0: c = 'wf2'
            put(x, y, c)
    for y in range(LAKE, 138):
        for x in range(155, 166):
            if g[y][x] in ('water', 'water_hi', 'water_d'):
                put(x, y, 'water_hi' if (y % 2 == 0 and (x + y + f) % 3 != 0) else ('water' if y % 2 == 0 else g[y][x]))
    s = 1 + 0.22 * (1 - math.cos(2 * math.pi * f / 6)) / 2
    for dy in range(-7, 4):
        for dx in range(-13, 14):
            r = (dx / (10 * s)) ** 2 + ((dy + 1) / (4 * s)) ** 2
            if r <= 1 and (r < 0.35 or (dx + dy) % 2 == 0): put(160 + dx, LAKE + dy, 'mist')
    return grid
files = save_times('waterfall', [wf_frame(f) for f in range(6)])
entry('waterfall', files, PW, PH, 6, 100, True, [0, 0], {'x': X0, 'y': Y0},
      'Patch drawn over the background at a fixed spot. Water streaks scroll down, mist breathes, pool glints shimmer.')

# ---- 2b. stars (night only) ----
SB, SD = (230, 236, 255, 255), (120, 140, 196, 255)
rs = random.Random(5)
vis = [(x, y, b) for x, y, b in stars if g[y][x].startswith('sky')]
PB = ['BBBB', 'BBBB', 'BBBB', 'BdBB', 'BBdB', 'SBBd', 'BdSB', 'dBBS']
PD = ['dddd', 'dddd', 'dddd', 'dodd', 'ddBd', 'oddd', 'dBdo']
sched = [(x, y, b, rs.choice(PB if b else PD)) for x, y, b in vis]
sframes = []
for f in range(4):
    grid = blank(W, H)
    for x, y, b, pat in sched:
        c = pat[f]; base = 'B' if b else 'd'
        if c == base: continue
        if c == 'o': grid[y][x] = g[y][x]
        elif c == 'd': grid[y][x] = SD
        else:
            grid[y][x] = SB
            if c == 'S':
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if 0 <= x + dx < W and 0 <= y + dy < H and g[y + dy][x + dx].startswith('sky'): grid[y + dy][x + dx] = SD
    sframes.append(img_from(grid, 'night'))
STARS = strip(sframes); STARS.save(f'{OUT}/stars_night.png')
entry('stars', ['stars_night.png'], W, H, 4, 450, True, [0, 0], {'x': 0, 'y': 0},
      'Night only. Full-canvas overlay holding just the pixels that change on the stars already painted into bg_night.')

# ---- 2c. clouds ----
def cloud(w, h, seed):
    r = random.Random(seed); base = h - 1; circ = []; x = h * 0.45
    while x < w - h * 0.4:
        rad = (h / 1.65) * (0.55 + 0.45 * math.sin(math.pi * x / w)) * r.uniform(0.8, 1.0)
        rad = min(rad, x, w - 1 - x)
        circ.append((x, base - rad * 0.6, rad)); x += max(2, rad * r.uniform(0.7, 1.1))
    grid = blank(w, h)
    for xx in range(w):
        top = None
        for yy in range(h):
            if any((xx - cx) ** 2 + (yy - cy) ** 2 <= cr * cr for cx, cy, cr in circ):
                if top is None: top = yy
                d = yy - top
                grid[yy][xx] = 'cl_l' if d < max(1, h // 6) else ('cl_d' if yy >= base - max(0, h // 8) else 'cl_m')
    ks = [xx for xx in range(w) if grid[base][xx]]
    for xx in ks[:2] + ks[-2:]: grid[base][xx] = None
    return grid
CL = {}
for nm, (w, h, sd) in dict(a=(56, 18, 3), b=(40, 14, 8), c=(28, 10, 2), d=(20, 8, 6)).items():
    gr = cloud(w, h, sd)
    for t in TIMES:
        im = img_from(gr, t); im.save(f'{OUT}/cloud_{nm}_{t}.png'); CL[(nm, t)] = im
    entry('cloud_' + nm, [f'cloud_{nm}_{t}.png' for t in TIMES], w, h, 1, 0, False, [0, 0],
          {'region': 'sky, y 26-70', 'clip': 'sky_mask.png'}, 'Static shape. Slide it sideways slowly in code (about 2-6 px per second).')

# ---- 2d. rain and snow ----
r = random.Random(21)
drops = [(r.randrange(32), r.randrange(64)) for _ in range(13)]
for t in TIMES:
    fr = []
    for f in range(4):
        grid = blank(64, 64)
        for x0, y0 in drops:
            hx, hy = (x0 - 8 * f) % 32, (y0 + 16 * f) % 64
            for i in range(6):
                yy = (hy - i) % 64; xx = (hx + (i + 1) // 2) % 32
                c = RAIN[t] + (190 if i < 3 else 110,)
                grid[yy][xx] = c; grid[yy][xx + 32] = c
        fr.append(img_from(grid, t))
    s = strip(fr); s.save(f'{OUT}/rain_{t}.png'); SHEETS[('rain', t)] = s
entry('rain', [f'rain_{t}.png' for t in TIMES], 64, 64, 4, 70, True, [0, 0], {'tile': 'repeat over the whole canvas'},
      'Seamless tile in x and y. Partly transparent streaks falling down and to the left.')
r = random.Random(33)
flakes = [(r.randrange(64), r.randrange(64), r.choice([8, 8, 16]), r.uniform(0, 6.28)) for _ in range(30)]
sn = []
for f in range(8):
    grid = blank(64, 64)
    for x0, y0, v, ph in flakes:
        x = (x0 + round(1.6 * math.sin(2 * math.pi * f / 8 + ph))) % 64; y = (y0 + v * f) % 64
        grid[y][x] = 'snow_l'
        if v == 16: grid[y][(x + 1) % 64] = 'snow_l'; grid[(y + 1) % 64][x] = 'snow_s'
    sn.append(grid)
files = save_times('snow', sn)
entry('snow', files, 64, 64, 8, 200, True, [0, 0], {'tile': 'repeat over the whole canvas'},
      'Seamless tile in x and y. Small flakes fall slowly, larger ones twice as fast, all wobbling sideways.')

# ---- 2e. swaying treetops ----
def near_scene(f):
    gg = [row[:] for row in g_before]
    for x in range(W):
        for y in range(hn[x], H): gg[y][x] = 'near'
    for xc, base, h, tier, trunk in trees:
        sway = 1 if (f > 0 and math.sin(2 * math.pi * f / 4 - xc * 0.09) > 0.2) else 0
        top = base - h
        for rr in range(h):
            hw = (rr % tier) + rr // tier; y = top + rr
            if not 0 <= y < H: continue
            sh = sway if rr < 3 else 0
            for dx in range(-hw, hw + 1):
                x = xc + dx + sh
                if 0 <= x < W and gg[y][x] not in ('wf1', 'wf2'): gg[y][x] = 'nt_l' if (dx < 0 or hw == 0) else 'nt_d'
        if trunk and 0 <= base < H and 0 <= xc < W: gg[base][xc] = trunk
    return gg
s0 = near_scene(0)
assert s0 == g, 'near forest rebuild does not match the background'
tf = []
for f in range(4):
    sc = near_scene(f)
    tf.append([[sc[y][x] if sc[y][x] != g[y][x] else None for x in range(W)] for y in range(H)])
files = save_times('treetops', tf)
entry('treetops', files, W, H, 4, 250, True, [0, 0], {'x': 0, 'y': 0},
      'Full-canvas overlay of changed pixels only; frame 0 is empty (trees at rest). Tips lean 1 px right in a wave. Draw after near_forest.')

# ---- 1a. bird ----
BM = {'D': 'bird_d', 'M': 'bird_m', 'L': 'bird_l', 'B': 'beak'}
body = [".....MMMMMDD....", "..DDMMMMMMDDB...", "....LLLLLL......"]
up = ["....DD..........", "....DDD.........", ".....DDD........", "......DDD......."]
down = ["....LLLDDD......", ".....DDD........", "....DDD.........", "....DD.........."]
def bird(kind):
    gr = ascii_grid(body, 16, 12, BM, 5)
    if kind == 'u': ascii_grid(up, 16, 12, BM, 1, gr)
    if kind == 'm': ascii_grid(["..DDDDDD........"], 16, 12, BM, 4, gr)
    if kind == 'd': ascii_grid(down, 16, 12, BM, 7, gr)
    return gr
files = save_times('bird_flap', [bird(k) for k in 'umdm'])
entry('bird_flap', files, 16, 12, 4, 100, True, [8, 6], {'region': 'anywhere in the opening; move 4-6 px per frame'},
      'Faces right; mirror for leftward flight. Wings up, level, down, level.')
sa = ["........", "D.....D.", ".D...D..", "..DDD..."]; sb = ["........", "........", "..DDD...", "DD...DD."]
files = save_times('bird_far', [ascii_grid(sa, 8, 6, BM), ascii_grid(sb, 8, 6, BM)])
entry('bird_far', files, 8, 6, 2, 180, True, [3, 3], {'region': 'sky', 'clip': 'sky_mask.png'}, 'Tiny distant bird silhouette.')

# ---- 1b. sasquatch ----
LEG = [(35, 10), (10, -15), (-10, -30), (-35, -45), (-25, -90), (10, -80), (45, -40), (50, 0)]
def vec(a, l):
    rr = math.radians(a); return l * math.sin(rr), l * math.cos(rr)
def sasquatch(f, S=0.6, FW=16, FH=14):
    grid = blank(FW, FH)
    hip = (FW * 0.44, FH * 0.55); sh = (hip[0] + 2.5 * S, hip[1] - 7 * S)
    def leg(ff):
        th, sn_ = LEG[ff % 8]; a = vec(th, 4.2 * S); k = (hip[0] + a[0], hip[1] + a[1]); b = vec(sn_, 4.2 * S)
        return k, (k[0] + b[0], k[1] + b[1]), sn_
    def arm(ff):
        upa = -40 * math.cos(2 * math.pi * ff / 8); a = vec(upa, 4 * S); e = (sh[0] + a[0], sh[1] + S + a[1])
        b = vec(upa + 30, 4.5 * S); return e, (e[0] + b[0], e[1] + b[1])
    nl, fl = leg(f), leg(f + 4); na, fa = arm(f), arm(f + 4)
    dy = (FH - 2.5) - max(nl[1][1], fl[1][1])
    def stamp(x, y, k):
        ix, iy = int(math.floor(x)), int(math.floor(y + dy))
        if 0 <= ix < FW and 0 <= iy < FH: grid[iy][ix] = k
    def line(p, q, k):
        for i in range(13):
            u = i / 12; stamp(p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u, k)
    def disk(cx, cy, rad, k):
        cy += dy
        for y in range(FH):
            for x in range(FW):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= rad * rad: grid[y][x] = k
    def limb_leg(L, k):
        kn, an, sn_ = L; line(hip, kn, k); line(kn, an, k); v = vec(sn_ + 90, 1.0); stamp(an[0] + v[0], an[1] + v[1], k)
    line((sh[0], sh[1] + S), fa[0], 'sq_d'); line(fa[0], fa[1], 'sq_d'); limb_leg(fl, 'sq_d')
    for i in range(9):
        u = i / 8; disk(hip[0] + (sh[0] - hip[0]) * u, hip[1] + (sh[1] - hip[1]) * u, (2.5 + 0.6 * u) * S, 'sq_m')
    hx, hy = sh[0] + 1.2 * S, sh[1] - 2.6 * S
    disk(hx, hy, 2.4 * S, 'sq_m')
    lit = [(x, y) for y in range(FH) for x in range(FW) if grid[y][x] == 'sq_m' and (y == 0 or grid[y - 1][x] is None)]
    for x, y in lit: grid[y][x] = 'sq_l'
    fx, fy = int(hx + 0.8), int(hy + dy)
    if 0 <= fx < FW and grid[fy][fx]: grid[fy][fx] = 'sq_f'
    limb_leg(nl, 'sq_m')
    line((sh[0], sh[1] + S), na[0], 'sq_l'); line(na[0], na[1], 'sq_l')
    return grid
files = save_times('sasquatch_run', [sasquatch(f) for f in range(8)])
entry('sasquatch_run', files, 16, 14, 8, 90, True, [7, 12],
      {'path': 'optional; feet on y=123, only visible in the gap around x 135-185', 'behind': 'near_forest_<time>.png'},
      'Small run cycle, faces right. Kept as an extra; the peek below is the main sasquatch event.')
# peek: head and shoulders rise between two treetops, look around, sink back
for t in TIMES: FP[t]['sq_e'] = (214, 200, 120) if t == 'night' else FP[t]['sq_e']
SQM = {'L': 'sq_l', 'M': 'sq_m', 'D': 'sq_d', 'F': 'sq_f', 'E': 'sq_e'}
def fig(look):
    eyes = {'c': "..MEFED...", 'l': "..EFEFD...", 'r': "..MFEFE...", 'b': "..MFFFD..."}[look]
    return ["...LMM....", "..LMMMD...", eyes, "..MFFFD...", ".LMMMMMD..", "LMMMMMMMD."] + ["LMMMMMMMD."] * 6
PEEK = [(2, 'c'), (4, 'c'), (6, 'c'), (7, 'c'), (7, 'l'), (7, 'l'), (7, 'c'), (7, 'r'), (7, 'r'), (7, 'b'), (7, 'c'), (5, 'c'), (3, 'c'), (1, 'c')]
def peek(shown, look):
    gr = blank(12, 16); rows = fig(look)
    for j in range(shown + 2):
        for i, ch in enumerate(rows[j]):
            if ch in SQM: gr[16 - (shown + 2) + j][1 + i] = SQM[ch]
    return gr
files = save_times('sasquatch_peek', [peek(*p) for p in PEEK])
skyline = [next((y for y in range(H) if g[y][x] in NEARSET), H) for x in range(W)]
spots = []
for x in range(48, 272):
    if 138 <= x <= 182: continue
    yv = skyline[x]
    if yv > 126 or yv < max(skyline[x - 1], skyline[x + 1]): continue
    if yv - min(skyline[x - 4:x + 5]) < 5: continue
    if g[yv - 4][x] in NEARSET or g[yv - 4][x].startswith('sky'): continue
    if spots and x - spots[-1][0] < 22: continue
    spots.append((x, yv))
SPOTS = [{'x': x, 'y': y + 2} for x, y in spots]
entry('sasquatch_peek', files, 12, 16, len(PEEK), 160, False, [5, 15],
      {'spots': SPOTS, 'behind': 'near_forest_<time>.png'},
      'Plays once. Put the anchor (bottom-centre of the frame) on one of the spots, each a gap between two front treetops, '
      'and draw before the near forest. He rises, looks left and right, blinks, and sinks back. Eyes glow at night.')

# ---- 1d. mug (the only sill item) ----
MW, MH, MCX = 32, 44, 13
def mug(f):
    gr = blank(MW, MH)
    for y in range(MH):
        for x in range(MW):
            px_, py_ = x + 0.5, y + 0.5
            w = 9 - 0.06 * (y - 22); u = (px_ - MCX) / w
            if 22 <= y and abs(u) <= 1 and py_ <= 37.3 + 2.4 * math.sqrt(max(0, 1 - u * u)):
                gr[y][x] = 'mug_l' if u < -0.62 else ('mug_d' if u > 0.42 else 'mug_m')
                if py_ > 36.6 + 2.4 * math.sqrt(max(0, 1 - u * u)): gr[y][x] = 'mug_d'
            hx_, hy_ = px_ - (MCX + 10.5), py_ - 29.5
            if px_ > MCX + w and (hx_ / 5.2) ** 2 + (hy_ / 6.2) ** 2 <= 1 and (hx_ / 3.0) ** 2 + (hy_ / 4.0) ** 2 > 1:
                gr[y][x] = 'mug_d' if (hy_ > 2 or hx_ > 3.4) else ('mug_l' if hy_ < -4 else 'mug_m')
            e = ((px_ - MCX) / 9) ** 2 + ((py_ - 22) / 3.2) ** 2
            if e <= 1:
                gr[y][x] = 'mug_r'
                ei = ((px_ - MCX) / 7.6) ** 2 + ((py_ - 22.2) / 2.3) ** 2
                if ei <= 1: gr[y][x] = 'drink_h' if (px_ < MCX - 2 and py_ < 21.5 and ei > 0.45) else 'drink'
    for cx, off in ((9, 0), (14, 5), (18, 9)):
        for y in range(2, 20):
            hgt = 19 - y; uu = (hgt - 2 * f + off) % 12
            if uu < 6:
                x = cx + round(1.7 * math.sin((hgt - 2 * f) * 2 * math.pi / 12 + off))
                gr[y][x] = (255, 255, 255, max(45, 215 - hgt * 10))
    return gr
mf = [mug(f) for f in range(6)]
for pal, nm in (('base', 'mug'), ('in_night', 'mug_night')):
    s = strip([img_from(x, pal) for x in mf]); s.save(f'{OUT}/{nm}.png'); SHEETS[nm] = s
MUG_AT = (218, 146)
entry('mug', ['mug.png', 'mug_night.png'], MW, MH, 6, 150, True, [MCX, 40], {'x': MUG_AT[0], 'y': MUG_AT[1], 'region': 'sill band'},
      'Anchor is the bottom-centre of the base. Sits a quarter of the way in from the right edge of the sill. Only the steam moves.')

# ---- 4. wind ----
WIND = {}
for nm, n in (('wind_gust', 14), ('wind_streak', 10)):
    im = Image.open(nm + '.png').convert('RGBA'); im.save(f'{OUT}/{nm}.png'); WIND[(nm, 'day')] = WIND[(nm, 'afternoon')] = im
    fl = [nm + '.png']
    for t in ('morning', 'night'):
        c = im.copy(); px = c.load(); col = P[t]['snow_l']
        for y in range(c.height):
            for x in range(c.width):
                if px[x, y][3]: px[x, y] = col + (px[x, y][3],)
        c.save(f'{OUT}/{nm}_{t}.png'); WIND[(nm, t)] = c; fl.append(f'{nm}_{t}.png')
    entry(nm, fl, 64, 24, n, 80, False, [0, 0], {'region': 'sky and treeline; slide right 4-5 px per frame while playing'},
          'Plays once. Plain file is white for day and afternoon; tinted versions for morning and night.')
json.dump(M, open(f'{OUT}/manifest.json', 'w'), indent=2)

# ---- previews ----
BG = {t: Image.open(f'bg_{t}.png').convert('RGBA') for t in TIMES}
WIN = Image.open('cabin_window.png').convert('RGBA')
def fr(sheet, fw, i):
    return sheet.crop((i * fw, 0, (i + 1) * fw, sheet.height))
def compose(t, k, weather=None, wind=False):
    c = BG[t].copy()
    sl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if t == 'night': sl.alpha_composite(fr(STARS, W, (k // 4) % 4))
    for nm, x, y, sp in (('a', 52, 30, 0.5), ('c', 196, 40, 0.3), ('b', 128, 60, 0.4), ('d', 236, 70, 0.25)):
        sl.alpha_composite(CL[(nm, t)], (int(x + k * sp), y))
    sl.alpha_composite(fr(SHEETS[('bird_far', t)], 8, (k // 2) % 2), (250 - int(k * 1.5), 36))
    c.alpha_composite(Image.composite(sl, Image.new('RGBA', (W, H), (0, 0, 0, 0)), sky.split()[3]))
    c.alpha_composite(fr(SHEETS[('waterfall', t)], PW, k % 6), (X0, Y0))
    for sp, k0 in ((SPOTS[len(SPOTS) // 3], 2), (SPOTS[-2], 24)):
        if k0 <= k < k0 + 2 * len(PEEK) - 6: c.alpha_composite(fr(SHEETS[('sasquatch_peek', t)], 12, min(len(PEEK) - 1, (k - k0) * 14 // 22)), (sp['x'] - 5, sp['y'] - 15))
    c.alpha_composite(NEAR[t]); c.alpha_composite(fr(SHEETS[('treetops', t)], W, (k // 3) % 4))
    bx = 40 + 5 * k
    c.alpha_composite(fr(SHEETS[('bird_flap', t)], 16, k % 4), (bx - 8, 52 + round(4 * math.sin(k * 0.3)) - 6))
    if weather:
        n, div = (4, 1) if weather == 'rain' else (8, 2)
        tile = fr(SHEETS[(weather, t)], 64, (k // div) % n)
        for ty in range(0, H, 64):
            for tx in range(0, W, 64): c.alpha_composite(tile, (tx, ty))
    if wind:
        if k < 14: c.alpha_composite(fr(WIND[('wind_gust', t)], 64, k), (70 + 5 * k, 76))
        if 20 <= k < 30: c.alpha_composite(fr(WIND[('wind_streak', t)], 64, k - 20), (130 + 4 * (k - 20), 96))
        if 30 <= k < 44: c.alpha_composite(fr(WIND[('wind_gust', t)], 64, k - 30), (50 + 5 * (k - 30), 100))
    c.alpha_composite(WIN)
    ni = t == 'night'
    c.alpha_composite(fr(SHEETS['mug_night' if ni else 'mug'], MW, (k // 2) % 6), (MUG_AT[0] - MCX, MUG_AT[1] - 40))
    return c
def gif(name, t, **kw):
    fs = [compose(t, k, **kw).resize((W * 2, H * 2), Image.NEAREST).convert('RGB').quantize(255) for k in range(48)]
    fs[0].save(f'{OUT}/previews/{name}.gif', save_all=True, append_images=fs[1:], duration=100, loop=0)
for t in TIMES: gif('preview_' + t, t, wind=(t in ('day', 'afternoon')))
gif('preview_rain', 'afternoon', weather='rain'); gif('preview_snow', 'night', weather='snow')
# stills for checking
st = Image.new('RGBA', (W * 2, H * 2))
for i, (t, kw) in enumerate((('day', dict(wind=True)), ('morning', {}), ('afternoon', dict(weather='rain')), ('night', dict(weather='snow')))):
    st.paste(compose(t, 11 + i * 9, **kw), ((i % 2) * W, (i // 2) * H))
st.resize((W * 6, H * 6), Image.NEAREST).save(f'{OUT}/previews/stills.png')
# contact sheet
S = 8
cs = Image.new('RGBA', (8 * 24 * S, 122 * S), (104, 164, 226, 255))
def lay(sheet, fw, n, y, bgc=None, step=24):
    for i in range(n):
        f_ = fr(sheet, fw, i).resize((fw * S, sheet.height * S), Image.NEAREST)
        if bgc: cs.paste(bgc, (i * step * S, y * S, i * step * S + fw * S, y * S + sheet.height * S))
        cs.alpha_composite(f_, (i * step * S, y * S))
lay(SHEETS[('bird_flap', 'day')], 16, 4, 0)
for i in range(2): cs.alpha_composite(fr(SHEETS[('bird_far', 'day')], 8, i).resize((64, 48), Image.NEAREST), ((4 * 24 + i * 12) * S, 2 * S))
lay(SHEETS[('sasquatch_run', 'day')], 16, 8, 13, (64, 124, 84, 255))
lay(SHEETS[('sasquatch_peek', 'day')], 12, 14, 28, (64, 124, 84, 255), 13)
lay(SHEETS['mug'], MW, 6, 46, (168, 114, 58, 255), 32)
x = 0
for nm in 'abcd':
    im = CL[(nm, 'day')]; cs.alpha_composite(im.resize((im.width * 6, im.height * 6), Image.NEAREST), (x, 97 * S)); x += im.width * 6 + 24
cs.save(f'{OUT}/previews/contact_sprites.png')
for f in ('anim.py', 'bg.py', 'make.py', 'wind.py'):
    os.makedirs(OUT + '/scripts', exist_ok=True); shutil.copy(f, OUT + '/scripts/' + f)
print('ok', len(os.listdir(OUT)), 'files; trees', len(trees), 'stars', len(vis))
