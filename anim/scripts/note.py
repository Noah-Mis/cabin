"""
Sasquatch-hand note delivery — v3.
  • Arm reaches from BEHIND the left window frame (drawn BEFORE cabin_window).
  • Note is larger (22×14) with visible text lines, wax seal, dog-ear, shadow.
  • Opened note is proportionally bigger so the "envelope" doesn't look tiny.

Assets:
  anim/note_deliver_<time>.png  — 14 frames, 120×50, 120ms, plays once
  anim/note_sill_<time>.png     — static 24×16 folded note
  anim/note_open_<time>.png     — 7 frames, 26×30, 110ms, note unfolding
"""

from PIL import Image, ImageDraw
import math, random

W_CANVAS, H_CANVAS = 320, 180

# ── Palettes ──────────────────────────────────────────────────────────
FUR = {
    'day':       dict(main=(88,60,42), dark=(44,30,24), light=(128,92,62), hi=(156,118,90), outline=(30,18,10)),
    'morning':   dict(main=(88,50,36), dark=(44,25,21), light=(128,77,54), hi=(156,99,79),  outline=(30,14,8)),
    'afternoon': dict(main=(91,57,33), dark=(45,28,19), light=(133,87,49), hi=(162,112,72),  outline=(30,16,8)),
    'night':     dict(main=(29,24,26), dark=(14,12,14), light=(43,36,38),  hi=(53,47,55),    outline=(6,4,6)),
}

PAPER = {
    'day':       dict(light=(250,244,228), mid=(238,230,208), dark=(210,198,172), line=(138,120,90),
                      fold=(216,204,178), edge=(184,172,146), accent=(180,168,140),
                      seal=(172,52,44), seal_d=(124,36,28), seal_hi=(200,80,68)),
    'morning':   dict(light=(252,238,214), mid=(242,226,200), dark=(214,194,164), line=(142,124,94),
                      fold=(220,202,172), edge=(188,172,144), accent=(184,168,140),
                      seal=(176,56,42), seal_d=(128,38,28), seal_hi=(204,82,64)),
    'afternoon': dict(light=(254,246,220), mid=(244,234,204), dark=(216,202,168), line=(144,128,96),
                      fold=(222,206,174), edge=(190,176,148), accent=(186,172,144),
                      seal=(178,54,40), seal_d=(130,36,26), seal_hi=(206,80,62)),
    'night':     dict(light=(136,144,166), mid=(118,126,150), dark=(78,86,110),   line=(52,58,82),
                      fold=(98,104,130), edge=(68,74,98), accent=(80,86,108),
                      seal=(126,46,56), seal_d=(88,32,42), seal_hi=(156,68,78)),
}

# ── NOTE dimensions ───────────────────────────────────────────────────
NOTE_W, NOTE_H = 22, 14      # folded note size (larger)

def draw_note(im, ox, oy, pp, w=NOTE_W, h=NOTE_H, detail=True):
    """Draw a detailed folded note/letter. Origin = top-left."""
    px = im.load()
    def put(x, y, c):
        ix, iy = int(ox + x), int(oy + y)
        if 0 <= ix < im.width and 0 <= iy < im.height:
            px[ix, iy] = c + (255,)

    # Drop shadow
    for nx in range(2, w + 1):
        put(nx, h, pp['edge'])
        put(nx, h + 1, pp['edge'])
    for ny in range(2, h + 1):
        put(w, ny, pp['edge'])
        put(w + 1, ny, pp['edge'])
    put(w, h, pp['edge'])

    # Main body
    for ny in range(h):
        for nx in range(w):
            # Border
            if ny == 0 or ny == h - 1 or nx == 0 or nx == w - 1:
                put(nx, ny, pp['dark'])
                continue

            # Dog-ear top-right
            if ny == 0 and nx >= w - 3:
                put(nx, ny, pp['fold'])
                continue
            if ny == 1 and nx >= w - 2:
                put(nx, ny, pp['fold'])
                continue
            if ny == 2 and nx == w - 2:
                put(nx, ny, pp['accent'])
                continue

            # Fold line across middle
            if ny == h // 2:
                put(nx, ny, pp['fold'])
                continue
            # Shadow just below fold
            if ny == h // 2 + 1 and nx > 1:
                put(nx, ny, pp['mid'] if nx % 2 == 0 else pp['light'])
                continue

            # Paper texture
            if (nx * 7 + ny * 13) % 11 == 0:
                put(nx, ny, pp['mid'])
            else:
                put(nx, ny, pp['light'])

    if detail:
        # ── "Text" lines on upper half (above fold) ──
        # Line 1 (header-ish, shorter)
        for nx in range(3, w - 6):
            if nx % 2 == 0:
                put(nx, 2, pp['line'])
        # Line 2
        for nx in range(2, w - 3):
            if nx % 2 == 0 or nx % 5 == 0:
                put(nx, 3, pp['line'])
        # Line 3
        for nx in range(2, w - 4):
            if nx % 2 == 0:
                put(nx, 4, pp['line'])
        # Line 4 (partial)
        for nx in range(2, w - 8):
            if nx % 2 == 0 or nx == 3:
                put(nx, 5, pp['line'])

        # ── "Text" lines on lower half (below fold) ──
        for nx in range(2, w - 3):
            if nx % 2 == 0 or nx % 3 == 0:
                put(nx, h // 2 + 3, pp['line'])
        for nx in range(2, w - 5):
            if nx % 2 == 0:
                put(nx, h // 2 + 4, pp['line'])
        # Short last line
        for nx in range(2, w - 10):
            if nx % 2 == 0:
                put(nx, h // 2 + 5, pp['line'])

        # ── Wax seal (bottom-right, 4×4 circle-ish) ──
        sx, sy = w - 6, h - 5
        #   .XX.
        #   XXXX
        #   XXHX
        #   .XX.
        put(sx + 1, sy, pp['seal']); put(sx + 2, sy, pp['seal'])
        put(sx, sy + 1, pp['seal']); put(sx + 1, sy + 1, pp['seal_hi'])
        put(sx + 2, sy + 1, pp['seal']); put(sx + 3, sy + 1, pp['seal'])
        put(sx, sy + 2, pp['seal']); put(sx + 1, sy + 2, pp['seal'])
        put(sx + 2, sy + 2, pp['seal_d']); put(sx + 3, sy + 2, pp['seal'])
        put(sx + 1, sy + 3, pp['seal_d']); put(sx + 2, sy + 3, pp['seal_d'])

        # Dog-ear triangle fill
        put(w - 3, 1, pp['fold']); put(w - 2, 1, pp['accent'])
        put(w - 2, 2, pp['fold'])


# ── Sasquatch arm reaching from left ─────────────────────────────────
def draw_arm(im, arm_end_x, arm_y, pal, holding_note=True,
             fingers_open=0, paper_pal=None):
    """
    Chunky pixel-art sasquatch arm + paw. Matches the blocky style of
    bg.py pine trees and sasquatch_peek sprites. Drawn BEFORE cabin_window.
    """
    px = im.load()
    def put(x, y, c):
        ix, iy = int(x), int(y)
        if 0 <= ix < im.width and 0 <= iy < im.height:
            px[ix, iy] = c + (255,)

    M, D, L, H, O = pal['main'], pal['dark'], pal['light'], pal['hi'], pal['outline']
    rng = random.Random(77)

    # ── Forearm — thick, blocky, extends from left ──
    arm_half = 5  # half-thickness (total ~11px tall)
    arm_start = -10
    hx = int(arm_end_x)
    hy = int(arm_y)

    for x in range(arm_start, hx - 2):
        for dy in range(-arm_half, arm_half + 1):
            y = hy + dy
            if abs(dy) == arm_half:
                put(x, y, O)                           # outline edge
            elif abs(dy) == arm_half - 1:
                put(x, y, D if dy > 0 else L)          # shadow bottom / lit top
            else:
                # Fur texture: chunky dither, not smooth
                if (x + dy * 3) % 5 == 0:
                    put(x, y, L)
                elif (x * 2 + dy) % 7 == 0:
                    put(x, y, H)
                else:
                    put(x, y, M)

        # Sparse fur tufts (1px pokes) — irregular silhouette
        if rng.random() < 0.4:
            put(x, hy - arm_half - 1, D if rng.random() < 0.7 else L)
        if rng.random() < 0.3:
            put(x, hy + arm_half + 1, D)

    # ── Paw — blocky mitt shape, not individual fingers ──
    # The paw is a rounded rectangle wider than the arm
    paw_w = 8 + fingers_open          # wider when opening
    paw_h = 12 + fingers_open         # taller when opening
    paw_top = hy - paw_h // 2
    paw_left = hx - 3

    for dx in range(paw_w):
        for dy in range(paw_h):
            px_x = paw_left + dx
            px_y = paw_top + dy

            # Rounded corners (skip corner pixels)
            corner = False
            if (dx == 0 or dx == paw_w - 1) and (dy == 0 or dy == paw_h - 1):
                corner = True
            if corner:
                continue

            # Edge = outline
            if dx == 0 or dx == paw_w - 1 or dy == 0 or dy == paw_h - 1:
                put(px_x, px_y, O)
            # Top row inside = highlight (lit from above)
            elif dy <= 2:
                put(px_x, px_y, L if (dx + dy) % 3 != 0 else H)
            # Bottom rows = shadow
            elif dy >= paw_h - 3:
                put(px_x, px_y, D if (dx + dy) % 3 != 0 else M)
            # Middle = main fur with texture
            else:
                if (dx * 3 + dy * 5) % 7 == 0:
                    put(px_x, px_y, L)
                elif (dx + dy * 2) % 5 == 0:
                    put(px_x, px_y, H)
                else:
                    put(px_x, px_y, M)

    # Knuckle bumps on right edge — 3 subtle nubs
    for nub_dy in [-3, 0, 3]:
        ny = hy + nub_dy
        nx = paw_left + paw_w
        put(nx, ny, O)
        put(nx, ny - 1, D)

    # Thumb nub below the paw
    tx, ty = paw_left + paw_w - 3, paw_top + paw_h
    put(tx, ty, O); put(tx + 1, ty, O); put(tx + 2, ty, O)
    put(tx, ty + 1, O); put(tx + 1, ty + 1, M); put(tx + 2, ty + 1, O)
    put(tx + 1, ty + 2, O)

    # Fur tufts on wrist area
    for tuft_y in range(hy - arm_half, hy + arm_half + 1, 2):
        if rng.random() < 0.5:
            put(hx - 4, tuft_y, D)

    # ── Note held in paw ──
    if holding_note and paper_pal:
        # Note sits just to the right of the paw
        note_x = paw_left + paw_w - 2
        note_y = hy - NOTE_H // 2
        draw_note(im, note_x, note_y, paper_pal)


# ── Generate static note on sill ──────────────────────────────────────
for time in ('morning', 'day', 'afternoon', 'night'):
    pp = PAPER[time]
    im = Image.new('RGBA', (NOTE_W + 3, NOTE_H + 3), (0, 0, 0, 0))
    draw_note(im, 0, 0, pp)
    im.save(f'/tmp/cabin/anim/note_sill_{time}.png')
    print(f'note_sill_{time}: {im.size}')


# ── Delivery animation ───────────────────────────────────────────────
FRAME_W, FRAME_H = 120, 70
N_FRAMES = 16

# Placement on canvas:
# Window opening: roughly x=40..280, y=24..131. Sill top: y≈132.
# Frame placed so the arm is in the upper-middle of the window opening,
# clearly visible, and the bottom of the frame reaches the sill for the note drop.
PLACE_X = 18   # frame origin X on canvas
PLACE_Y = 86   # frame origin Y → arm at canvas y≈86+18=104 (mid-window)

# Arm center Y in frame coords — high enough to be clearly visible
ARM_Y = 18

# Note final rest position in frame coords
# Canvas sill target: ~(74, 140) → frame coords: (74-18, 140-86) = (56, 54)
NOTE_REST_FX = 56
NOTE_REST_FY = 54

# Keyframes: arm reaches in, note drops to sill, arm retreats
#   (frame, arm_reach_x, arm_dy, fopen, holding)
#   arm_dy = vertical offset from ARM_Y (for the "drop" motion)
KEYS = [
    #     arm_x, arm_dy, fopen, holding
    (0,   -10,   0,      0,     True),    # off-screen
    (1,    4,    0,      0,     True),    # fingertips peeking in
    (2,   18,    0,      0,     True),    # hand entering
    (3,   32,    0,      0,     True),    # arm extending
    (4,   44,    0,      0,     True),    # nearly there
    (5,   52,    0,      0,     True),    # at position
    (6,   56,    0,      0,     True),    # slight overshoot
    (7,   54,    2,      0,     True),    # settle + dip toward sill
    (8,   54,    6,      0,     True),    # lowering hand toward sill
    (9,   54,   12,      0,     True),    # hand near sill level
    (10,  54,   18,      1,     True),    # fingers begin open at sill
    (11,  54,   18,      2,     False),   # release note onto sill
    (12,  50,   10,      2,     False),   # pulling back + up
    (13,  36,    2,      1,     False),   # retreating
    (14,  14,    0,      0,     False),   # mostly gone
    (15,  -8,    0,      0,     False),   # gone
]

for time in ('morning', 'day', 'afternoon', 'night'):
    fur = FUR[time]
    pp = PAPER[time]
    sheet = Image.new('RGBA', (FRAME_W * N_FRAMES, FRAME_H), (0, 0, 0, 0))

    for fi, (_, reach, arm_dy, fopen, holding) in enumerate(KEYS):
        frame = Image.new('RGBA', (FRAME_W, FRAME_H), (0, 0, 0, 0))

        if reach > -8:
            draw_arm(frame, reach, ARM_Y + arm_dy, fur,
                     holding_note=holding, fingers_open=fopen,
                     paper_pal=pp if holding else None)

        # Released note stays at rest position (on the sill)
        if not holding:
            draw_note(frame, NOTE_REST_FX - NOTE_W // 2,
                      NOTE_REST_FY - NOTE_H // 2, pp)

        sheet.paste(frame, (fi * FRAME_W, 0))

    sheet.save(f'/tmp/cabin/anim/note_deliver_{time}.png')
    print(f'note_deliver_{time}: {sheet.size}')


# ── Note open animation ──────────────────────────────────────────────
# Simple unfold: the folded note is the same size as note_sill.
# It opens by the top half lifting up (hinged at the fold line) to
# reveal text underneath. The flap stays CONNECTED to the body at the fold.
# Final frame = fully open letter, same width, double height.

NOPEN_W = NOTE_W + 4       # padding for shadow
NOPEN_H = NOTE_H * 2 + 4   # full open height + padding
NOPEN_FRAMES = 6

for time in ('morning', 'day', 'afternoon', 'night'):
    pp = PAPER[time]
    sheet = Image.new('RGBA', (NOPEN_W * NOPEN_FRAMES, NOPEN_H), (0, 0, 0, 0))

    for fi in range(NOPEN_FRAMES):
        frame = Image.new('RGBA', (NOPEN_W, NOPEN_H), (0, 0, 0, 0))
        px = frame.load()
        def put(x, y, c):
            if 0 <= x < NOPEN_W and 0 <= y < NOPEN_H:
                px[x, y] = c + (255,)

        ox = 1   # left margin
        fold_y = NOPEN_H - NOTE_H // 2 - 2  # fold line stays fixed (bottom half anchor)
        bottom_top = fold_y                   # bottom half starts at fold line
        bottom_h = NOTE_H // 2               # bottom half height

        if fi == 0:
            # Fully folded — just draw the folded note at the bottom
            draw_note(frame, ox, fold_y - NOTE_H // 2, pp)
        else:
            progress = fi / (NOPEN_FRAMES - 1)  # 0→1

            # How much the top flap has opened (0 = folded flat, 1 = fully open upward)
            # The top flap "unfolds" upward from the fold line
            flap_open = min(1.0, progress)
            top_h = max(1, int(NOTE_H // 2 * flap_open))  # visible height of top section
            top_top = fold_y - top_h  # top of the unfolding flap

            # ── Bottom half (always visible, has text) ──
            for ny in range(bottom_h + 1):
                for nx in range(NOTE_W + 1):
                    x, y = ox + nx, bottom_top + ny
                    if ny == bottom_h or nx == 0 or nx == NOTE_W:
                        put(x, y, pp['dark'])
                    elif ny == 0:
                        put(x, y, pp['fold'])  # fold line
                    elif (nx * 7 + ny * 13) % 11 == 0:
                        put(x, y, pp['mid'])
                    else:
                        put(x, y, pp['light'])

            # Text on bottom half
            for row in range(2, bottom_h):
                indent = 1
                end_m = 2 if row < bottom_h - 1 else 8
                for nx in range(indent, NOTE_W - end_m):
                    if nx % 2 == 0 or (nx % 3 == 0 and row % 2 == 0):
                        put(ox + nx, bottom_top + row, pp['line'])

            # Wax seal on bottom half
            if bottom_h >= 5:
                sx, sy = ox + NOTE_W - 6, bottom_top + bottom_h - 4
                put(sx+1,sy,pp['seal']); put(sx+2,sy,pp['seal'])
                put(sx,sy+1,pp['seal']); put(sx+1,sy+1,pp['seal_hi'])
                put(sx+2,sy+1,pp['seal']); put(sx+3,sy+1,pp['seal'])
                put(sx,sy+2,pp['seal']); put(sx+1,sy+2,pp['seal'])
                put(sx+2,sy+2,pp['seal_d']); put(sx+3,sy+2,pp['seal'])
                put(sx+1,sy+3,pp['seal_d']); put(sx+2,sy+3,pp['seal_d'])

            # Shadow under bottom
            for nx in range(2, NOTE_W + 2):
                put(ox + nx, bottom_top + bottom_h + 1, pp['edge'])

            # ── Top flap (unfolds upward from fold line) ──
            if top_h >= 1:
                for ny in range(top_h + 1):
                    for nx in range(NOTE_W + 1):
                        x, y = ox + nx, top_top + ny
                        if ny == 0 or nx == 0 or nx == NOTE_W:
                            put(x, y, pp['dark'])
                        elif ny == top_h:
                            put(x, y, pp['fold'])  # fold line connects to bottom
                        else:
                            # Slightly different shade for flap (back of paper)
                            if (nx + ny) % 5 == 0:
                                put(x, y, pp['fold'])
                            elif (nx * 3 + ny * 7) % 9 == 0:
                                put(x, y, pp['mid'])
                            else:
                                put(x, y, pp['light'])

                # Text visible on flap once mostly open
                if flap_open > 0.5:
                    for row in range(1, min(top_h, NOTE_H // 2)):
                        indent = 3 if row == 1 else 1
                        for nx in range(indent, NOTE_W - 2):
                            if nx % 2 == 0:
                                put(ox + nx, top_top + row, pp['line'])

                # Dog-ear on top-right corner
                if top_h > 2:
                    put(ox + NOTE_W - 1, top_top + 1, pp['fold'])
                    put(ox + NOTE_W - 2, top_top, pp['fold'])

        sheet.paste(frame, (fi * NOPEN_W, 0))

    sheet.save(f'/tmp/cabin/anim/note_open_{time}.png')
    print(f'note_open_{time}: {sheet.size}')


# ── Previews ──────────────────────────────────────────────────────────
print("\nPreviews...")
try:
    bg = Image.open('/tmp/cabin/bg_day.png').convert('RGBA')
    win = Image.open('/tmp/cabin/cabin_window.png').convert('RGBA')
    deliver = Image.open('/tmp/cabin/anim/note_deliver_day.png')

    # Key: draw the arm BEFORE the window, so the frame covers the entry point
    show_frames = [2, 5, 8, 10, 12, 14]
    scale = 4
    crop_x, crop_y, crop_w, crop_h = 10, 70, 140, 95

    cols = len(show_frames)
    pw = crop_w * scale * cols + (cols - 1) * 2
    ph = crop_h * scale
    preview = Image.new('RGB', (pw, ph), (20, 20, 24))
    d = ImageDraw.Draw(preview)

    for i, fi in enumerate(show_frames):
        scene = bg.copy()
        # Draw arm BEFORE window!
        f = deliver.crop((fi * FRAME_W, 0, (fi + 1) * FRAME_W, FRAME_H))
        scene.alpha_composite(f, (PLACE_X, PLACE_Y))
        # Window on top — covers the arm where it enters
        scene.alpha_composite(win)

        crop = scene.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
        scaled = crop.resize((crop_w * scale, crop_h * scale), Image.NEAREST)
        x_off = i * (crop_w * scale + 2)
        preview.paste(scaled, (x_off, 0))
        d.text((x_off + 4, 4), f'F{fi}', fill=(255, 255, 0))

    preview.save('/tmp/cabin/note_preview_anim.png')
    print(f'Anim preview: {preview.size}')

    # Static note on sill zoomed
    scene2 = bg.copy()
    scene2.alpha_composite(win)
    note_img = Image.open('/tmp/cabin/anim/note_sill_day.png')
    # Place note: anchor (11,13) at canvas (74,148)
    scene2.alpha_composite(note_img, (63, 135))
    crop2 = scene2.crop((45, 118, 130, 162))
    z2 = crop2.resize((crop2.width * 6, crop2.height * 6), Image.NEAREST)
    z2.save('/tmp/cabin/note_preview_sill.png')
    print(f'Sill preview: {z2.size}')

    # Note open strip zoomed
    nopen = Image.open('/tmp/cabin/anim/note_open_day.png')
    z3 = nopen.resize((nopen.width * 5, nopen.height * 5), Image.NEAREST)
    z3.save('/tmp/cabin/note_preview_open.png')
    print(f'Open preview: {z3.size}')

except Exception as e:
    import traceback; traceback.print_exc()

print("\nDone!")
