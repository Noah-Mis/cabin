"""First-person animations with no hands: the pack arrives, a cigarette leaves it, and the smoking sequence.
Everything is drawn with simple capsule shapes, then shaded, so each piece can be regenerated or adjusted."""
import math, json, random, os
from PIL import Image
os.chdir('/tmp/cabin')
W, H = 320, 180
OUT = 'anim'
GX = -52
MS = 120                                   # every animation here plays at 120 ms per frame
NIGHT = (0.55, 0.52, 0.66)
SK = dict(l=(236, 190, 156), m=(212, 160, 126), d=(170, 120, 96))
MAT = {'paper': (244, 240, 232), 'paper_d': (206, 200, 198), 'filter': (214, 156, 96), 'filter_d': (176, 122, 72), 'ash': (150, 148, 150),
       'emb0': (140, 34, 24), 'emb1': (222, 74, 30), 'emb2': (252, 150, 48), 'emb3': (255, 226, 130), 'ash_d': (96, 92, 98), 'lt': (186, 192, 202), 'lt_d': (120, 126, 140), 'lt_top': (90, 94, 104)}
EMISSIVE = ('emb0', 'emb1', 'emb2', 'emb3')
EMB_PHASE = 0                              # 0-7; set per frame so the ember pattern crawls and loops every 8 frames

def new(): return [[None] * W for _ in range(H)]
def capsule(G, p, q, r, m):
    dx, dy = q[0] - p[0], q[1] - p[1]; L2 = dx * dx + dy * dy or 1e-9
    for y in range(max(0, int(min(p[1], q[1]) - r - 1)), min(H, int(max(p[1], q[1]) + r + 2))):
        for x in range(max(0, int(min(p[0], q[0]) - r - 1)), min(W, int(max(p[0], q[0]) + r + 2))):
            cx, cy = x + .5, y + .5; u = max(0, min(1, ((cx - p[0]) * dx + (cy - p[1]) * dy) / L2))
            if (cx - p[0] - u * dx) ** 2 + (cy - p[1] - u * dy) ** 2 <= r * r: G[y][x] = m
def cig(G, p, q, r, lit, hot, scale=1.0, filt=0):
    """A cigarette from p (held end) to q (tip). When lit the tip is ember, with a short band of ash behind it."""
    dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy) or 1e-9
    for y in range(max(0, int(min(p[1], q[1]) - r - 1)), min(H, int(max(p[1], q[1]) + r + 2))):
        for x in range(max(0, int(min(p[0], q[0]) - r - 1)), min(W, int(max(p[0], q[0]) + r + 2))):
            cx, cy = x + .5, y + .5; u = max(0, min(1, ((cx - p[0]) * dx + (cy - p[1]) * dy) / (L * L)))
            if (cx - p[0] - u * dx) ** 2 + (cy - p[1] - u * dy) ** 2 > r * r: continue
            d = (1 - u) * L; side = (cx - p[0]) * dy - (cy - p[1]) * dx
            m = 'paper_d' if side < -0.4 * scale else 'paper'
            if filt and u * L < filt * scale: m = 'filter_d' if side < -0.4 * scale else 'filter'
            if lit and d < 5.4 * scale:
                # Heat varies pixel by pixel and drifts with EMB_PHASE: hot spots crawl across the coal instead of the whole tip blinking.
                ph = 2 * math.pi * EMB_PHASE / 8
                heat = (0.85 if hot else 0.56) + 0.24 * math.sin(x * 2.1 + y * 1.3 + ph) + 0.20 * math.sin(x * 0.9 - y * 2.7 + 2 * ph + 1.3)
                heat += 0.12 * (1 - min(1, abs(side) / (r * L)))             # the core runs hotter than the rim
                if d < 2.8 * scale:
                    m = 'emb3' if heat > 0.92 else ('emb2' if heat > 0.68 else ('emb1' if heat > 0.44 else 'emb0'))
                    if not hot and heat < 0.30: m = 'ash_d'                   # a fleck of ash crusting over
                else:
                    m = 'ash_d' if (x * 7 + y * 13) % 5 < 2 else 'ash'
                    if d < 3.9 * scale and heat > 0.80: m = 'emb0'            # smouldering edge showing through the ash
            G[y][x] = m
def colorize(G, tint=None):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); px = im.load()
    for y in range(H):
        for x in range(W):
            m = G[y][x]
            if m is None: continue
            def same(xx, yy): return not (0 <= xx < W and 0 <= yy < H) or G[yy][xx] == m
            if isinstance(m, tuple) and m[0] == 'skin':
                c = SK['d'] if not (same(x + 1, y) and same(x, y + 1)) else (SK['l'] if not (same(x - 1, y) and same(x, y - 1)) else SK['m'])
            elif isinstance(m, tuple) and m[0] == 'sleeve':       # red flannel check
                c = (112, 30, 34) if (x // 4 + y // 4) % 2 else (158, 46, 46)
                if not (same(x + 1, y) and same(x, y + 1)): c = (84, 22, 28)
            else: c = MAT[m]
            if tint and m not in EMISSIVE: c = tuple(int(v * t) for v, t in zip(c, tint))
            px[x, y] = c + (255,)
    return im
def dot(im, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        o = Image.new('RGBA', (1, 1), c); im.alpha_composite(o, (int(x), int(y)))
def strip(frames, box=None):
    fr = [f.crop(box) for f in frames] if box else frames
    w, h = fr[0].size; s = Image.new('RGBA', (w * len(fr), h), (0, 0, 0, 0))
    for i, f in enumerate(fr): s.paste(f, (i * w, 0))
    return s

# ------------------------------------------------------------------ the smoking hand (lower right, close to the viewer)
def smoking_cig(t=0.0, off=(0, 0), level=0, lit=False, hot=False, tint=None, wisp=None, lighter=None, phase=0):
    """t = 0 is the resting pose; t -> 1 brings the hand toward the viewer (bigger, lower, toward the mouth).
    level 0-4 shortens the cigarette as it burns down."""
    global EMB_PHASE
    EMB_PHASE = phase
    G = new(); S = 1 + 1.2 * t
    hc = (236 + GX + 44 * t + off[0], 162 + 95 * t + off[1])     # GX keeps the hand clear of the mug
    T = lambda p: (hc[0] + (p[0] - 236) * S, hc[1] + (p[1] - 162) * S)
    base, full = (221, 145), (206, 128); k = 1 - 0.16 * level
    tip = T((base[0] + (full[0] - base[0]) * k, base[1] + (full[1] - base[1]) * k))
    cig(G, T((227, 152)), tip, 1.5 * S, lit, hot, S, filt=7)                 # no hand: the cigarette floats on its own
    if lighter is not None:                                                  # second hand with a lighter, from the lower left
        dy, flame = lighter; o = lambda p: (p[0] + GX, p[1] + dy)
        for y in range(133, 150):
            for x in range(200, 207):
                yy = y + dy
                if 0 <= yy < H: G[yy][x + GX] = 'lt_top' if y < 136 else ('lt_d' if x > 204 else 'lt')
    im = colorize(G, tint)
    if lighter is not None and lighter[1] is not None:
        f = lighter[1]; h = [6, 7, 5, 7, 6, 8][f % 6]; lean = [0, 1, 0, -1, 0, 0][f % 6]
        for rr in range(h):
            w = 3 if rr < h * 0.5 else (2 if rr < h * 0.75 else 1); cx = 203 + GX + round(lean * rr / h); y = 132 + lighter[0] - rr
            for x in ([cx - 1, cx, cx + 1] if w == 3 else ([cx, cx + 1] if w == 2 else [cx])): dot(im, x, y, (250, 150, 40, 255))
            if rr < h * 0.7 and w >= 2: dot(im, cx, y, (255, 220, 90, 255))
            if rr in (1, 2): dot(im, cx, y, (255, 250, 220, 255))
    if lit:                                                                  # glow: strong on a drag, otherwise a soft halo that breathes
        pulse = math.sin(2 * math.pi * phase / 8)
        R = 6 * min(S, 1.6) / 1.2 if hot else (3.3 + 0.8 * pulse) * S
        for dy_ in range(-8, 9):
            for dx_ in range(-8, 9):
                d = math.hypot(dx_, dy_)
                if 1.5 * S < d <= R:
                    al = (80 if d < 3.5 else 40) if hot else (44 if d < 2.4 * S else 22)
                    dot(im, tip[0] + dx_, tip[1] + dy_, (255, 150, 60, al))
        if not hot and phase in (2, 3, 4):                                   # a spark lifts off and fades
            k = phase - 2
            dot(im, tip[0] - 1 - k, tip[1] - 2 - 2 * k, (255, 176, 70, (235, 160, 80)[k]))
    if wisp is not None and lit:                                             # thin smoke rising from the tip
        for hgt in range(2, 34):
            if (hgt - 2 * wisp) % 16 < 10:
                x = tip[0] + round(2.2 * math.sin((hgt - 2 * wisp) * 2 * math.pi / 16) * min(1, hgt / 8))
                dot(im, x, tip[1] - hgt, (226, 226, 232, max(30, 190 - hgt * 5)))
    return im

EASE = [(34, 76), (22, 50), (13, 30), (7, 16), (3, 7), (1, 2), (0, 0), (0, 0)]
def build_smoke(tint, tag):
    A = {}
    A['smoke_raise'] = [smoking_cig(off=o, tint=tint) for o in EASE]
    LD = [60, 34, 14, 3] + [0] * 6 + [3, 14, 34, 60]
    A['smoke_light'] = [smoking_cig(tint=tint, lit=(i >= 6), hot=(6 <= i < 10), wisp=(i - 6 if i >= 6 else None), phase=i % 8,
                                     lighter=(LD[i], (i - 4) if 4 <= i < 10 else None)) for i in range(14)]
    DR = [0.2, 0.4, 0.6, 0.75, 0.8, 0.8, 0.8, 0.75, 0.6, 0.4, 0.2, 0.0]
    for lv in range(5):
        A[f'smoke_hold_{lv}'] = [smoking_cig(level=lv, lit=True, wisp=f, tint=tint, phase=f) for f in range(8)]
        A[f'smoke_drag_{lv}'] = [smoking_cig(t=tt, level=lv, lit=True, hot=(2 <= i <= 8), tint=tint, phase=i % 8) for i, tt in enumerate(DR)]
    A['smoke_lower'] = [smoking_cig(off=o, level=4, lit=True, tint=tint) for o in reversed(EASE)]
    r = random.Random(4)
    parts = [(r.uniform(0, 6), r.uniform(-1.0, 1.0), r.uniform(4.5, 7.5), r.uniform(0.8, 1.3)) for _ in range(46)]
    col = (226, 226, 232) if not tint else (150, 156, 180)
    ex = []
    for f in range(24):
        a = [[0] * W for _ in range(H)]
        for b, dirx, vy, gr in parts:
            age = f - b
            if age < 0 or age > 16: continue
            cx, cy, rad = 160 + dirx * age * 7, 186 - age * vy, 5 + age * 1.5 * gr; al = 150 * (1 - age / 16)
            for y in range(max(0, int(cy - rad)), min(H, int(cy + rad) + 1)):
                for x in range(max(0, int(cx - rad)), min(W, int(cx + rad) + 1)):
                    if (x - cx) ** 2 + (y - cy) ** 2 <= rad * rad: a[y][x] = max(a[y][x], al)
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); px = im.load()
        for y in range(H):
            for x in range(W):
                v = a[y][x]; q = 120 if v > 100 else (80 if v > 60 else (45 if v > 25 else 0))
                if q == 45 and (x + y) % 2: q = 0                 # dither the thinnest smoke
                if q: px[x, y] = col + (q,)
        ex.append(im)
    A['smoke_exhale'] = ex
    for k, fr in A.items(): strip(fr).save(f'{OUT}/{k}{tag}.png')
    return A

# ------------------------------------------------------------------ at the sill: the pack arrives, and one cigarette leaves it
BOX = (80, 110, 200, 180)
PACK = {'': Image.open(f'{OUT}/cig_pack.png').convert('RGBA'), '_night': Image.open(f'{OUT}/cig_pack_night.png').convert('RGBA')}
PACK_AT = (101 - 7, 148 - 13)
def tc(c, tint): return tuple(int(v * t) for v, t in zip(c, tint)) if tint else c
def lid(im, stage, tint):
    """Flip-top lid: stage 0 closed, 3 fully open. Opening reveals two rows of filter tips; the lid stands up behind."""
    if stage == 0: return
    x0, y0 = PACK_AT
    for d in (9, 8, 7)[:stage]:
        for a in range(13):
            if stage == 1: c = (70, 44, 40)
            elif d == 9: c = (226, 222, 210)
            else: c = (214, 156, 96) if (a + d) % 2 else (150, 100, 62)
            dot(im, x0 + 1 + a + d // 2, y0 + 10 - d, tc(c, tint) + (255,))
    hgt = {1: 2, 2: 3, 3: 5}[stage]
    for j in range(hgt):
        for a in range(13):
            c = (226, 222, 210)                                  # inside of the lid is plain card
            if j == hgt - 1 or a in (0, 12): c = (200, 32, 40)   # red rim
            if j == 0: c = (150, 144, 140)                       # hinge shadow
            dot(im, x0 + 6 + a, y0 - j, tc(c, tint) + (255,))
def stick(im, h, lift, tint):
    """A cigarette standing in the pack, filter up, h pixels showing, raised by lift."""
    for k in range(h):
        c = MAT['filter'] if (h - 1 - k) < 3 else MAT['paper']
        for x in (105, 106): dot(im, x, 137 - lift - k, tc(c if x == 105 else tuple(int(v * 0.85) for v in c), tint) + (255,))
def build_sill(tint, tag):
    A = {}
    fr = []
    for dy in [50, 36, 24, 14, 6, 0, -3, -1, 0, 0]:              # the pack slides up onto the sill and settles with a small bounce
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); im.alpha_composite(PACK[tag], (PACK_AT[0], PACK_AT[1] + dy)); fr.append(im)
    A['pack_place'] = fr
    fr = []
    def frame(stage, draw=None):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); lid(im, stage, tint)
        if draw: draw(im)
        fr.append(im)
    for st in (1, 2, 3, 3): frame(st)                            # lid flips open, a beat to see the filters
    for h in (2, 4, 6, 8, 11): frame(3, lambda im, h=h: stick(im, h, 0, tint))      # one cigarette rises out
    frame(3, lambda im: stick(im, 11, 3, tint))                  # it lifts clear
    for i in range(8):                                           # it turns over and drifts down toward the viewer while the lid shuts
        e = ((i + 1) / 8) ** 1.6
        c = (105.5 + (168 - 105.5) * e, 129 + (196 - 129) * e); ang = math.radians(90 + 139 * e); ln = 11 + 13 * e
        dx, dy = math.cos(ang) * ln / 2, math.sin(ang) * ln / 2
        def fly(im, c=c, dx=dx, dy=dy, e=e, ln=ln):
            G = new(); cig(G, (c[0] - dx, c[1] - dy), (c[0] + dx, c[1] + dy), 1.0 + 0.5 * e, False, False, 1.0, filt=3 * ln / 11)
            im.alpha_composite(colorize(G, tint))
        frame((3, 3, 2, 1, 0, 0, 0, 0)[i], fly)
    A['cig_pick'] = fr
    for k, f_ in A.items(): strip(f_, BOX).save(f'{OUT}/{k}{tag}.png')
    return A

DAY = {**build_sill(None, ''), **build_smoke(None, '')}
build_sill(NIGHT, '_night'); build_smoke(NIGHT, '_night')

# ------------------------------------------------------------------ the one-minute sequence, as data
CYCLES, HOLD_LOOPS = 5, 6
steps = [{'play': 'smoke_raise'}, {'play': 'smoke_light'}]
for i in range(CYCLES):
    steps += [{'loop': f'smoke_hold_{i}', 'times': HOLD_LOOPS}, {'play': f'smoke_drag_{i}'},
              {'play': 'smoke_exhale', 'while_looping': f'smoke_hold_{min(4, i + 1)}'}]
steps += [{'loop': 'smoke_hold_4', 'times': 2}, {'play': 'smoke_lower'}]
def expand():
    out = []                                                    # list of frames, each a list of (name, index) layers
    for s in steps:
        if 'loop' in s: out += [[(s['loop'], f)] for _ in range(s['times']) for f in range(8)]
        elif 'while_looping' in s: out += [[(s['while_looping'], f % 8), (s['play'], f)] for f in range(len(DAY[s['play']]))]
        else: out += [[(s['play'], f)] for f in range(len(DAY[s['play']]))]
    return out
TL = expand()
m = json.load(open(f'{OUT}/manifest.json'))
def entry(name, n, loop, full, note):
    m['animations'][name] = dict(files=[name + '.png', name + '_night.png'], frame_w=W if full else BOX[2] - BOX[0],
                                 frame_h=H if full else BOX[3] - BOX[1], frames=n, ms_per_frame=MS, loop=loop, anchor=[0, 0],
                                 placement={'x': 0 if full else BOX[0], 'y': 0 if full else BOX[1]}, note=note)
entry('pack_place', 10, False, False, 'The pack slides up onto the sill and settles with a small bounce. The pack is part of these frames; show cig_pack once it ends.')
entry('cig_pick', 18, False, False, 'The lid flips open showing the filters, one cigarette rises out, lifts clear, turns over and drifts down toward the viewer while the lid shuts. Draw over the static cig_pack.')
entry('smoke_raise', 8, False, True, 'An unlit cigarette rises into view at the lower middle.')
entry('smoke_light', 14, False, True, 'A lighter rises, its flame lights the tip, and it lowers.')
for i in range(5):
    entry(f'smoke_hold_{i}', 8, True, True, f'Resting pose with a lit cigarette at burn level {i} (0 = full length). The ember smoulders with drifting hot spots, a soft glow and the odd spark; a wisp of smoke rises.')
    entry(f'smoke_drag_{i}', 12, False, True, f'The cigarette comes toward the viewer until the tip glows at the bottom edge, then pulls away. Burn level {i}.')
entry('smoke_exhale', 24, False, True, 'Smoke blown from the viewer: rises from the bottom centre, spreads and fades. Partly transparent.')
entry('smoke_lower', 8, False, True, 'The cigarette lowers out of view.')
m['sequences'] = {'smoke': {'total_frames': len(TL), 'seconds': round(len(TL) * MS / 1000, 1), 'steps': steps,
                            'note': 'Play the steps in order, all at 120 ms per frame, drawn above everything else including the window. '
                                    'For "while_looping", keep the named hold loop running underneath while the other animation plays.'},
                  'get_cigarette': {'steps': [{'play': 'pack_place'}, {'play': 'cig_pick'}], 'note': 'Then start the smoke sequence.'}}
m['draw_order'] += ['pack_place / cig_pick', 'smoke_* (top)']
json.dump(m, open(f'{OUT}/manifest.json', 'w'), indent=2)

# ------------------------------------------------------------------ previews
bg = Image.open('bg_day.png').convert('RGBA'); bg.alpha_composite(Image.open(f'{OUT}/near_forest_day.png'))
bg.alpha_composite(Image.open('cabin_window.png').convert('RGBA'))
bg.alpha_composite(Image.open(f'{OUT}/mug.png').crop((0, 0, 32, 44)), (218 - 13, 146 - 40))
with_pack = bg.copy(); with_pack.alpha_composite(PACK[''], PACK_AT)
def scene(layers, base):
    c = base.copy()
    for name, f in layers: c.alpha_composite(DAY[name][f])
    return c
full = [scene([('pack_place', f)], bg) for f in range(10)] + [with_pack] * 4 + [scene([('cig_pick', f)], with_pack) for f in range(18)] + [with_pack] * 3
full += [scene(l, with_pack) for l in TL]
gf = [f.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').quantize(128) for f in full]
gf[0].save(f'{OUT}/previews/preview_smoke.gif', save_all=True, append_images=gf[1:], duration=MS, loop=0, optimize=False)
n0 = 10 + 4 + 18 + 3
keys = [2, 16, 20, 22, 25, 28, n0 + 5, n0 + 14, n0 + 26, n0 + 22 + 48 + 2, n0 + 22 + 48 + 5, n0 + 22 + 48 + 12 + 8]
sheet = Image.new('RGB', (W * 2 * 3, H * 2 * 4))
for i, k in enumerate(keys): sheet.paste(full[k].resize((W * 2, H * 2), Image.NEAREST).convert('RGB'), ((i % 3) * W * 2, (i // 3) * H * 2))
sheet.save(f'{OUT}/previews/smoke_keyframes.png')
print(len(TL), 'frames in smoke sequence =', len(TL) * MS / 1000, 's; total preview frames', len(full))
