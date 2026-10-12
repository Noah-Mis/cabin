"""
Terrarium plant tiles — 12 species, seam-guaranteed.

CONNECTION CONTRACT
-------------------
Plants are built by stacking tiles upward from the soil line. For that to
read as one continuous plant, every tile must hand the stem off to its
neighbour at exactly the same pixels.

  stem tiles   16x16, stem occupies x = 7,8 on BOTH the top and bottom edge
  bloom tiles  24x24, stem stub occupies x = 11,12 on the bottom edge

A bloom is drawn 4px left of the stem column, so its stub (11,12) lands on
the stem's (7,8). Nothing else crosses a tile boundary — branches and leaves
terminate inside their own tile — so there is exactly one seam to get right
and it is verified at the bottom of this file.

  stack, bottom to top:  [stem...] -> bloom      (flowering species)
                         [stem...] -> crown      (foliage species)

Sheets produced (x4 time-of-day):
  terrarium_plants_<t>.png   144x192   9 cols x 12 species, 16x16 tiles
  terrarium_blooms_<t>.png    72x288   3 cols x 12 species, 24x24 tiles
"""

from PIL import Image
import math

TILE = 16
BLOOM = 24
STEM_X = (7, 8)            # stem columns inside a 16px tile
BLOOM_STEM_X = (11, 12)    # stem stub columns inside a 24px bloom tile
BLOOM_OFFSET = -4          # bloom draws at stemX + this

# tile columns
C_SEED, C_SPROUT, C_STEM, C_STEM_LR, C_STEM_L, C_STEM_R, C_CROWN, C_DEAD, C_WILT = range(9)
NCOLS = 9
TIMES = ['morning', 'day', 'afternoon', 'night']


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


def tint_bloom(c, t):
    """Blooms are the focal point — at night they dim but keep their hue,
    otherwise every flower turns into the same grey smudge."""
    if t != 'night':
        return tint(c, t)
    r, g, b = c
    return (_c(r * 0.44 + 6), _c(g * 0.46 + 8), _c(b * 0.52 + 14))


# ── Species ───────────────────────────────────────────────────────────
# foliage: mat | frond | trefoil | simple | vine | stalk
# bloom:   none | disc | bell | tuft | cap | aurora
def S(id, name, rarity, foliage, bloom_style, stem, leaf, bloom=None,
      center=None):
    leaf_d = tuple(_c(v * 0.62) for v in leaf)
    leaf_hi = tuple(_c(v * 1.22 + 10) for v in leaf)
    stem_d = tuple(_c(v * 0.64) for v in stem)
    d = dict(id=id, name=name, rarity=rarity, foliage=foliage,
             bloom_style=bloom_style, stem=stem, stem_d=stem_d,
             leaf=leaf, leaf_d=leaf_d, leaf_hi=leaf_hi)
    if bloom:
        d['bloom'] = bloom
        d['bloom_d'] = tuple(_c(v * 0.66) for v in bloom)
        d['bloom_hi'] = tuple(_c(v * 1.18 + 16) for v in bloom)
        d['center'] = center or (220, 170, 60)
        d['center_d'] = tuple(_c(v * 0.62) for v in (center or (220, 170, 60)))
    return d


SPECIES = [
    S('moss',       'Moss',        1, 'mat',     'none',   (56, 96, 48),  (72, 128, 56)),
    S('fern',       'Fern',        1, 'frond',   'none',   (48, 88, 44),  (64, 120, 52)),
    S('clover',     'Clover',      1, 'trefoil', 'none',   (62, 110, 50), (96, 160, 72)),
    S('daisy',      'Daisy',       2, 'simple',  'disc',   (48, 88, 44),  (64, 120, 52),
      (248, 240, 200), (222, 172, 58)),
    S('wildflower', 'Wildflower',  2, 'simple',  'disc',   (48, 86, 44),  (64, 116, 52),
      (204, 84, 104),  (240, 184, 64)),
    S('mushroom',   'Mushroom',    2, 'stalk',   'cap',    (198, 188, 168), (176, 150, 120),
      (178, 104, 78),  (228, 206, 176)),
    S('bluebell',   'Bluebell',    3, 'simple',  'bell',   (56, 104, 58), (70, 128, 62),
      (108, 116, 216), (78, 84, 170)),
    S('suncap',     'Suncap',      3, 'stalk',   'cap',    (206, 192, 158), (184, 160, 120),
      (236, 164, 56),  (250, 214, 120)),
    S('ivy',        'Ivy',         3, 'vine',    'none',   (44, 92, 54),  (56, 112, 62)),
    S('thistle',    'Thistle',     4, 'simple',  'tuft',   (70, 104, 64), (84, 124, 70),
      (164, 108, 204), (112, 70, 152)),
    S('moonflower', 'Moonflower',  4, 'simple',  'bell',   (60, 100, 90), (74, 118, 104),
      (230, 234, 246), (170, 186, 214)),
    S('aurora',     'Aurora Bloom',5, 'simple',  'aurora', (46, 126, 96), (58, 148, 108),
      (84, 206, 164),  (152, 244, 214)),
]
NSPEC = len(SPECIES)


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


# ── Foliage pieces ────────────────────────────────────────────────────
def stem_span(sp):
    """Columns the stem occupies. Mushrooms get a thick stipe; everything
    else is a 2px stalk. Always includes STEM_X so the contract holds."""
    return (6, 7, 8, 9) if sp['foliage'] == 'stalk' else STEM_X


def stem_shade(sp, t):
    """Colour per column, left-lit. Returned as a dict so the seam check and
    the renderer cannot disagree about it."""
    lit, dark = tint(sp['stem'], t), tint(sp['stem_d'], t)
    span = stem_span(sp)
    if len(span) == 2:
        return {span[0]: lit, span[1]: dark}
    mid = tuple(_c((a * 2 + b) / 3) for a, b in zip(sp['stem'], sp['stem_d']))
    mid = tint(mid, t)
    return {span[0]: lit, span[1]: lit, span[2]: mid, span[3]: dark}


def draw_stem(put, y0, y1, sp, t):
    """The stem. Same columns, same colours, every tile — this is the seam."""
    sh = stem_shade(sp, t)
    for y in range(y0, y1 + 1):
        for x, col in sh.items():
            put(x, y, col)


def leaf_simple(put, ax, ay, dx, L, sp, t, droop=0.0):
    """Oval leaf sweeping out and slightly up from an attachment point."""
    lit, mid, dk = tint(sp['leaf_hi'], t), tint(sp['leaf'], t), tint(sp['leaf_d'], t)
    for i in range(L):
        f = i / max(1, L - 1)
        w = max(0, int(round(2.6 * math.sin(math.pi * min(1.0, f * 1.05 + 0.12)))))
        x = ax + dx * (i + 1)
        y = ay - f * 1.9 + droop * f * f * 4.2
        for o in range(-w, w + 1):
            put(x, round(y + o), dk if o > 0 else (lit if o < -w + 1 else mid))
    # midrib
    for i in range(L - 1):
        f = i / max(1, L - 1)
        put(ax + dx * (i + 1), round(ay - f * 1.9 + droop * f * f * 4.2), mid)


def leaf_frond(put, ax, ay, dx, L, sp, t, droop=0.0):
    """Pinnate frond — a midrib with leaflets, reads as fern at 16px."""
    mid, dk = tint(sp['leaf'], t), tint(sp['leaf_d'], t)
    lit = tint(sp['leaf_hi'], t)
    for i in range(L):
        f = i / max(1, L - 1)
        x = ax + dx * (i + 1)
        y = round(ay - f * 2.4 + droop * f * f * 4.5)
        put(x, y, mid if i % 2 else lit)
        h = max(0, int(round(2.2 * (1 - f))))
        for o in range(1, h + 1):
            put(x, y - o, lit if o == h else mid)
            put(x, y + o, dk)


def leaf_trefoil(put, ax, ay, dx, sp, t, droop=0.0):
    """Three round lobes on a short stalk."""
    mid, dk = tint(sp['leaf'], t), tint(sp['leaf_d'], t)
    lit = tint(sp['leaf_hi'], t)
    sx = ax + dx * 2
    for i in range(2):
        put(ax + dx * (i + 1), ay, mid)
    for lobe, (lx, ly) in enumerate([(2, -2), (3, 1), (1, 2)]):
        cxp, cyp = sx + dx * lx, ay + ly + int(droop * 3)
        for oy in range(-1, 2):
            for ox in range(-1, 2):
                if abs(ox) + abs(oy) <= 1:
                    put(cxp + ox, cyp + oy,
                        lit if (ox == -1 and oy == -1) else (dk if oy == 1 else mid))


def leaf_vine(put, ax, ay, dx, sp, t, droop=0.0):
    """Ivy — a small lobed heart."""
    mid, dk = tint(sp['leaf'], t), tint(sp['leaf_d'], t)
    lit = tint(sp['leaf_hi'], t)
    pts = [(1, 0), (2, -1), (3, -1), (4, 0), (2, 0), (3, 0),
           (2, 1), (3, 1), (4, 1), (3, 2)]
    for px_, py_ in pts:
        put(ax + dx * px_, ay + py_ + int(droop * 3),
            lit if py_ < 0 else (dk if py_ > 1 else mid))


def foliage(put, sp, t, ay, left, right, droop=0.0):
    """Dispatch to the species' leaf style at attachment row ay."""
    f = sp['foliage']
    for dx, on in ((-1, left), (1, right)):
        if not on:
            continue
        ax = STEM_X[0] if dx < 0 else STEM_X[1]
        if f == 'frond':
            leaf_frond(put, ax, ay, dx, 6, sp, t, droop)
        elif f == 'trefoil':
            leaf_trefoil(put, ax, ay, dx, sp, t, droop)
        elif f == 'vine':
            leaf_vine(put, ax, ay, dx, sp, t, droop)
        elif f == 'stalk':
            pass                                   # mushrooms have no leaves
        else:
            leaf_simple(put, ax, ay, dx, 6, sp, t, droop)


# ── 16x16 tiles ───────────────────────────────────────────────────────
def tile_seed(put, sp, t):
    base, dk = tint(sp['leaf'], t), tint(sp['leaf_d'], t)
    for y in range(9, 14):
        f = (y - 9) / 4
        w = int(round(2.6 * math.sin(math.pi * (0.18 + f * 0.82))))
        for x in range(8 - w, 8 + w):
            put(x, y, dk if x >= 8 else base)
    put(7, 9, tint(sp['leaf_hi'], t))


def tile_sprout(put, sp, t):
    lit = tint(sp['stem'], t)
    draw_stem(put, 8, 15, sp, t)
    put(STEM_X[0], 7, lit)
    put(STEM_X[1], 7, tint(sp['stem_d'], t))
    if sp['foliage'] == 'stalk':
        cap, cap_d = tint(sp['leaf'], t), tint(sp['leaf_d'], t)
        for x in range(5, 11):
            put(x, 6, cap if x < 8 else cap_d)
        for x in range(6, 10):
            put(x, 5, cap)
    else:
        foliage(put, sp, t, 7, True, True)


def tile_stem(put, sp, t, left=False, right=False, droop=0.0):
    draw_stem(put, 0, 15, sp, t)
    if left or right:
        foliage(put, sp, t, 9, left, right, droop)
    if sp['foliage'] == 'stalk':
        # A thick stipe needs vertical fibre, not node bumps — bumps on a
        # 4px stalk read as floating dots.
        # Rows 0 and 15 are the seam — fibre must never touch them or the
        # stem colour steps where two tiles meet.
        fib = tint(sp['stem_d'], t)
        for y in range(2, 15, 3):
            put(7, y, fib)
    else:
        put(STEM_X[0] - 1, 4, tint(sp['stem_d'], t))
        put(STEM_X[1] + 1, 11, tint(sp['stem_d'], t))


def tile_crown(put, sp, t):
    """Top cap for species that never flower."""
    draw_stem(put, 6, 15, sp, t)
    if sp['foliage'] == 'mat':
        mid, dk = tint(sp['leaf'], t), tint(sp['leaf_d'], t)
        lit = tint(sp['leaf_hi'], t)
        for y in range(4, 11):
            for x in range(2, 14):
                if (x * 5 + y * 3) % 4 == 0:
                    continue
                d = abs(x - 8) + abs(y - 7)
                if d > 7:
                    continue
                put(x, y, lit if (x + y) % 7 == 0 else (dk if y > 7 else mid))
    else:
        foliage(put, sp, t, 7, True, True)
        foliage(put, sp, t, 3, True, True)
        draw_stem(put, 2, 15, sp, t)


def tile_dead(put, sp, t):
    """Withered. Occupies the species' full stem span so a dead stack still
    stacks — when a plant dies, render every tile from this column."""
    dry = (118, 96, 62) if sp['foliage'] != 'stalk' else (120, 110, 94)
    dry_d = tuple(_c(v * 0.6) for v in dry)
    a, b = tint(dry, t), tint(dry_d, t)
    span = stem_span(sp)
    for y in range(4, 16):
        for i, x in enumerate(span):
            put(x, y, a if i < max(1, len(span) - 1) else b)
    for ox, oy, dx in [(0, 6, -1), (1, 9, 1), (0, 12, -1)]:
        ax = span[0] if dx < 0 else span[-1]
        for i in range(3):
            put(ax + dx * (i + 1), oy + i, b if i else a)
    put(span[0], 3, b)
    put(span[-1], 4, a)


def tile_wilt(put, sp, t):
    tile_stem(put, sp, t, left=True, right=True, droop=1.0)


TILE_FN = {
    C_SEED:    lambda p, s, t: tile_seed(p, s, t),
    C_SPROUT:  lambda p, s, t: tile_sprout(p, s, t),
    C_STEM:    lambda p, s, t: tile_stem(p, s, t),
    C_STEM_LR: lambda p, s, t: tile_stem(p, s, t, True, True),
    C_STEM_L:  lambda p, s, t: tile_stem(p, s, t, True, False),
    C_STEM_R:  lambda p, s, t: tile_stem(p, s, t, False, True),
    C_CROWN:   lambda p, s, t: tile_crown(p, s, t),
    C_DEAD:    lambda p, s, t: tile_dead(p, s, t),
    C_WILT:    lambda p, s, t: tile_wilt(p, s, t),
}


# ── 24x24 blooms ──────────────────────────────────────────────────────
def bloom_span(sp):
    """Stem columns inside a bloom tile — the stem tile's span shifted by the
    bloom's draw offset, so the two land on the same pixels."""
    return tuple(x - BLOOM_OFFSET for x in stem_span(sp))


def bloom_stub(put, sp, t, from_y):
    for y in range(from_y, BLOOM):
        for x, col in stem_shade(sp, t).items():
            put(x - BLOOM_OFFSET, y, col)


def _petal(put, cx, cy, ang, inner, outer, width, squash,
           col, col_d, col_hi, hi_side):
    """One tapered petal along `ang`, drawn as a filled swept blob."""
    ca, sa = math.cos(ang), math.sin(ang)
    for r in range(inner, outer + 1):
        f = (r - inner) / max(1, outer - inner)
        w = width * (1.0 - f * f * 0.82)
        steps = max(1, int(w * 2) + 1)
        for k in range(-steps, steps + 1):
            o = (k / steps) * w
            x = cx + ca * r - sa * o
            y = cy + (sa * r + ca * o) * squash
            edge = abs(o) > w * 0.62 or r >= outer - 1
            if hi_side and f < 0.55 and abs(o) < w * 0.4:
                put(round(x), round(y), col_hi)
            else:
                put(round(x), round(y), col_d if edge else col)


def _center(put, cx, cy, rad, squash, sp, t, detailed):
    cen, cen_d = tint_bloom(sp['center'], t), tint_bloom(sp['center_d'], t)
    for dy in range(-rad - 1, rad + 2):
        for dx in range(-rad - 1, rad + 2):
            if (dx / rad) ** 2 + (dy / (rad * squash)) ** 2 <= 1.0:
                edge = (dx / rad) ** 2 + (dy / (rad * squash)) ** 2 > 0.55
                put(cx + dx, round(cy + dy), cen_d if edge else cen)
    if detailed:                                   # stamen dots
        for a in range(6):
            ang = a * math.pi / 3
            put(round(cx + math.cos(ang) * rad * 0.62),
                round(cy + math.sin(ang) * rad * squash * 0.62), cen_d)
        put(cx - 1, round(cy - 1), tint_bloom(sp['bloom_hi'], t))


def bloom_disc(put, sp, t, stage, cx, cy):
    """Classic radiating flower. Rare species get a second offset ring,
    per-petal highlights and a stamen-dotted centre."""
    col = tint_bloom(sp['bloom'], t)
    col_d = tint_bloom(sp['bloom_d'], t)
    col_hi = tint_bloom(sp['bloom_hi'], t)
    rare = sp['rarity'] >= 4
    n, inner, outer, width = [(5, 2, 5, 1.5), (7, 2, 7, 1.9), (8, 3, 9, 2.4)][stage]
    if rare:
        n += 2
    squash = 0.82
    for i in range(n):
        ang = 2 * math.pi * i / n - math.pi / 2
        _petal(put, cx, cy, ang, inner, outer, width, squash,
               col, col_d, col_hi, rare and math.sin(ang) < 0.2)
    if rare and stage == 2:                        # inner ring, offset
        for i in range(n):
            ang = 2 * math.pi * (i + 0.5) / n - math.pi / 2
            _petal(put, cx, cy, ang, 2, outer - 3, width * 0.8, squash,
                   col_hi, col, col_hi, False)
    _center(put, cx, cy, [1, 2, 3][stage], squash, sp, t, rare and stage == 2)


def _bell(put, bx, by, size, col, col_d, col_hi, rare):
    """One bell hanging from (bx, by).

    A bell has to be TALLER than it is wide, and widen along a concave curve
    that levels off near the mouth. Flare it linearly and you get a triangle,
    which reads as a parasol rather than a flower."""
    h = size + 2                                   # body rows
    wmax = max(1.2, size * 0.62)
    for dy in range(2):                            # neck
        put(bx, by + dy, col)
        put(bx + 1, by + dy, col_d)
    wi = 1
    for dy in range(h):
        f = (dy + 1) / h
        wi = int(round(1 + (wmax - 1) * (f ** 0.6)))
        y = by + 2 + dy
        for dx in range(-wi, wi + 2):
            edge = dx <= -wi or dx >= wi + 1
            if not edge and dx == -wi + 1 and dy < h * 0.5:
                put(bx + dx, y, col_hi)
            else:
                put(bx + dx, y, col_d if edge else col)
    y = by + 2 + h                                 # lobed mouth
    for dx in range(-wi, wi + 2):
        put(bx + dx, y, col_d if (dx + wi) % 2 == 0 else col)
    if rare:                                       # stamens peeking out
        put(bx, y + 1, col_hi)
        put(bx + 1, y + 1, col_d)


def bloom_bell(put, sp, t, stage, cx, cy):
    """Bells hanging off arching pedicels, the way a campanula carries them."""
    col = tint_bloom(sp['bloom'], t)
    col_d = tint_bloom(sp['bloom_d'], t)
    col_hi = tint_bloom(sp['bloom_hi'], t)
    stem_c = tint(sp['stem'], t)
    rare = sp['rarity'] >= 4
    size, slots = [
        (2, [(-4, 9),  (4, 10)]),
        (3, [(-5, 7),  (5, 8)]),
        (4, [(-6, 5),  (6, 6), (0, 1)]),
    ][stage]
    top = min(y for _, y in slots) - 3
    for y in range(top, cy + 4):                   # stalk up to the pedicels
        put(cx, y, stem_c)
        put(cx + 1, y, tint(sp['stem_d'], t))
    for ox, by in slots:
        if ox:                                     # arching pedicel
            d = 1 if ox > 0 else -1
            steps = abs(ox)
            for i in range(steps + 1):
                put(cx + d * i, by - 3 + round(3 * (i / steps) ** 2), stem_c)
        _bell(put, cx + ox, by, size, col, col_d, col_hi, rare)


def bloom_tuft(put, sp, t, stage, cx, cy):
    """Thistle — an urn of green bracts with filaments spraying up out of it.
    The cup is drawn first and the spray strictly above it, so the filaments
    never cut back down through the base."""
    col = tint_bloom(sp['bloom'], t)
    col_d = tint_bloom(sp['bloom_d'], t)
    col_hi = tint_bloom(sp['bloom_hi'], t)
    leaf_c, leaf_d = tint(sp['leaf'], t), tint(sp['leaf_d'], t)
    leaf_hi = tint(sp['leaf_hi'], t)
    # Cup stays small; the spray is the plant. A big cup under a short spray
    # reads as a flat disc on a bowl.
    # Cup stays small; the spray is the plant. Filaments also start away from
    # the centre — packed together at r=1 they merge into a solid disc
    # instead of reading as separate hairs.
    spikes, length, basew, baseh = [(7, 5, 2, 3), (9, 7, 3, 3), (11, 10, 4, 4)][stage]
    # Filaments start at r=1 so the spray actually meets the cup. Starting
    # them further out leaves an empty row between head and base — the spray
    # floats. Keeping the spike count low is what stops the inner radii from
    # merging into a solid disc; pushing them outward is not.
    inner = 1

    rim = cy + 1                                   # top of the cup
    for dy in range(baseh):                        # urn: widest mid, tapering
        f = dy / max(1, baseh - 1)
        w = int(round(basew * (0.72 + 0.46 * math.sin(math.pi * (0.25 + f * 0.6)))))
        y = rim + dy
        for dx in range(-w, w + 1):
            if abs(dx) >= w - 1:
                put(cx + dx, y, leaf_d)
            elif dx < -w * 0.4 and dy < baseh - 1:
                put(cx + dx, y, leaf_hi)
            else:
                put(cx + dx, y, leaf_c)
        if dy % 2 == 0:                            # bract spines
            put(cx - w - 1, y, leaf_d)
            put(cx + w + 1, y, leaf_d)

    for i in range(spikes):                        # filament spray, upward only
        a = -math.pi / 2 + (i - (spikes - 1) / 2) * (math.pi * 0.86 / spikes)
        L = length - (abs(i - (spikes - 1) / 2) > spikes * 0.3)
        for r in range(inner, L + 1):
            x = cx + math.cos(a) * r * 1.1
            y = rim - 1 + math.sin(a) * r
            if y > rim:
                continue
            put(round(x), round(y),
                col_hi if r >= L - 1 else (col if r % 2 else col_d))
    if sp['rarity'] >= 4 and stage == 2:           # denser inner spray
        for i in range(spikes - 2):
            a = -math.pi / 2 + (i - (spikes - 3) / 2) * (math.pi * 0.74 / spikes)
            for r in range(inner - 1, length - 2):
                y = rim - 1 + math.sin(a) * r * 0.9
                if y > rim:
                    continue
                put(round(cx + math.cos(a) * r * 1.25), round(y),
                    col_hi if r == length - 3 else col)


def bloom_cap(put, sp, t, stage, cx, cy):
    """Mushroom cap — not a flower, but it's this species' mature form."""
    col = tint_bloom(sp['bloom'], t)
    col_d = tint_bloom(sp['bloom_d'], t)
    col_hi = tint_bloom(sp['bloom_hi'], t)
    gill = tint_bloom(sp['center'], t)
    rx, ry = [(5, 3), (7, 4), (9, 5)][stage]
    for dy in range(-ry, 1):
        w = int(round(rx * math.sqrt(max(0.0, 1 - (dy / ry) ** 2))))
        if w < 2:
            continue              # skip the ellipse's degenerate tip — it
                                  # renders as one stray pixel above the cap
        for dx in range(-w, w + 1):
            y = cy + dy
            if abs(dx) >= w - 1 or dy == -ry:
                put(cx + dx, y, col_d)
            elif dx < -w * 0.35 and dy < -ry * 0.3:
                put(cx + dx, y, col_hi)
            else:
                put(cx + dx, y, col)
    for dx in range(-rx + 1, rx):                  # gills under the cap
        put(cx + dx, cy + 1, gill if dx % 2 else col_d)
    if stage == 2:                                 # cap speckles
        for ox, oy in [(-3, -3), (2, -4), (4, -2), (-5, -1), (0, -2)]:
            if abs(ox) < rx - 1:
                put(cx + ox, cy + oy, col_hi)


def bloom_aurora(put, sp, t, stage, cx, cy):
    """Legendary — layered star petals, inner corona, drifting motes."""
    col = tint_bloom(sp['bloom'], t)
    col_d = tint_bloom(sp['bloom_d'], t)
    col_hi = tint_bloom(sp['bloom_hi'], t)
    cen = tint_bloom(sp['center'], t)
    n, inner, outer, width = [(6, 2, 5, 1.4), (8, 2, 7, 1.9), (10, 3, 10, 2.3)][stage]
    squash = 0.86
    for i in range(n):                             # long outer star points
        ang = 2 * math.pi * i / n - math.pi / 2
        _petal(put, cx, cy, ang, inner, outer, width, squash,
               col, col_d, col_hi, True)
    for i in range(n):                             # mid ring, offset
        ang = 2 * math.pi * (i + 0.5) / n - math.pi / 2
        _petal(put, cx, cy, ang, 2, max(3, outer - 4), width * 0.75, squash,
               col_hi, col, col_hi, False)
    if stage == 2:                                 # inner corona
        for i in range(n * 2):
            ang = 2 * math.pi * i / (n * 2)
            put(round(cx + math.cos(ang) * 3.2),
                round(cy + math.sin(ang) * 3.2 * squash), col_hi)
    _center(put, cx, cy, [1, 2, 3][stage], squash, sp, t, stage == 2)
    if stage == 2:                                 # motes
        for ox, oy in [(-9, -6), (9, -5), (-7, 5), (8, 6), (0, -11), (-11, 0)]:
            put(cx + ox, cy + oy, col_hi)


BLOOM_FN = {'disc': bloom_disc, 'bell': bloom_bell, 'tuft': bloom_tuft,
            'cap': bloom_cap, 'aurora': bloom_aurora}


def draw_bloom_tile(put, sp, t, stage):
    span = bloom_span(sp)
    cx = (span[0] + span[-1]) // 2
    head_y = [13, 11, 10][stage]
    # Where the stem has to reach depends on how low the head hangs. A petal
    # mass covers its own join, but a mushroom's gills sit at head_y + 1, so a
    # flat stub row leaves the cap floating above the stipe.
    if sp['bloom_style'] == 'cap':
        stub_from = head_y + 2
    else:
        stub_from = [16, 15, 14][stage]
    bloom_stub(put, sp, t, stub_from)
    BLOOM_FN[sp['bloom_style']](put, sp, t, stage, cx, head_y)
    if sp['bloom_style'] != 'cap':
        bloom_stub(put, sp, t, stub_from + 2)      # redraw over petal spill


# ── Generate ──────────────────────────────────────────────────────────
def generate():
    for t in TIMES:
        sheet = Canvas(NCOLS * TILE, NSPEC * TILE)
        for si, sp in enumerate(SPECIES):
            for col in range(NCOLS):
                ox, oy = col * TILE, si * TILE
                put = lambda x, y, c, ox=ox, oy=oy: (
                    sheet.put(ox + x, oy + y, c) if 0 <= x < TILE and 0 <= y < TILE else None)
                TILE_FN[col](put, sp, t)
        sheet.save(f"anim/terrarium_plants_{t}.png")

        bl = Canvas(3 * BLOOM, NSPEC * BLOOM)
        for si, sp in enumerate(SPECIES):
            if sp['bloom_style'] == 'none':
                continue
            for stage in range(3):
                ox, oy = stage * BLOOM, si * BLOOM
                put = lambda x, y, c, ox=ox, oy=oy: (
                    sheet_put(bl, ox, oy, x, y, c))
                draw_bloom_tile(put, sp, t, stage)
        bl.save(f"anim/terrarium_blooms_{t}.png")
    return True


def sheet_put(canvas, ox, oy, x, y, c):
    if 0 <= x < BLOOM and 0 <= y < BLOOM:
        canvas.put(ox + x, oy + y, c)


# ── Contract verification ─────────────────────────────────────────────
def verify():
    """Every seam, checked. A tile that must pass the stem on has to have
    opaque pixels at the contract columns, and the colours either side of a
    join must match or the stem visibly steps."""
    need_top = {C_STEM, C_STEM_LR, C_STEM_L, C_STEM_R, C_WILT}
    need_bot = {C_STEM, C_STEM_LR, C_STEM_L, C_STEM_R, C_WILT,
                C_CROWN, C_DEAD}
    fails = []
    for t in TIMES:
        im = Image.open(f"anim/terrarium_plants_{t}.png").convert("RGBA")
        px = im.load()
        bl = Image.open(f"anim/terrarium_blooms_{t}.png").convert("RGBA")
        bpx = bl.load()
        for si, sp in enumerate(SPECIES):
            oy = si * TILE
            span = stem_span(sp)
            bspan = bloom_span(sp)
            for col in range(NCOLS):
                ox = col * TILE
                for sx in span:
                    if col in need_top and px[ox + sx, oy][3] == 0:
                        fails.append(f"{t}/{sp['id']}/col{col}: top gap x={sx}")
                    if col in need_bot and px[ox + sx, oy + TILE - 1][3] == 0:
                        fails.append(f"{t}/{sp['id']}/col{col}: bottom gap x={sx}")
            # stem colour must be identical across a stem-to-stem join, and
            # identical BETWEEN tiles — stacking mixes the variants freely
            ref = {sx: px[C_STEM * TILE + sx, oy] for sx in span}
            for col in (C_STEM, C_STEM_LR, C_STEM_L, C_STEM_R):
                for sx in span:
                    top = px[col * TILE + sx, oy]
                    bot = px[col * TILE + sx, oy + TILE - 1]
                    if top != bot:
                        fails.append(f"{t}/{sp['id']}/col{col}: stem steps within "
                                     f"tile at x={sx} ({top} vs {bot})")
                    if top != ref[sx]:
                        fails.append(f"{t}/{sp['id']}/col{col}: stem differs from "
                                     f"plain stem at x={sx} ({top} vs {ref[sx]})")
            # Nothing may float. Flood-fill from the stub at the bottom edge;
            # every opaque pixel has to be reachable. This is what catches a
            # head drawn too high above the stem it is supposed to sit on.
            if sp['bloom_style'] != 'none':
                for stage in range(3):
                    bx0, by0 = stage * BLOOM, si * BLOOM
                    opaque = {(x, y) for y in range(BLOOM) for x in range(BLOOM)
                              if bpx[bx0 + x, by0 + y][3] != 0}
                    seeds = [(x, BLOOM - 1) for x in bspan
                             if (x, BLOOM - 1) in opaque]
                    seen, stackq = set(seeds), list(seeds)
                    nbr = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
                    while stackq:
                        x, y = stackq.pop()
                        for ddx, ddy in nbr:
                            nxy = (x + ddx, y + ddy)
                            if nxy in opaque and nxy not in seen:
                                seen.add(nxy)
                                stackq.append(nxy)
                    orphan = opaque - seen
                    # group orphans; 1-2px specks are deliberate (aurora motes)
                    while orphan:
                        start = next(iter(orphan))
                        comp, q = {start}, [start]
                        orphan.discard(start)
                        while q:
                            x, y = q.pop()
                            for ddx, ddy in nbr:
                                nxy = (x + ddx, y + ddy)
                                if nxy in orphan:
                                    orphan.discard(nxy)
                                    comp.add(nxy)
                                    q.append(nxy)
                        if len(comp) >= 4:
                            ys = sorted(c[1] for c in comp)
                            fails.append(f"{t}/{sp['id']}/bloom{stage}: {len(comp)}px "
                                         f"detached from stem (rows {ys[0]}-{ys[-1]})")

            # bloom stub must land on, and match, the stem it sits on
            if sp['bloom_style'] != 'none':
                for stage in range(3):
                    bx0 = stage * BLOOM
                    for k, sx in enumerate(bspan):
                        stub = bpx[bx0 + sx, si * BLOOM + BLOOM - 1]
                        stem = ref[span[k]]
                        if stub[3] == 0:
                            fails.append(f"{t}/{sp['id']}/bloom{stage}: stub gap x={sx}")
                        elif stub != stem:
                            fails.append(f"{t}/{sp['id']}/bloom{stage}: stub colour "
                                         f"mismatch x={sx} ({stub} vs {stem})")
    return fails


if __name__ == '__main__':
    generate()
    print(f"plants  {NCOLS * TILE}x{NSPEC * TILE}   blooms  {3 * BLOOM}x{NSPEC * BLOOM}"
          f"   x{len(TIMES)} times")
    f = verify()
    if f:
        print(f"\nCONTRACT FAILURES ({len(f)}):")
        for line in f[:25]:
            print("  ", line)
        if len(f) > 25:
            print(f"   ... and {len(f) - 25} more")
    else:
        print("seam contract: all tiles pass")
