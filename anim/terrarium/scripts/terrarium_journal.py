"""
Terrarium Field Journal — complete minigame UI asset set.

DESIGN PREMISE
--------------
The pot on the wall is your ONE growing slot. The journal is where the
game lives: seed inventory, the crossing bench, and the species codex.

    plant seed -> water over real time -> harvest at maturity ->
    cross two seeds in the journal -> new hybrid seed -> plant it ->
    codex fills up

This respects the approved single-pot asset (no new wall furniture) while
giving breeding a real home.

Assets produced (all x4 time-of-day):
  terrarium_journal_<t>.png      164x124  panel w/ 4 baked inactive tabs
  terrarium_tab_active_<t>.png    14x22   active-tab overlay
  terrarium_tabicons_<t>.png      40x10   4 tab icons (10x10 each)
  terrarium_seeds_<t>.png         96x8    12 seed sprites (8x8 each)
  terrarium_codex_<t>.png        192x16   12 species portraits (16x16 each)
  terrarium_slot_sm_<t>.png       64x16   4 slot states (16x16 each)
  terrarium_slot_lg_<t>.png       60x20   3 slot states (20x20 each)
  terrarium_meter_<t>.png         50x60   water 0-4 (y0-29), growth 0-4 (y30-59)
  terrarium_btn_sm_<t>.png        84x16   3 states (28x16 each)
  terrarium_btn_lg_<t>.png       144x16   3 states (48x16 each)
  terrarium_traits_<t>.png        48x8    6 trait icons (8x8 each)
  terrarium_stars_<t>.png         14x7    empty + filled star (7x7 each)
  terrarium_popup_pot_<t>.png     48x40   zoomed pot cross-section
"""

from PIL import Image
import random
import math
import pixfont

random.seed(7)

W_CANVAS, H_CANVAS = 320, 180

# ── Panel geometry ────────────────────────────────────────────────────
PANEL_W, PANEL_H = 164, 124
PAPER_W = 150                      # paper ends here; tabs protrude right
TAB_W, TAB_H = 16, 22    # 16 = PANEL_W - (PAPER_W - 2); the active
                         # overlay must match the baked tab exactly or the
                         # inactive tab shows through on the right
TAB_YS = [10, 36, 62, 88]          # four tab top-edges
PANEL_X, PANEL_Y = 78, 28          # centered on canvas

POTPANEL_W, POTPANEL_H = 48, 40
METER_W, METER_H = 50, 6
SLOT_SM, SLOT_LG = 16, 20
BTN_SM_W, BTN_LG_W, BTN_H = 40, 48, 16   # 40 fits "Harvest" (27px ink) + 6px pad
SEED_PX, CODEX_PX, TRAIT_PX, STAR_PX = 8, 16, 8, 7

TIMES = ['morning', 'day', 'afternoon', 'night']


# ── Time-of-day tinting ───────────────────────────────────────────────
def _c(v):
    return max(0, min(255, int(round(v))))


def tint(c, t):
    """Shift a day-base colour into another time of day."""
    r, g, b = c
    if t == 'day':
        return (r, g, b)
    if t == 'morning':                       # cool dawn, pink lift
        return (_c(r * 0.96 + 14), _c(g * 0.90 + 8), _c(b * 0.92 + 16))
    if t == 'afternoon':                     # golden hour
        return (_c(r * 1.04 + 6), _c(g * 0.98 + 2), _c(b * 0.88))
    # night — collapse to luminance, push blue, crush value
    lum = r * 0.3 + g * 0.6 + b * 0.1
    return (_c(lum * 0.16 + 6), _c(lum * 0.20 + 8), _c(lum * 0.26 + 14))


def tint_ui(c, t):
    """UI accents — meter fills, stars, trait glyphs — are lit indicators,
    not scenery. At night they dim but keep their hue, or they vanish
    against the dark paper."""
    if t != 'night':
        return tint(c, t)
    r, g, b = c
    return (_c(r * 0.62), _c(g * 0.62), _c(b * 0.68))


# ── Paper / chrome palette ────────────────────────────────────────────
PAPER = {
    'day':       dict(bg=(242,234,218), bg_d=(228,218,198), line=(180,168,148),
                      border=(120,104,80), border_d=(88,76,58), text=(52,44,34),
                      text_d=(96,84,68), accent=(140,88,48), tab=(206,190,164),
                      tab_d=(170,152,126), slot=(220,210,190), slot_d=(176,162,138),
                      btn=(206,186,154), btn_hi=(228,212,184), btn_lo=(150,132,106)),
    'morning':   dict(bg=(244,230,212), bg_d=(232,216,196), line=(184,164,142),
                      border=(124,100,74), border_d=(90,72,54), text=(56,42,32),
                      text_d=(100,80,64), accent=(144,84,44), tab=(208,186,160),
                      tab_d=(172,148,122), slot=(222,206,186), slot_d=(178,158,134),
                      btn=(208,182,150), btn_hi=(230,208,180), btn_lo=(152,128,102)),
    'afternoon': dict(bg=(246,236,214), bg_d=(234,222,196), line=(186,172,146),
                      border=(126,108,78), border_d=(92,78,56), text=(54,46,32),
                      text_d=(98,86,66), accent=(146,92,46), tab=(210,194,162),
                      tab_d=(174,156,124), slot=(224,212,188), slot_d=(180,164,136),
                      btn=(210,190,152), btn_hi=(232,216,182), btn_lo=(154,134,104)),
    'night':     dict(bg=(38,36,46), bg_d=(30,28,38), line=(52,48,62),
                      border=(24,22,32), border_d=(16,14,22), text=(160,152,140),
                      text_d=(100,94,86), accent=(88,72,52), tab=(46,44,56),
                      tab_d=(32,30,40), slot=(30,28,38), slot_d=(50,46,60),
                      btn=(52,48,62), btn_hi=(70,66,82), btn_lo=(28,26,36)),
}

UI = {   # day-base; tinted per time
    'water':  (80,140,200), 'water_hi': (124,186,232), 'water_lo': (52,100,160),
    'growth': (96,164,84),  'growth_hi': (138,204,120), 'growth_lo': (60,116,56),
    'blade':  (160,168,170),'blade_d': (116,124,128),  'handle': (122,88,52),
    'gold':   (226,178,68), 'gold_d': (176,132,44),
    'lock':   (118,110,98), 'lock_d': (82,76,66),
}


# ── Species table ─────────────────────────────────────────────────────
# parents=None  -> starter seed, available from the start
# parents=(a,b) -> hybrid, discovered by crossing a x b
SPECIES = [
    dict(id='moss',       name='Moss',        rarity=1, parents=None,
         seed='spore',    base=(72,128,56),  accent=(40,76,36),   bloom=None,            center=None),
    dict(id='fern',       name='Fern',        rarity=1, parents=None,
         seed='oval',     base=(64,120,52),  accent=(36,72,34),   bloom=None,            center=None),
    dict(id='clover',     name='Clover',      rarity=1, parents=None,
         seed='round',    base=(96,160,72),  accent=(52,100,44),  bloom=None,            center=None),
    dict(id='daisy',      name='Daisy',       rarity=2, parents=None,
         seed='teardrop', base=(64,120,52),  accent=(36,72,34),   bloom=(248,240,200),   center=(220,170,60)),
    dict(id='wildflower', name='Wildflower',  rarity=2, parents=None,
         seed='teardrop', base=(64,116,52),  accent=(36,70,34),   bloom=(204,84,104),    center=(240,184,64)),
    dict(id='mushroom',   name='Mushroom',    rarity=2, parents=None,
         seed='spore',    base=(200,190,170),accent=(140,88,64),  bloom=(180,120,90),    center=None),
    dict(id='bluebell',   name='Bluebell',    rarity=3, parents=('daisy','wildflower'),
         seed='bell',     base=(56,110,60),  accent=(32,66,38),   bloom=(108,116,216),   center=(80,84,170)),
    dict(id='suncap',     name='Suncap',      rarity=3, parents=('mushroom','daisy'),
         seed='spore',    base=(206,186,150),accent=(150,112,60), bloom=(236,164,56),    center=None),
    dict(id='ivy',        name='Ivy',         rarity=3, parents=('fern','clover'),
         seed='winged',   base=(44,96,56),   accent=(24,60,38),   bloom=None,            center=None),
    dict(id='thistle',    name='Thistle',     rarity=4, parents=('wildflower','fern'),
         seed='spiky',    base=(70,104,64),  accent=(40,64,42),   bloom=(156,104,196),   center=(110,70,150)),
    dict(id='moonflower', name='Moonflower',  rarity=4, parents=('bluebell','mushroom'),
         seed='bell',     base=(60,96,88),   accent=(32,58,54),   bloom=(226,230,244),   center=(170,186,214)),
    dict(id='aurora',     name='Aurora Bloom',rarity=5, parents=('moonflower','suncap'),
         seed='winged',   base=(52,140,100), accent=(30,80,60),   bloom=(80,200,160),    center=(140,236,208)),
]
NSPEC = len(SPECIES)


# ── Pixel helper ──────────────────────────────────────────────────────
class Canvas:
    def __init__(self, w, h):
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.px = self.im.load()
        self.w, self.h = w, h

    def put(self, x, y, c, a=255):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = (c[0], c[1], c[2], a) if len(c) == 3 else c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.put(x, y, c)

    def frame(self, x0, y0, x1, y1, c):
        for x in range(int(x0), int(x1) + 1):
            self.put(x, y0, c); self.put(x, y1, c)
        for y in range(int(y0), int(y1) + 1):
            self.put(x0, y, c); self.put(x1, y, c)

    def save(self, path):
        self.im.save(path)
        return self.im


# ── 1. Journal panel ──────────────────────────────────────────────────
def draw_journal(t):
    p = PAPER[t]
    c = Canvas(PANEL_W, PANEL_H)

    # Tabs first, so the paper body overlaps their left edge cleanly.
    # These must reach PANEL_W - 1. Stopping at PANEL_W - 2 leaves column 163
    # never written — a 1px transparent strip down the whole right edge that
    # shows the scene through the panel.
    for ty in TAB_YS:
        c.rect(PAPER_W - 2, ty + 1, PANEL_W - 2, ty + TAB_H - 2, p['tab'])
        c.rect(PANEL_W - 1, ty + 3, PANEL_W - 1, ty + TAB_H - 4, p['tab_d'])
        c.frame(PAPER_W - 2, ty, PANEL_W - 1, ty + TAB_H - 1, p['border_d'])
        for corner in [(PANEL_W-1, ty), (PANEL_W-1, ty+TAB_H-1)]:
            c.put(corner[0], corner[1], (0,0,0,0))

    # Paper body + subtle fibre texture. This has to reach PAPER_W - 2: the
    # tabs attach at that column, so stopping a pixel short leaves a 1px
    # transparent seam between tabs, walled in by paper on one side and the
    # right border on the other.
    c.rect(2, 2, PAPER_W - 2, PANEL_H - 3, p['bg'])
    for y in range(2, PANEL_H - 2):
        for x in range(2, PAPER_W - 1):
            if (x * 3 + y * 7) % 23 == 0:
                c.put(x, y, p['bg_d'])

    # Border
    for x in range(PAPER_W):
        c.put(x, 0, p['border']);            c.put(x, 1, p['border_d'])
        c.put(x, PANEL_H - 1, p['border']);  c.put(x, PANEL_H - 2, p['border_d'])
    for y in range(PANEL_H):
        c.put(0, y, p['border']);            c.put(1, y, p['border_d'])
        c.put(PAPER_W - 1, y, p['border_d'])
    for cx, cy in [(0,0),(1,0),(0,1),(0,PANEL_H-1),(1,PANEL_H-1),(0,PANEL_H-2)]:
        c.put(cx, cy, (0,0,0,0))

    # Ruled lines + red margin
    for ly in range(26, PANEL_H - 12, 10):
        for x in range(12, PAPER_W - 6):
            if (x + ly) % 4 != 0:
                c.put(x, ly, p['line'])
    for y in range(4, PANEL_H - 4):
        c.put(9, y, p['accent'])
        if y % 3 == 0:
            c.put(10, y, p['accent'])

    # Spiral binding holes down the left edge
    for hy in range(12, PANEL_H - 10, 18):
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                d = dx*dx + dy*dy
                if d <= 4:
                    c.put(5 + dx, hy + dy, (0,0,0,0) if d <= 2 else p['border_d'])

    # Header rule under the title zone
    for x in range(12, 92):
        if (x + 17) % 3 != 0:
            c.put(x, 17, p['line'])

    # Footer divider above the action row
    for x in range(6, PAPER_W - 6):
        if (x + 100) % 3 != 0:
            c.put(x, 100, p['line'])

    return c.save(f"anim/terrarium_journal_{t}.png")


def draw_tab_active(t):
    p = PAPER[t]
    c = Canvas(TAB_W, TAB_H)
    c.rect(0, 1, TAB_W - 2, TAB_H - 2, p['bg'])
    c.rect(TAB_W - 1, 3, TAB_W - 1, TAB_H - 4, p['bg_d'])
    c.frame(0, 0, TAB_W - 1, TAB_H - 1, p['border'])
    for x in range(0, 3):                       # open left edge -> joins the page
        for y in range(1, TAB_H - 1):
            c.put(x, y, p['bg'])
    c.put(TAB_W - 1, 0, (0,0,0,0)); c.put(TAB_W - 1, TAB_H - 1, (0,0,0,0))
    return c.save(f"anim/terrarium_tab_active_{t}.png")


def draw_tab_icons(t):
    """10x10 each: pot, seed, cross, book."""
    p = PAPER[t]
    ink, ink_d = p['text'], p['text_d']
    c = Canvas(40, 10)

    # 0 pot
    c.rect(2, 2, 8, 3, ink); c.rect(3, 4, 7, 7, ink_d); c.rect(4, 8, 6, 8, ink)
    # 1 seed
    for y in range(2, 9):
        hw = 3 - abs(y - 5) // 2
        c.rect(15 - hw, y, 15 + hw, y, ink_d)
    c.put(15, 3, ink); c.put(14, 4, ink)
    # 2 cross (two arrows meeting)
    for i in range(4):
        c.put(22 + i, 2 + i, ink); c.put(27 - i, 2 + i, ink)
    c.rect(24, 6, 25, 8, ink_d); c.put(23, 5, ink_d); c.put(26, 5, ink_d)
    # 3 book
    c.rect(32, 2, 38, 8, ink_d); c.rect(33, 3, 34, 7, ink); c.rect(36, 3, 37, 7, ink)
    c.rect(35, 2, 35, 8, ink)
    return c.save(f"anim/terrarium_tabicons_{t}.png")


# ── 2. Seeds ──────────────────────────────────────────────────────────
def _seed_shape(c, ox, shape, base, accent):
    """Draw one 8x8 seed at x-offset ox."""
    P = lambda x, y, col: c.put(ox + x, y, col)
    if shape == 'round':
        for y in range(1, 7):
            hw = 3 - (1 if y in (1, 6) else 0)
            for x in range(4 - hw, 4 + hw):
                P(x, y, base if (x + y) % 3 else accent)
        P(2, 2, accent); P(5, 5, accent)
    elif shape == 'oval':
        for y in range(1, 7):
            hw = 2 if y in (1, 6) else 3
            for x in range(4 - hw, 4 + hw):
                P(x, y, base)
        for y in range(2, 6):
            P(3, y, accent)
    elif shape == 'teardrop':
        for y in range(1, 7):
            hw = max(1, (y - 1) // 2 + 1)
            for x in range(4 - hw, 4 + hw):
                P(x, y, base)
        P(4, 1, accent); P(3, 5, accent); P(4, 6, accent)
    elif shape == 'spore':
        for x, y in [(3,2),(4,2),(2,3),(3,3),(4,3),(5,3),
                     (2,4),(3,4),(4,4),(5,4),(3,5),(4,5)]:
            P(x, y, base)
        for x, y in [(2,2),(5,2),(2,5),(5,5),(4,6)]:
            P(x, y, accent)
    elif shape == 'bell':
        P(4, 1, accent)
        for y in range(2, 6):
            hw = y - 1
            for x in range(4 - hw, 4 + hw):
                P(x, y, base)
        for x in range(1, 7):
            P(x, 6, accent)
    elif shape == 'winged':
        for y in range(2, 6):
            P(4, y, base); P(3, y, base)
        for i in range(3):
            P(1 + i, 2 + i, accent); P(6 - i, 2 + i, accent)
        P(3, 6, accent); P(4, 6, accent)
    elif shape == 'spiky':
        for y in range(2, 6):
            for x in range(2, 6):
                P(x, y, base)
        for x, y in [(1,1),(6,1),(1,6),(6,6),(4,0),(3,7),(0,3),(7,4)]:
            P(x, y, accent)


def seed_colors(s):
    """A seed is colour-coded by the species' signature colour so the
    inventory reads at a glance: bloom colour when the plant flowers,
    foliage otherwise."""
    if s['bloom']:
        return s['bloom'], (s['center'] or s['accent'])
    return s['base'], s['accent']


def draw_seeds(t):
    c = Canvas(SEED_PX * NSPEC, SEED_PX)
    for i, s in enumerate(SPECIES):
        base, acc = seed_colors(s)
        _seed_shape(c, i * SEED_PX, s['seed'], tint(base, t), tint(acc, t))
    return c.save(f"anim/terrarium_seeds_{t}.png")


# ── 3. Codex portraits ────────────────────────────────────────────────
def draw_codex(t):
    c = Canvas(CODEX_PX * NSPEC, CODEX_PX)
    for i, s in enumerate(SPECIES):
        ox = i * CODEX_PX
        base, acc = tint(s['base'], t), tint(s['accent'], t)
        bloom = tint(s['bloom'], t) if s['bloom'] else None
        cen = tint(s['center'], t) if s['center'] else None
        P = lambda x, y, col: c.put(ox + x, y, col)

        if s['id'] == 'moss':                      # low cushion mat
            for y in range(10, 15):
                for x in range(2, 14):
                    if (x * 5 + y * 3) % 4 != 0:
                        P(x, y, base if (x + y) % 3 else acc)
            for x in range(3, 13, 3):
                P(x, 9, base)

        elif s['id'] == 'mushroom' or s['id'] == 'suncap':
            capcol = bloom if bloom else base
            for y in range(4, 9):                  # cap
                hw = 6 - abs(y - 6)
                for x in range(8 - hw, 8 + hw):
                    P(x, y, capcol if (x + y) % 4 else acc)
            for y in range(9, 14):                 # stem
                P(7, y, base); P(8, y, base); P(6, y, acc)
            for x in range(5, 11):
                P(x, 14, acc)
            for x, y in [(5,5),(10,6),(7,4)]:      # cap speckles
                P(x, y, acc)

        else:                                       # stem + leaves (+ bloom)
            for y in range(6, 15):                 # stem
                P(8, y, base)
                if y % 2 == 0:
                    P(7, y, acc)
            leafrows = [(9, 3), (11, 4), (13, 3)]
            for ly, span in leafrows:              # paired leaves
                for i in range(span):
                    P(7 - i, ly - i // 2, base)
                    P(9 + i, ly - i // 2, base)
                P(7 - span + 1, ly - span // 2, acc)
                P(9 + span - 1, ly - span // 2, acc)
            if s['id'] == 'ivy':                   # extra climbing leaves
                for ly in [7, 10, 12]:
                    P(10, ly, base); P(11, ly - 1, acc)
            if s['id'] == 'thistle':               # spiky tuft
                for i in range(5):
                    P(6 + i, 2 + (i % 2), bloom)
                    P(6 + i, 4, cen)
                P(8, 1, bloom)
            elif s['id'] in ('bluebell', 'moonflower'):   # hanging bells
                for bx in (6, 10):
                    P(bx, 4, acc)
                    for by in range(5, 8):
                        hw = by - 4
                        for x in range(bx - hw + 1, bx + hw):
                            P(x, by, bloom)
                    P(bx, 8, cen)
            elif bloom:                            # round flower head
                for y in range(2, 7):
                    hw = 3 - abs(y - 4)
                    for x in range(8 - hw - 1, 8 + hw + 1):
                        P(x, y, bloom)
                P(8, 4, cen); P(7, 4, cen)
                if s['id'] == 'aurora':            # glow halo
                    for x, y in [(4,4),(12,4),(8,0),(5,1),(11,1)]:
                        P(x, y, cen)
    return c.save(f"anim/terrarium_codex_{t}.png")


# ── 4. Slots ──────────────────────────────────────────────────────────
def _slot(c, ox, size, p, state):
    """state: empty | hover | filled | locked"""
    fill = {'empty': p['slot'], 'hover': p['btn_hi'],
            'filled': p['bg'],  'locked': p['slot_d']}[state]
    edge = {'empty': p['slot_d'], 'hover': p['accent'],
            'filled': p['border_d'], 'locked': p['border_d']}[state]
    c.rect(ox + 1, 1, ox + size - 2, size - 2, fill)
    c.frame(ox, 0, ox + size - 1, size - 1, edge)
    for dx, dy in [(0,0),(size-1,0),(0,size-1),(size-1,size-1)]:
        c.put(ox + dx, dy, (0,0,0,0))
    if state == 'locked':                          # hatching
        for y in range(2, size - 2):
            for x in range(2, size - 2):
                if (x + y) % 3 == 0:
                    c.put(ox + x, y, p['border_d'])
    if state == 'hover':                           # corner ticks
        for d in range(3):
            c.put(ox + 1 + d, 1, p['accent']); c.put(ox + 1, 1 + d, p['accent'])
            c.put(ox + size - 2 - d, size - 2, p['accent'])
            c.put(ox + size - 2, size - 2 - d, p['accent'])


def draw_slots(t):
    p = PAPER[t]
    c = Canvas(SLOT_SM * 4, SLOT_SM)
    for i, st in enumerate(['empty', 'hover', 'filled', 'locked']):
        _slot(c, i * SLOT_SM, SLOT_SM, p, st)
    c.save(f"anim/terrarium_slot_sm_{t}.png")

    c2 = Canvas(SLOT_LG * 3, SLOT_LG)
    for i, st in enumerate(['empty', 'hover', 'filled']):
        _slot(c2, i * SLOT_LG, SLOT_LG, p, st)
    return c2.save(f"anim/terrarium_slot_lg_{t}.png")


# ── 5. Meters (water + growth) ────────────────────────────────────────
def draw_meter(t):
    p = PAPER[t]
    c = Canvas(METER_W, METER_H * 10)
    for kind, row0 in (('water', 0), ('growth', 5)):
        fillc = tint_ui(UI[kind], t)
        hic   = tint_ui(UI[kind + '_hi'], t)
        for state in range(5):
            oy = (row0 + state) * METER_H
            fw = int(state / 4 * (METER_W - 4))
            c.rect(1, oy + 1, METER_W - 2, oy + METER_H - 2, p['bg_d'])
            for x in range(2, 2 + fw):
                c.put(x, oy + 2, hic)
                for y in range(oy + 3, oy + METER_H - 2):
                    c.put(x, y, fillc)
            c.frame(0, oy, METER_W - 1, oy + METER_H - 1, p['border_d'])
            for tk in range(1, 4):                 # quarter ticks
                tx = 2 + int(tk * 0.25 * (METER_W - 4))
                c.put(tx, oy, p['border']); c.put(tx, oy + METER_H - 1, p['border'])
    return c.save(f"anim/terrarium_meter_{t}.png")


# ── 6. Buttons ────────────────────────────────────────────────────────
def _button(c, ox, w, p, state):
    face = {'normal': p['btn'], 'hover': p['btn_hi'], 'disabled': p['bg_d']}[state]
    edge = {'normal': p['border_d'], 'hover': p['accent'], 'disabled': p['slot_d']}[state]
    c.rect(ox + 1, 1, ox + w - 2, BTN_H - 2, face)
    c.rect(ox + 1, BTN_H - 3, ox + w - 2, BTN_H - 2, p['btn_lo'] if state != 'disabled' else p['bg_d'])
    c.rect(ox + 1, 1, ox + w - 2, 2, p['btn_hi'] if state == 'normal' else face)
    c.frame(ox, 0, ox + w - 1, BTN_H - 1, edge)
    for dx, dy in [(0,0),(w-1,0),(0,BTN_H-1),(w-1,BTN_H-1)]:
        c.put(ox + dx, dy, (0,0,0,0))


def draw_buttons(t):
    p = PAPER[t]
    c = Canvas(BTN_SM_W * 3, BTN_H)
    for i, st in enumerate(['normal', 'hover', 'disabled']):
        _button(c, i * BTN_SM_W, BTN_SM_W, p, st)
    c.save(f"anim/terrarium_btn_sm_{t}.png")

    c2 = Canvas(BTN_LG_W * 3, BTN_H)
    for i, st in enumerate(['normal', 'hover', 'disabled']):
        _button(c2, i * BTN_LG_W, BTN_LG_W, p, st)
    return c2.save(f"anim/terrarium_btn_lg_{t}.png")


# ── 7. Trait icons ────────────────────────────────────────────────────
def draw_traits(t):
    """height, bloom, vigor, hue, hardiness, rarity — 8x8 each."""
    p = PAPER[t]
    ink, ink_d = p['text'], p['text_d']
    c = Canvas(TRAIT_PX * 6, TRAIT_PX)

    # 0 height — upward arrow w/ baseline
    for y in range(2, 7): c.put(3, y, ink)
    for i in range(2): c.put(3 - 1 - i, 3 + i, ink_d); c.put(3 + 1 + i, 3 + i, ink_d)
    c.rect(1, 7, 6, 7, ink_d)
    # 1 bloom — five-petal flower
    o = 8
    for dx, dy in [(0,-2),(-2,-1),(2,-1),(-1,2),(1,2)]:
        c.put(o + 4 + dx, 4 + dy, ink)
    c.put(o + 4, 4, tint_ui(UI['gold'], t)); c.put(o + 3, 4, tint_ui(UI['gold_d'], t))
    # 2 vigor — lightning bolt
    o = 16
    for x, y in [(5,1),(4,2),(3,3),(5,3),(4,4),(3,5),(2,6)]:
        c.put(o + x, y, tint_ui(UI['gold'], t))
    for x, y in [(4,1),(2,3),(2,5)]:
        c.put(o + x, y, tint_ui(UI['gold_d'], t))
    # 3 hue — droplet / palette blob
    o = 24
    for y in range(2, 7):
        hw = min(3, y - 1)
        for x in range(4 - hw, 4 + hw):
            c.put(o + x, y, tint_ui(UI['water'], t))
    c.put(o + 4, 1, tint_ui(UI['water_hi'], t)); c.put(o + 3, 3, tint_ui(UI['water_hi'], t))
    # 4 hardiness — shield
    o = 32
    for y in range(1, 5):
        for x in range(1, 7): c.put(o + x, y, ink_d)
    for y in range(5, 8):
        hw = 3 - (y - 5)
        for x in range(4 - hw, 4 + hw + 1): c.put(o + x, y, ink_d)
    c.put(o + 3, 3, ink); c.put(o + 4, 3, ink); c.put(o + 3, 4, ink)
    # 5 rarity — star
    o = 40
    for x, y in [(4,1),(3,3),(5,3),(2,4),(6,4),(3,5),(5,5),(2,7),(6,7),(4,6)]:
        c.put(o + x, y, tint_ui(UI['gold'], t))
    c.put(o + 4, 2, tint_ui(UI['gold'], t))
    return c.save(f"anim/terrarium_traits_{t}.png")


def draw_stars(t):
    p = PAPER[t]
    c = Canvas(STAR_PX * 2, STAR_PX)
    pts = [(3,0),(2,2),(0,2),(1,4),(0,6),(3,5),(6,6),(5,4),(6,2),(4,2)]
    body = [(3,1),(2,3),(3,3),(4,3),(3,4),(2,4),(4,4)]
    for i, col in enumerate([p['slot_d'], tint_ui(UI['gold'], t)]):
        o = i * STAR_PX
        for x, y in pts: c.put(o + x, y, col)
        for x, y in body: c.put(o + x, y, col if i else p['slot_d'])
        if i:
            c.put(o + 3, 2, tint_ui(UI['gold_d'], t))
    return c.save(f"anim/terrarium_stars_{t}.png")


# ── 8. Zoomed pot cross-section ───────────────────────────────────────
TERRA = {
    'day':       dict(light=(196,128,88), mid=(168,100,64), dark=(132,76,48),
                      rim=(208,144,100), edge=(104,64,40),
                      soil_dry=(96,72,48), soil_mid=(68,52,36), soil_wet=(52,40,30),
                      soil_top=(126,98,66)),
    'morning':   dict(light=(192,120,80), mid=(164,94,58), dark=(128,72,44),
                      rim=(204,136,92), edge=(100,60,38),
                      soil_dry=(92,66,44), soil_mid=(64,48,34), soil_wet=(48,36,28),
                      soil_top=(120,90,60)),
    'afternoon': dict(light=(200,132,86), mid=(172,104,62), dark=(136,80,46),
                      rim=(212,148,98), edge=(108,68,38),
                      soil_dry=(100,74,46), soil_mid=(70,54,34), soil_wet=(54,42,28),
                      soil_top=(130,102,64)),
    'night':     dict(light=(58,42,48), mid=(42,32,38), dark=(30,22,28),
                      rim=(66,50,56), edge=(20,16,22),
                      soil_dry=(28,24,30), soil_mid=(20,18,24), soil_wet=(14,14,20),
                      soil_top=(42,36,44)),
}


# Pot geometry — shared by both halves so they register exactly.
# The pot is split at the rim so the plant can grow OUT of the opening:
# back half (rim far edge + inner wall + soil) is drawn behind the plant,
# front half (rim near face + body + saucer) is drawn in front of it.
POT_CX      = POTPANEL_W // 2     # 24
OPEN_CY     = 14                  # centre row of the elliptical mouth
RX_OUT, RY_OUT = 22, 7            # rim outer ellipse
RX_IN,  RY_IN  = 18, 5            # opening (inner) ellipse
RIM_DY      = 6                   # draw ring rows dy -6..6  -> y 8..20
IN_DY       = 4                   # inner ellipse rows -4..4 -> y 10..18
SOIL_LINE   = OPEN_CY + 1         # 15 — plant anchors here, front-of-centre
BODY_TOP    = OPEN_CY             # body starts at the ellipse's widest row
BODY_BOT    = 33
BASE_BOT    = 36


def ehw(rx, ry, dy):
    """Half-width of an ellipse at vertical offset dy. -1 when outside."""
    if abs(dy) > ry:
        return -1
    return int(round(rx * math.sqrt(max(0.0, 1.0 - (dy / ry) ** 2))))


def body_hw(ny):
    """Pot body half-width, tapering from the rim's widest row to the base."""
    tt = (ny - BODY_TOP) / (BODY_BOT - BODY_TOP)
    return int(round(RX_OUT - tt * 7))


def _rim_ring(c, tp, dy_from, dy_to, oy=0):
    """Draw the elliptical rim ring for rows dy_from..dy_to (relative to the
    opening centre). The ring is everything inside the outer ellipse and
    outside the opening."""
    cx = POT_CX
    for dy in range(dy_from, dy_to + 1):
        ny = OPEN_CY + dy + oy
        ho = ehw(RX_OUT, RY_OUT, dy)
        if ho < 0:
            continue
        hi = ehw(RX_IN, RY_IN, dy) if abs(dy) <= IN_DY else -1
        for nx in range(-ho, ho + 1):
            if hi >= 0 and abs(nx) <= hi:
                continue                       # that's the opening
            x = cx + nx
            # The near arc sits ON the body, so it must not draw its own
            # silhouette outline — the body's edge already defines it, and
            # outlining here reads as a jagged seam across the shoulder.
            outer_edge = abs(nx) >= ho - 1 and dy <= 0
            if outer_edge:
                c.put(x, ny, tp['edge'])
            elif dy <= -RY_OUT + 2:
                c.put(x, ny, tp['rim'])        # far arc, full light
            elif dy < 0:
                c.put(x, ny, tp['rim'] if nx < 0 else tp['light'])
            elif dy == 0:
                c.put(x, ny, tp['light'] if nx < 0 else tp['mid'])
            elif dy == 1:
                c.put(x, ny, tp['rim'] if nx < 0 else tp['light'])
            elif dy >= RY_OUT - 2:
                c.put(x, ny, tp['dark'])       # underside of the lip
            else:
                c.put(x, ny, tp['light'] if nx < 0 else tp['mid'])
            # inner wall just inside the opening reads as shadow
            if hi >= 0 and abs(nx) == hi + 1 and dy <= 0:
                c.put(x, ny, tp['edge'])


WET_STATES = ('dry', 'moist', 'wet')
WET_SCALE = {'dry': 1.24, 'moist': 1.0, 'wet': 0.72}


def soil_ramp(tp, state):
    """Shift the whole soil ramp by wetness. Watering has to be visible in
    the pot itself, not just in a meter, or the can feels inert."""
    k = WET_SCALE[state]
    return {key: tuple(_c(v * k) for v in tp[key])
            for key in ('soil_wet', 'soil_mid', 'soil_dry', 'soil_top')}


def _pot_back_pane(c, tp, oy, state):
    cx = POT_CX
    _rim_ring(c, tp, -RIM_DY, 0, oy)
    sr = soil_ramp(tp, state)
    # Soil — fills the opening ellipse. Light comes from the front, so the bed
    # is brightest at the near edge and falls into shadow under the back rim.
    for dy in range(-IN_DY, IN_DY + 1):
        ny = OPEN_CY + dy + oy
        hi = ehw(RX_IN, RY_IN, dy)
        if hi < 0:
            continue
        for nx in range(-hi, hi + 1):
            x = cx + nx
            speck = ((nx * 7 + (ny - oy) * 13) % 11) < 2
            rim_shadow = abs(nx) >= hi - 1          # soil meeting the wall
            if dy <= -IN_DY + 1 or rim_shadow:
                c.put(x, ny, sr['soil_wet'])        # under the back rim
            elif dy <= -1:
                c.put(x, ny, sr['soil_mid'] if speck else sr['soil_wet'])
            elif dy == 0:
                c.put(x, ny, sr['soil_dry'] if speck else sr['soil_mid'])
            elif dy == 1:
                c.put(x, ny, sr['soil_mid'] if speck else sr['soil_dry'])
            else:
                c.put(x, ny, sr['soil_dry'] if speck else sr['soil_top'])


def draw_pot_back(t):
    """Behind the plant: the rim's far arc and the soil bed, at three wetness
    levels stacked vertically (dry / moist / wet)."""
    tp = TERRA[t]
    c = Canvas(POTPANEL_W, POTPANEL_H * len(WET_STATES))
    for i, state in enumerate(WET_STATES):
        _pot_back_pane(c, tp, i * POTPANEL_H, state)
    return c.save(f"anim/terrarium_pot_back_{t}.png")


def draw_pot_glow(t):
    """Drop-target highlight: the mouth ellipse traced in a warm outline,
    drawn over pot_back while a tool hovers the pot."""
    p = PAPER[t]
    c = Canvas(POTPANEL_W, POTPANEL_H)
    cx = POT_CX
    glow = tint_ui((255, 236, 170), t) if t != 'night' else (150, 134, 92)
    for dy in range(-RY_OUT, RY_OUT + 1):
        ho = ehw(RX_OUT, RY_OUT, dy)
        if ho < 1:
            continue
        ny = OPEN_CY + dy
        for nx in (-ho, -ho + 1, ho - 1, ho):
            c.put(cx + nx, ny, glow)
    for dy in (-RY_OUT, RY_OUT):
        ho = ehw(RX_OUT, RY_OUT, dy)
        for nx in range(-ho, ho + 1):
            c.put(cx + nx, OPEN_CY + dy, glow)
    return c.save(f"anim/terrarium_pot_glow_{t}.png")


def draw_pot_front(t):
    """In front of the plant: the rim's near arc, the body, base and saucer."""
    tp = TERRA[t]
    c = Canvas(POTPANEL_W, POTPANEL_H)
    cx = POT_CX

    # Body first — the opening is a hole punched through it, so skip any pixel
    # that falls inside the mouth ellipse.
    for ny in range(BODY_TOP, BODY_BOT + 1):
        hw = body_hw(ny)
        dy = ny - OPEN_CY
        hi = ehw(RX_IN, RY_IN, dy) if abs(dy) <= IN_DY else -1
        for nx in range(-hw, hw + 1):
            if hi >= 0 and abs(nx) <= hi:
                continue
            x = cx + nx
            if abs(nx) >= hw:
                c.put(x, ny, tp['edge'])
                continue
            f = (nx + hw) / (2 * hw)               # 0 left .. 1 right
            dith = (nx + ny) % 3 == 0
            if f < 0.28:    c.put(x, ny, tp['light'] if (nx + ny) % 4 else tp['mid'])
            elif f < 0.42:  c.put(x, ny, tp['mid'] if dith else tp['light'])
            elif f < 0.62:  c.put(x, ny, tp['mid'])
            elif f < 0.78:  c.put(x, ny, tp['dark'] if dith else tp['mid'])
            else:           c.put(x, ny, tp['dark'])

    # Near arc of the rim, over the body — this is the lip that the plant
    # stands behind.
    _rim_ring(c, tp, 1, RIM_DY)

    # Base ring
    for ny in range(BODY_BOT + 1, BASE_BOT + 1):
        hw = 15
        for nx in range(-hw, hw + 1):
            c.put(cx + nx, ny, tp['dark'] if ny == BASE_BOT else tp['edge'])

    # Saucer — a shallow ellipse of its own
    sc_rows = POTPANEL_H - BASE_BOT - 1
    for i in range(sc_rows):
        ny = BASE_BOT + 1 + i
        hw = ehw(21, sc_rows + 1, i - 1)
        if hw < 0:
            continue
        for nx in range(-hw, hw + 1):
            x = cx + nx
            if i == sc_rows - 1 or abs(nx) >= hw - 1:
                c.put(x, ny, tp['edge'])
            else:
                c.put(x, ny, tp['mid'] if nx < 0 else tp['dark'])
    return c.save(f"anim/terrarium_pot_front_{t}.png")


def draw_pot_panel(t):
    draw_pot_back(t)
    return draw_pot_front(t)


# ── 9. Font sheet ─────────────────────────────────────────────────────
def draw_font_sheet():
    """One white sheet, tinted in JS. Cell is 4x6, glyph index == position
    of the character in pixfont.CHARSET."""
    cs = pixfont.CHARSET
    c = Canvas(len(cs) * pixfont.CELL_W, pixfont.CELL_H)
    for i, ch in enumerate(cs):
        pixfont.draw(lambda x, y, col: c.put(x, y, col),
                     ch, i * pixfont.CELL_W, 0, (255, 255, 255))
    c.save("anim/terrarium_font.png")
    return cs


# ── Generate ──────────────────────────────────────────────────────────
print("Terrarium Field Journal — generating assets\n")
cs = draw_font_sheet()
print(f"  font sheet  {len(cs)} glyphs, cell {pixfont.CELL_W}x{pixfont.CELL_H}, "
      f"advance {pixfont.ADVANCE}px")
for label in ["Water", "Trim", "Harvest", "Plant", "Clear", "CROSS"]:
    box = BTN_LG_W if label == "CROSS" else BTN_SM_W
    ok = "fits" if pixfont.fits(label, box) else "OVERFLOW"
    print(f"    {label:<8} {pixfont.width(label):>3}px ink in {box}px button  {ok}")
print()
for t in TIMES:
    draw_journal(t); draw_tab_active(t); draw_tab_icons(t)
    draw_seeds(t);   draw_codex(t);      draw_slots(t)
    draw_meter(t);   draw_buttons(t);    draw_traits(t)
    draw_stars(t);   draw_pot_panel(t);  draw_pot_glow(t)
    print(f"  {t:<10} journal+tabs, seeds({NSPEC}), codex({NSPEC}), slots, meters, buttons, traits, stars, pot")

print(f"\n{len(TIMES) * 11} files written to anim/")
