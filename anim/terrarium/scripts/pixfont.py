"""
3x5 pixel font for the cabin UI.

Glyph cell is 4x6 (3x5 ink + 1px right gap + 1px baseline gap).
Advance is 4px. Space is 4px. This is the metric the journal layout
is designed against — "Harvest" is 7 chars = 27px of ink.
"""

GLYPH_W, GLYPH_H = 3, 5
CELL_W, CELL_H = 4, 6
ADVANCE = 4

F = {
    ' ': "...|...|...|...|...",
    'A': ".#.|#.#|###|#.#|#.#",
    'B': "##.|#.#|##.|#.#|##.",
    'C': ".##|#..|#..|#..|.##",
    'D': "##.|#.#|#.#|#.#|##.",
    'E': "###|#..|##.|#..|###",
    'F': "###|#..|##.|#..|#..",
    'G': ".##|#..|#.#|#.#|.##",
    'H': "#.#|#.#|###|#.#|#.#",
    'I': "###|.#.|.#.|.#.|###",
    'J': "..#|..#|..#|#.#|.#.",
    'K': "#.#|#.#|##.|#.#|#.#",
    'L': "#..|#..|#..|#..|###",
    'M': "#.#|###|###|#.#|#.#",
    'N': "#.#|##.|###|.##|#.#",
    'O': ".#.|#.#|#.#|#.#|.#.",
    'P': "##.|#.#|##.|#..|#..",
    'Q': ".#.|#.#|#.#|##.|.##",
    'R': "##.|#.#|##.|#.#|#.#",
    'S': ".##|#..|.#.|..#|##.",
    'T': "###|.#.|.#.|.#.|.#.",
    'U': "#.#|#.#|#.#|#.#|###",
    'V': "#.#|#.#|#.#|.#.|.#.",
    'W': "#.#|#.#|###|###|#.#",
    'X': "#.#|#.#|.#.|#.#|#.#",
    'Y': "#.#|#.#|.#.|.#.|.#.",
    'Z': "###|..#|.#.|#..|###",
    '0': "###|#.#|#.#|#.#|###",
    '1': ".#.|##.|.#.|.#.|###",
    '2': "##.|..#|.#.|#..|###",
    '3': "##.|..#|.#.|..#|##.",
    '4': "#.#|#.#|###|..#|..#",
    '5': "###|#..|##.|..#|##.",
    '6': ".##|#..|###|#.#|###",
    '7': "###|..#|.#.|.#.|.#.",
    '8': "###|#.#|###|#.#|###",
    '9': "###|#.#|###|..#|##.",
    '.': "...|...|...|...|.#.",
    ',': "...|...|...|.#.|#..",
    '-': "...|...|###|...|...",
    '_': "...|...|...|...|###",
    '/': "..#|..#|.#.|#..|#..",
    '%': "#.#|..#|.#.|#..|#.#",
    '!': ".#.|.#.|.#.|...|.#.",
    '?': "##.|..#|.#.|...|.#.",
    ':': "...|.#.|...|.#.|...",
    '+': "...|.#.|###|.#.|...",
    '>': "#..|.#.|..#|.#.|#..",
    '<': "..#|.#.|#..|.#.|..#",
    '(': "..#|.#.|.#.|.#.|..#",
    ')': "#..|.#.|.#.|.#.|#..",
    '*': "#.#|.#.|###|.#.|#.#",
    "'": ".#.|.#.|...|...|...",
}

CHARSET = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,-_/%!?:+><()*'"


def rows(ch):
    """Return the 5 row-strings for a character (uppercased, fallback space)."""
    return F.get(ch.upper(), F[' ']).split('|')


def width(s):
    """Ink width of a string in pixels (no trailing gap)."""
    return max(0, len(s) * ADVANCE - 1)


def draw(put, s, ox, oy, color):
    """Blit string s at (ox, oy). `put(x, y, color)` does the pixel write."""
    for i, ch in enumerate(s):
        gx = ox + i * ADVANCE
        for ry, row in enumerate(rows(ch)):
            for rx, bit in enumerate(row):
                if bit == '#':
                    put(gx + rx, oy + ry, color)


def draw_centered(put, s, cx, oy, color):
    """Blit centred on cx."""
    draw(put, s, cx - width(s) // 2, oy, color)


def fits(s, box_w, pad=3):
    """Does s fit inside box_w with pad on each side?"""
    return width(s) + pad * 2 <= box_w
