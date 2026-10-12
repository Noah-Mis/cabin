"""
Terrarium hand tools + effect particles.

Replaces the WATER / TRIM / HARVEST buttons with objects you pick up off a
rail and carry to the pot.

Sheets produced (x4 time-of-day):
  terrarium_tools_<t>.png   48x48   3 tools x 3 states, 16x16 tiles
  terrarium_fx_<t>.png      48x48   3 effects x 3 frames, 16x16 tiles

Tool rows:   0 watering can   1 shears   2 basket
             (planting has no tool — you pick a seed straight out of the
              seed tray on the Pot tab, see the plan doc)
Tool states: 0 idle (on the rail)   1 held (follows the pointer)   2 active
FX rows:     0 droplets   1 clippings   2 collect sparkle
"""

from PIL import Image
import math

TILE = 16
TOOL_ROWS = 3        # can, shears, basket — seeds come from the tray
STATES = 3
FX_ROWS = 3
FX_FRAMES = 3
TIMES = ['morning', 'day', 'afternoon', 'night']

CAN, SHEARS, BASKET = range(3)
IDLE, HELD, ACTIVE = range(3)


def _c(v):
    return max(0, min(255, int(round(v))))


def tint(c, t):
    r, g, b = c
    if t == 'day':
        return (r, g, b)
    if t == 'morning':
        return (_c(r * 0.96 + 14), _c(g * 0.90 + 8), _c(b * 0.92 + 16))
    if t == 'afternoon':
        return (_c(r * 1.04 + 6), _c(g * 0.98 + 2), _c(b * 0.88))
    lum = r * 0.3 + g * 0.6 + b * 0.1
    return (_c(lum * 0.16 + 6), _c(lum * 0.20 + 8), _c(lum * 0.26 + 14))


def tint_ui(c, t):
    """Tools are held objects under the reader's eye, not scenery — at night
    they dim but stay legible."""
    if t != 'night':
        return tint(c, t)
    r, g, b = c
    return (_c(r * 0.58 + 4), _c(g * 0.58 + 6), _c(b * 0.64 + 12))


# ── Palette ───────────────────────────────────────────────────────────
PAL = dict(
    zinc_hi=(188, 198, 206), zinc=(146, 158, 168), zinc_d=(96, 108, 120),
    zinc_e=(58, 68, 80),
    steel_hi=(206, 212, 216), steel=(158, 166, 172), steel_d=(104, 112, 120),
    grip=(164, 82, 68), grip_d=(112, 52, 42),
    wick_hi=(214, 182, 126), wick=(178, 142, 92), wick_d=(126, 96, 58),
    kraft_hi=(220, 196, 152), kraft=(190, 162, 116), kraft_d=(138, 112, 74),
    seedc=(104, 150, 76),
    water_hi=(176, 222, 246), water=(108, 178, 224), water_d=(62, 122, 180),
    leaf=(84, 140, 68), leaf_d=(52, 94, 44),
    spark_hi=(255, 246, 198), spark=(246, 212, 110), spark_d=(198, 156, 56),
)


class Canvas:
    def __init__(self, w, h):
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.px = self.im.load()
        self.w, self.h = w, h

    def put(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = (c[0], c[1], c[2], 255)

    def save(self, p):
        self.im.save(p)
        return self.im


def pen(c, ox, oy, t):
    """A put() clipped to one 16x16 tile, with time-of-day tinting applied."""
    def p(x, y, col):
        if 0 <= x < TILE and 0 <= y < TILE:
            c.put(ox + x, oy + y, tint_ui(col, t))
    return p


# ── Watering can ──────────────────────────────────────────────────────
def can_upright(p, lift=0):
    """Body, handle, spout. `lift` nudges it up for the held state."""
    P = PAL
    oy = -lift
    for y in range(7, 14):                              # body
        f = (y - 7) / 6
        x0, x1 = 5, 12
        for x in range(x0, x1 + 1):
            if y == 7:
                p(x, y + oy, P['zinc_hi'])
            elif x <= x0 + 1:
                p(x, y + oy, P['zinc_hi'] if f < 0.6 else P['zinc'])
            elif x >= x1:
                p(x, y + oy, P['zinc_d'])
            else:
                p(x, y + oy, P['zinc'])
    for x in range(5, 13):                              # base
        p(x, 14 + oy, P['zinc_e'])
    for x in range(7, 12):                              # handle arc
        p(x, 4 + oy, P['zinc_d'])
    p(7, 5 + oy, P['zinc_d']); p(11, 5 + oy, P['zinc_d'])
    p(7, 6 + oy, P['zinc_d']); p(11, 6 + oy, P['zinc_d'])
    for i in range(4):                                  # spout up-left
        p(4 - i, 8 - i + oy, P['zinc'])
        p(4 - i, 9 - i + oy, P['zinc_d'])
    p(0, 4 + oy, P['zinc_hi'])                          # rose
    p(1, 4 + oy, P['zinc_hi'])
    p(0, 5 + oy, P['zinc_d'])
    p(1, 5 + oy, P['zinc_d'])


def can_pour_from(idle_img, t):
    """The pouring frame is the idle can rotated 90° counter-clockwise, not a
    second drawing. A 90° turn is lossless, so it stays recognisably the same
    object — every other angle tested turned to mush at 16px. Tipped this way
    the spout points down-left, handle left, base right: a can being poured.

    Returns a new 16x16 image."""
    out = idle_img.rotate(90, resample=Image.NEAREST, expand=False)
    px = out.load()

    def put(x, y, col):
        if 0 <= x < TILE and 0 <= y < TILE:
            c = tint_ui(col, t)
            px[x, y] = (c[0], c[1], c[2], 255)

    # Water leaving the rose. The spout tip lands near (3, 11) after the turn.
    for x, y in [(2, 13), (3, 14)]:
        put(x, y, PAL['water_hi'])
    for x, y in [(2, 15), (4, 15)]:
        put(x, y, PAL['water'])
    return out


def _line(p, x0, y0, x1, y1, col):
    """Bresenham. Sampling a curve at integer steps leaves dotted gaps —
    at 16px that reads as broken, so every stroke goes through here."""
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        p(x0, y0, col)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy


def _ring(p, cx, cy, col, col_d):
    """Small hollow handle loop."""
    for dx, dy in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0),
                   (-1, 1), (0, 1), (1, 1)]:
        p(cx + dx, cy + dy, col_d if dy > 0 else col)


# ── Shears ────────────────────────────────────────────────────────────
def shears(p, open_blades=False):
    """Secateurs seen side-on: blades to the upper left, pivot centre,
    looped grips to the right."""
    P = PAL
    pvx, pvy = 9, 8
    tips = [(2, 2), (2, 12)] if open_blades else [(2, 6), (2, 8)]
    for tx, ty in tips:                                 # 2px blades
        _line(p, tx, ty, pvx, pvy, P['steel_hi'])
        _line(p, tx, ty + 1, pvx, pvy + 1, P['steel'])
        p(tx, ty, P['steel_hi'])
    for dx in (0, 1):                                   # pivot rivet
        for dy in (0, 1):
            p(pvx + dx, pvy + dy, P['steel_d'])
    _line(p, pvx + 1, pvy, 12, 4, P['grip'])            # shafts to the grips
    _line(p, pvx + 1, pvy + 1, 12, 12, P['grip'])
    _ring(p, 13, 4, P['grip'], P['grip_d'])
    _ring(p, 13, 12, P['grip'], P['grip_d'])


# ── Basket ────────────────────────────────────────────────────────────
def basket(p, full=False):
    P = PAL
    for y in range(7, 14):                              # woven body, tapered
        f = (y - 7) / 6
        hw = int(round(6 - f * 1.6))
        for dx in range(-hw, hw + 1):
            x = 8 + dx
            if abs(dx) >= hw:
                p(x, y, P['wick_d'])
            elif (x + y) % 2 == 0:
                p(x, y, P['wick_hi'] if dx < 0 else P['wick'])
            else:
                p(x, y, P['wick'])
    for x in range(2, 15):                              # rim
        p(x, 6, P['wick_hi'] if x < 8 else P['wick'])
    arc = [(round(8 - math.cos(math.pi * i / 8) * 5),
            round(6 - math.sin(math.pi * i / 8) * 4)) for i in range(9)]
    for a, b in zip(arc, arc[1:]):                      # handle, unbroken
        _line(p, a[0], a[1], b[0], b[1], P['wick_d'])
    if full:
        for dx, dy in [(-2, 7), (0, 7), (2, 8), (-1, 8), (1, 7)]:
            p(8 + dx, dy, P['seedc'])
        p(8, 6, PAL['spark_hi'])


# ── Effects ───────────────────────────────────────────────────────────
def fx_droplets(p, frame):
    P = PAL
    sets = [
        [(4, 2), (8, 5), (11, 3)],
        [(4, 7), (8, 10), (11, 8), (6, 3)],
        [(4, 12), (8, 14), (11, 13), (6, 9), (9, 5)],
    ][frame]
    for x, y in sets:
        p(x, y, P['water_hi'])
        p(x, y + 1, P['water'])
        if frame == 2 and y >= 12:                      # splash on landing
            p(x - 1, y + 1, P['water_d'])
            p(x + 1, y + 1, P['water_d'])


def fx_clippings(p, frame):
    P = PAL
    sets = [
        [(5, 4, 0), (10, 3, 1)],
        [(4, 8, 1), (11, 7, 0), (7, 5, 1)],
        [(3, 12, 0), (12, 11, 1), (7, 10, 0), (9, 13, 1)],
    ][frame]
    for x, y, flip in sets:
        p(x, y, P['leaf'])
        p(x + (1 if flip else -1), y, P['leaf_d'])
        p(x, y + 1, P['leaf_d'])


def fx_sparkle(p, frame):
    P = PAL
    r = [2, 4, 6][frame]
    n = [4, 6, 8][frame]
    for i in range(n):
        a = 2 * math.pi * i / n + frame * 0.3
        x = 8 + math.cos(a) * r
        y = 8 + math.sin(a) * r * 0.85
        p(round(x), round(y), P['spark_hi'] if i % 2 else P['spark'])
    if frame < 2:
        p(8, 8, P['spark_hi'])
        p(7, 8, P['spark'])
    # frame 2 leaves the centre empty — the burst has travelled outward, and
    # a filled core there reads as a smudge rather than a flash.


# ── Generate ──────────────────────────────────────────────────────────
TOOL_DRAW = {
    (CAN, IDLE):      lambda p: can_upright(p),
    (CAN, HELD):      lambda p: can_upright(p, lift=1),
    (SHEARS, IDLE):   lambda p: shears(p, False),
    (SHEARS, HELD):   lambda p: shears(p, False),
    (SHEARS, ACTIVE): lambda p: shears(p, True),
    (BASKET, IDLE):   lambda p: basket(p, False),
    (BASKET, HELD):   lambda p: basket(p, False),
    (BASKET, ACTIVE): lambda p: basket(p, True),
}

FX_DRAW = {0: fx_droplets, 1: fx_clippings, 2: fx_sparkle}


def tile_img(drawfn, t):
    """Render one tool state into its own 16x16 image, so it can be
    transformed before being placed on the sheet."""
    c = Canvas(TILE, TILE)
    drawfn(pen(c, 0, 0, t))
    return c.im


def generate():
    for t in TIMES:
        c = Canvas(STATES * TILE, TOOL_ROWS * TILE)
        for row in range(TOOL_ROWS):
            for st in range(STATES):
                if (row, st) == (CAN, ACTIVE):
                    img = can_pour_from(tile_img(TOOL_DRAW[(CAN, IDLE)], t), t)
                else:
                    img = tile_img(TOOL_DRAW[(row, st)], t)
                c.im.alpha_composite(img, (st * TILE, row * TILE))
        c.save(f"anim/terrarium_tools_{t}.png")

        f = Canvas(FX_FRAMES * TILE, FX_ROWS * TILE)
        for row in range(FX_ROWS):
            for fr in range(FX_FRAMES):
                FX_DRAW[row](pen(f, fr * TILE, row * TILE, t), fr)
        f.save(f"anim/terrarium_fx_{t}.png")


if __name__ == '__main__':
    generate()
    print(f"tools  {STATES * TILE}x{TOOL_ROWS * TILE}   "
          f"fx  {FX_FRAMES * TILE}x{FX_ROWS * TILE}   x{len(TIMES)} times")
