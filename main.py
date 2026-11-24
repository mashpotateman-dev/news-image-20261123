"""World news of 23 November 2026 as one newspaper front page.

Python 3.13, standard library only, no network, fully deterministic: every pixel is
drawn from shapes and a hand-made 5x7 bitmap font, then written as a PNG to
/output/entry.png (MAKEFUN_OUTPUT_DIR overrides the folder for local runs).
"""

import math
import os
import struct
import zlib

W = H = 1024          # final image size
SS = 2                # supersampling factor for smooth edges
CW = W * SS           # canvas size
CH = H * SS

# ---------------------------------------------------------------- colours
PAPER = (246, 241, 226)
PANEL = (255, 253, 248)
INK = (17, 17, 17)
WHITE = (255, 255, 255)
GREEN = (38, 160, 58)
CRIMSON = (178, 22, 32)
NAVY = (16, 62, 122)
PURPLE = (86, 42, 134)
GOLD = (232, 178, 32)
STEEL = (92, 98, 110)
DARK = (38, 40, 46)
SEA = (28, 92, 168)
SEA_LIGHT = (120, 175, 225)
ORANGE = (248, 126, 20)
YELLOW = (255, 214, 40)
RED = (214, 30, 30)
SMOKE = (70, 70, 74)
LAND = (150, 196, 120)

# ---------------------------------------------------------------- font
# 5x7 bitmap glyphs, one string of 7 rows each ('#' = ink).
FONT_SRC = {
    'A': ".###. #...# #...# ##### #...# #...# #...#",
    'B': "####. #...# #...# ####. #...# #...# ####.",
    'C': ".###. #...# #.... #.... #.... #...# .###.",
    'D': "####. #...# #...# #...# #...# #...# ####.",
    'E': "##### #.... #.... ####. #.... #.... #####",
    'F': "##### #.... #.... ####. #.... #.... #....",
    'G': ".###. #...# #.... #.### #...# #...# .####",
    'H': "#...# #...# #...# ##### #...# #...# #...#",
    'I': ".###. ..#.. ..#.. ..#.. ..#.. ..#.. .###.",
    'J': "..### ...#. ...#. ...#. ...#. #..#. .##..",
    'K': "#...# #..#. #.#.. ##... #.#.. #..#. #...#",
    'L': "#.... #.... #.... #.... #.... #.... #####",
    'M': "#...# ##.## #.#.# #.#.# #...# #...# #...#",
    'N': "#...# #...# ##..# #.#.# #..## #...# #...#",
    'O': ".###. #...# #...# #...# #...# #...# .###.",
    'P': "####. #...# #...# ####. #.... #.... #....",
    'Q': ".###. #...# #...# #...# #.#.# #..#. .##.#",
    'R': "####. #...# #...# ####. #.#.. #..#. #...#",
    'S': ".#### #.... #.... .###. ....# ....# ####.",
    'T': "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    'U': "#...# #...# #...# #...# #...# #...# .###.",
    'V': "#...# #...# #...# #...# #...# .#.#. ..#..",
    'W': "#...# #...# #...# #.#.# #.#.# #.#.# .#.#.",
    'X': "#...# #...# .#.#. ..#.. .#.#. #...# #...#",
    'Y': "#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..",
    'Z': "##### ....# ...#. ..#.. .#... #.... #####",
    '0': ".###. #...# #..## #.#.# ##..# #...# .###.",
    '1': "..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.",
    '2': ".###. #...# ....# ...#. ..#.. .#... #####",
    '3': "####. ....# ....# .###. ....# ....# ####.",
    '4': "...#. ..##. .#.#. #..#. ##### ...#. ...#.",
    '5': "##### #.... ####. ....# ....# #...# .###.",
    '6': ".###. #.... #.... ####. #...# #...# .###.",
    '7': "##### ....# ...#. ..#.. .#... .#... .#...",
    '8': ".###. #...# #...# .###. #...# #...# .###.",
    '9': ".###. #...# #...# .#### ....# ....# .###.",
    ' ': "..... ..... ..... ..... ..... ..... .....",
    ',': "..... ..... ..... ..... .##.. ..#.. .#...",
    '.': "..... ..... ..... ..... ..... .##.. .##..",
    ';': "..... .##.. .##.. ..... .##.. ..#.. .#...",
    ':': "..... .##.. .##.. ..... .##.. .##.. .....",
    '%': "##..# ##..# ...#. ..#.. .#... #..## #..##",
    '+': "..... ..#.. ..#.. ##### ..#.. ..#.. .....",
    '-': "..... ..... ..... ##### ..... ..... .....",
    '/': "....# ....# ...#. ..#.. .#... #.... #....",
    '$': "..#.. .#### #.#.. .###. ..#.# ####. ..#..",
    "'": "..#.. ..#.. .#... ..... ..... ..... .....",
}
FONT = {ch: [row for row in src.split()] for ch, src in FONT_SRC.items()}


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, color):
        self.buf = bytearray(bytes(color) * (CW * CH))

    def span(self, j, x0, x1, color):
        """Fill canvas row j from canvas x0 (inclusive) to x1 (exclusive)."""
        if j < 0 or j >= CH:
            return
        x0 = max(0, x0)
        x1 = min(CW, x1)
        if x1 <= x0:
            return
        a = (j * CW + x0) * 3
        self.buf[a:a + (x1 - x0) * 3] = bytes(color) * (x1 - x0)

    def rect(self, x, y, w, h, color):
        x0 = round(x * SS)
        x1 = round((x + w) * SS)
        for j in range(round(y * SS), round((y + h) * SS)):
            self.span(j, x0, x1, color)

    def polygon(self, pts, color):
        sp = [(px * SS, py * SS) for px, py in pts]
        ys = [p[1] for p in sp]
        edges = list(zip(sp, sp[1:] + sp[:1]))
        for j in range(max(0, int(min(ys))), min(CH, int(math.ceil(max(ys))) + 1)):
            yc = j + 0.5
            xs = []
            for (x1, y1), (x2, y2) in edges:
                if (y1 <= yc < y2) or (y2 <= yc < y1):
                    xs.append(x1 + (yc - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.span(j, round(xs[k]), round(xs[k + 1]), color)

    def ellipse(self, cx, cy, rx, ry, color, inner=0.0):
        """Filled ellipse; with inner > 0 a ring of that thickness."""
        cx, cy, rx, ry, t = cx * SS, cy * SS, rx * SS, ry * SS, inner * SS
        for j in range(int(cy - ry) - 1, int(cy + ry) + 2):
            d = (j + 0.5 - cy) / ry
            if abs(d) >= 1:
                continue
            ho = rx * math.sqrt(1 - d * d)
            hi = -1.0
            if t > 0 and ry - t > 0:
                di = (j + 0.5 - cy) / (ry - t)
                if abs(di) < 1:
                    hi = (rx - t) * math.sqrt(1 - di * di)
            if hi < 0:
                self.span(j, round(cx - ho), round(cx + ho), color)
            else:
                self.span(j, round(cx - ho), round(cx - hi), color)
                self.span(j, round(cx + hi), round(cx + ho), color)

    def circle(self, cx, cy, r, color, inner=0.0):
        self.ellipse(cx, cy, r, r, color, inner)

    def line(self, x1, y1, x2, y2, width, color, caps=True):
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy) or 1.0
        ox, oy = -dy / n * width / 2, dx / n * width / 2
        self.polygon([(x1 + ox, y1 + oy), (x2 + ox, y2 + oy),
                      (x2 - ox, y2 - oy), (x1 - ox, y1 - oy)], color)
        if caps:
            self.circle(x1, y1, width / 2, color)
            self.circle(x2, y2, width / 2, color)

    def outline(self, pts, width, color):
        for a, b in zip(pts, pts[1:] + pts[:1]):
            self.line(a[0], a[1], b[0], b[1], width, color)

    def downsample(self):
        """Average SS x SS blocks into the final W x H RGB image."""
        out = bytearray(W * H * 3)
        rowlen = CW * 3
        for y in range(H):
            a = self.buf[2 * y * rowlen:(2 * y + 1) * rowlen]
            b = self.buf[(2 * y + 1) * rowlen:(2 * y + 2) * rowlen]
            s = [p + q for p, q in zip(a, b)]
            row = bytearray(W * 3)
            for c in range(3):
                row[c::3] = bytes((p + q + 2) >> 2 for p, q in zip(s[c::6], s[c + 3::6]))
            out[y * W * 3:(y + 1) * W * 3] = row
        return out


# ---------------------------------------------------------------- text
def text_width(text, s):
    return len(text) * 6 * s - s


def draw_text(cv, x, y, text, s, color, bold=True):
    """Draw text with the 5x7 font at pixel scale s; bold widens each stroke."""
    bw = s * (1.3 if bold else 1.0)
    for i, ch in enumerate(text.upper()):
        glyph = FONT.get(ch, FONT[' '])
        gx = x + i * 6 * s
        for r, row in enumerate(glyph):
            c = 0
            while c < 5:
                if row[c] == '#':
                    e = c
                    while e + 1 < 5 and row[e + 1] == '#':
                        e += 1
                    cv.rect(gx + c * s, y + r * s, (e - c) * s + bw, s, color)
                    c = e + 1
                else:
                    c += 1


def draw_text_centered(cv, cx, y, text, s, color, bold=True):
    draw_text(cv, cx - text_width(text, s) / 2, y, text, s, color, bold)


def wrap(text, max_chars):
    lines, cur = [], ""
    for word in text.upper().split():
        cand = word if not cur else cur + " " + word
        if len(cand) <= max_chars:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- helpers
def rotate(pts, cx, cy, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]


def flame(cv, x, base, w, h):
    """A three-layer flame standing on (x, base)."""
    for k, col in ((1.0, RED), (0.72, ORANGE), (0.42, YELLOW)):
        ww, hh = w * k, h * k
        cv.polygon([(x - ww / 2, base), (x - ww / 2.6, base - hh * 0.55), (x - ww / 6, base - hh * 0.45),
                    (x, base - hh), (x + ww / 5, base - hh * 0.5), (x + ww / 2.4, base - hh * 0.6),
                    (x + ww / 2, base)], col)


# ---------------------------------------------------------------- icons
# Each icon draws into a box (ox, oy) of 456 x 200 pixels.
def icon_chip(cv, ox, oy):
    cx, cy, half = ox + 150, oy + 102, 72
    for i in range(6):                                   # pins on all four sides
        p = cy - half + 14 + i * 23
        cv.rect(cx - half - 20, p, 22, 10, STEEL)
        cv.rect(cx + half - 2, p, 22, 10, STEEL)
        q = cx - half + 14 + i * 23
        cv.rect(q, cy - half - 20, 10, 22, STEEL)
        cv.rect(q, cy + half - 2, 10, 22, STEEL)
    cv.rect(cx - half, cy - half, 2 * half, 2 * half, DARK)
    cv.rect(cx - 44, cy - 44, 88, 88, (64, 68, 78))
    cv.rect(cx - 30, cy - 30, 60, 60, GREEN)
    cv.rect(cx - 18, cy - 18, 36, 36, (24, 110, 40))
    # big green up arrow with a black edge
    ax = ox + 360
    shaft = [(ax - 28, oy + 192), (ax + 28, oy + 192), (ax + 28, oy + 82), (ax - 28, oy + 82)]
    head = [(ax - 70, oy + 88), (ax, oy + 6), (ax + 70, oy + 88)]
    cv.outline(shaft, 8, INK)
    cv.outline(head, 8, INK)
    cv.polygon(shaft, GREEN)
    cv.polygon(head, GREEN)


def icon_bank(cv, ox, oy):
    c = (44, 50, 66)
    bx = ox + 20
    cv.polygon([(bx, oy + 66), (bx + 210, oy + 66), (bx + 105, oy + 10)], c)
    cv.polygon([(bx + 36, oy + 58), (bx + 174, oy + 58), (bx + 105, oy + 24)], PANEL)
    cv.circle(bx + 105, oy + 46, 9, GOLD)
    cv.rect(bx + 4, oy + 70, 202, 14, c)
    for i in range(4):
        cv.rect(bx + 22 + i * 46, oy + 90, 24, 72, c)
    cv.rect(bx - 4, oy + 166, 218, 13, c)
    cv.rect(bx - 14, oy + 183, 238, 14, c)
    # gold coin with a dollar sign
    cv.circle(ox + 312, oy + 58, 54, INK)
    cv.circle(ox + 312, oy + 58, 49, GOLD)
    cv.circle(ox + 312, oy + 58, 40, (200, 146, 20), inner=4)
    draw_text_centered(cv, ox + 312, oy + 58 - 28, "$", 8, INK)
    # broken chain: two links on each side of a red break
    gray = (96, 100, 108)
    cv.ellipse(ox + 254, oy + 164, 28, 16, gray, inner=9)
    cv.ellipse(ox + 292, oy + 164, 28, 16, gray, inner=9)
    cv.ellipse(ox + 384, oy + 164, 28, 16, gray, inner=9)
    cv.ellipse(ox + 422, oy + 164, 28, 16, gray, inner=9)
    cv.rect(ox + 314, oy + 142, 48, 46, PANEL)            # the gap
    for (x1, y1, x2, y2) in ((338, 134, 328, 152), (338, 194, 328, 176),
                             (324, 164, 310, 164), (352, 164, 366, 164),
                             (348, 138, 356, 150), (348, 190, 356, 178)):
        cv.line(ox + x1, oy + y1, ox + x2, oy + y2, 5, RED)


def icon_warship(cv, ox, oy):
    sea_top = oy + 134
    cv.rect(ox, sea_top, 456, 66, SEA)
    for i in range(7):                                    # wave crests
        wx = ox + 12 + i * 64
        cv.line(wx, sea_top + 22 + (i % 2) * 18, wx + 30, sea_top + 22 + (i % 2) * 18, 4, SEA_LIGHT)
    # smoke behind the ship
    for (sx, sy, r) in ((262, 46, 26), (292, 30, 30), (326, 22, 24), (238, 30, 18)):
        cv.circle(ox + sx, oy + sy, r, SMOKE)
    # the ship, listing to one side
    pc, py = ox + 200, oy + 140
    hull = [(ox + 40, oy + 112), (ox + 352, oy + 112), (ox + 328, oy + 152), (ox + 72, oy + 152)]
    deck1 = [(ox + 140, oy + 82), (ox + 250, oy + 82), (ox + 250, oy + 114), (ox + 140, oy + 114)]
    deck2 = [(ox + 168, oy + 58), (ox + 222, oy + 58), (ox + 222, oy + 84), (ox + 168, oy + 84)]
    gun = [(ox + 90, oy + 100), (ox + 120, oy + 100), (ox + 120, oy + 114), (ox + 90, oy + 114)]
    tilt = 7
    cv.polygon(rotate(hull, pc, py, tilt), STEEL)
    cv.polygon(rotate(deck1, pc, py, tilt), (120, 126, 138))
    cv.polygon(rotate(deck2, pc, py, tilt), (120, 126, 138))
    cv.polygon(rotate(gun, pc, py, tilt), DARK)
    (gx1, gy1), (gx2, gy2) = rotate([(ox + 92, oy + 104), (ox + 52, oy + 96)], pc, py, tilt)
    cv.line(gx1, gy1, gx2, gy2, 5, DARK)
    (mx1, my1), (mx2, my2) = rotate([(ox + 195, oy + 60), (ox + 195, oy + 22)], pc, py, tilt)
    cv.line(mx1, my1, mx2, my2, 5, DARK)
    cv.rect(ox, sea_top + 14, 456, 3, SEA)                # waterline over the hull bottom
    # flames on the ship and on the sea
    flame(cv, ox + 282, oy + 124, 70, 92)
    flame(cv, ox + 236, oy + 104, 44, 60)
    flame(cv, ox + 340, sea_top + 8, 44, 46)
    flame(cv, ox + 60, sea_top + 10, 34, 34)
    # sea drone racing in from the right, with its wake
    dx, dy = ox + 376, sea_top + 6
    for k in range(3):
        cv.line(dx + 46 + k * 8, dy - 6 + k * 8, dx + 62 + k * 8, dy - 6 + k * 8, 4, WHITE)
    cv.polygon([(dx - 26, dy), (dx + 2, dy - 12), (dx + 40, dy - 10), (dx + 40, dy + 10), (dx + 2, dy + 10)], DARK)
    cv.rect(dx + 8, dy - 18, 16, 8, DARK)
    # impact burst where it meets the hull
    bx, by = ox + 352, oy + 128
    star = []
    for k in range(16):
        r = 30 if k % 2 == 0 else 12
        a = math.radians(k * 22.5)
        star.append((bx + r * math.cos(a), by + r * math.sin(a)))
    cv.polygon(star, YELLOW)


# rough outline of Poland, x from west to east, y from north to south (0..1)
POLAND = [(0.04, 0.16), (0.20, 0.08), (0.36, 0.03), (0.48, 0.00), (0.56, 0.07), (0.66, 0.06),
          (0.84, 0.04), (0.93, 0.10), (0.95, 0.28), (0.98, 0.42), (0.92, 0.56), (1.00, 0.76),
          (0.92, 0.86), (0.86, 1.00), (0.72, 0.93), (0.56, 0.96), (0.44, 0.88), (0.32, 0.83),
          (0.22, 0.75), (0.10, 0.66), (0.06, 0.54), (0.02, 0.38), (0.00, 0.24)]


def icon_awacs(cv, ox, oy):
    mx, my, mw, mh = ox + 196, oy + 56, 250, 142
    pts = [(mx + u * mw, my + v * mh) for u, v in POLAND]
    cv.polygon(pts, LAND)
    cv.outline(pts, 5, (40, 80, 40))
    for (u, v) in ((0.80, 0.70), (0.66, 0.52), (0.86, 0.40)):   # missile impacts
        x, y = mx + u * mw, my + v * mh
        cv.line(x - 11, y - 11, x + 11, y + 11, 7, RED)
        cv.line(x - 11, y + 11, x + 11, y - 11, 7, RED)
    draw_text(cv, mx + 82, my + 104, "POLAND", 2.8, (30, 60, 30))
    # AWACS plane with its radar dome, flying over the map
    body = (205, 210, 220)
    edge = (40, 44, 56)
    px, py = ox + 180, oy + 92
    wing = [(px - 10, py - 6), (px + 40, py - 6), (px - 50, py + 66), (px - 82, py + 66)]
    wing_far = [(px - 4, py - 4), (px + 30, py - 4), (px - 32, py - 48), (px - 56, py - 48)]
    tail = [(px - 150, py - 4), (px - 118, py - 4), (px - 150, py - 52), (px - 172, py - 52)]
    tail_h = [(px - 160, py - 2), (px - 120, py - 2), (px - 150, py + 20), (px - 172, py + 20)]
    for poly in (wing_far, tail):
        cv.outline(poly, 6, edge)
        cv.polygon(poly, body)
    cv.ellipse(px, py, 172, 22, edge)
    cv.ellipse(px, py, 167, 17, body)
    cv.ellipse(px + 150, py - 4, 16, 9, edge)                       # cockpit
    for poly in (wing, tail_h):
        cv.outline(poly, 6, edge)
        cv.polygon(poly, body)
    for i in range(6):                                               # windows
        cv.circle(px + 40 + i * 18, py - 4, 3.5, edge)
    cv.rect(px - 52, py - 40, 8, 24, edge)                           # dome struts
    cv.rect(px - 22, py - 40, 8, 24, edge)
    cv.ellipse(px - 33, py - 46, 66, 14, edge)                       # rotodome
    cv.ellipse(px - 33, py - 46, 61, 9, (230, 232, 238))
    cv.rect(px - 92, py - 48, 118, 4, edge)
    # radar sweep arcs
    for r in (70, 92):
        a0, pts_arc = -60, []
        for k in range(13):
            a = math.radians(a0 + k * 10 - 90)
            pts_arc.append((px - 33 + r * math.cos(a), py - 46 + r * 0.45 * math.sin(a)))
        for a, b in zip(pts_arc, pts_arc[1:]):
            cv.line(a[0], a[1], b[0], b[1], 4, PURPLE, caps=False)


# ---------------------------------------------------------------- page
STORIES = [
    ("NVIDIA", GREEN, "HUANG IS BACK",
     "Nvidia reinstates Jensen Huang as CEO; shares jump about 31%", icon_chip),
    ("IRAN SANCTIONS", CRIMSON, "SHADOW BANKING HIT",
     "US Treasury sanctions 25+ Iranian exchange houses and front firms", icon_bank),
    ("LIBYA WARSHIP", NAVY, "WARSHIP SUNK IN LIBYA",
     "Ukraine says 7 sea drones sank the Russian corvette Merkury in Benghazi", icon_warship),
    ("NATO / POLAND", PURPLE, "AWACS TO POLAND",
     "NATO sends an AWACS early-warning plane after 3 Russian missiles fell in Poland", icon_awacs),
]


def draw_page():
    cv = Canvas(PAPER)
    # masthead
    cv.rect(24, 14, 976, 5, INK)
    draw_text_centered(cv, 512, 30, "NOVEMBER 23, 2026", 5, INK)
    cv.rect(24, 76, 976, 3, INK)
    draw_text_centered(cv, 512, 90, "WORLD NEWS IN ONE IMAGE", 7, INK)
    cv.rect(24, 150, 976, 7, INK)
    cv.rect(24, 161, 976, 2, INK)

    margin, gap, top, bottom = 20, 16, 176, 1008
    pw = (W - 2 * margin - gap) / 2
    ph = (bottom - top - gap) / 2
    inner = pw - 32
    title_s = min(4.6, min((inner + 1) / (6 * len(t) - 1) for _, _, t, _, _ in STORIES))
    cap_s = 3.0
    while True:                                          # one caption size for all, at most 3 lines
        per_line = int((inner + cap_s) // (6 * cap_s))
        if all(len(wrap(c, per_line)) <= 3 for _, _, _, c, _ in STORIES):
            break
        cap_s -= 0.1

    for i, (kicker, color, title, caption, icon) in enumerate(STORIES):
        px = margin + (i % 2) * (pw + gap)
        py = top + (i // 2) * (ph + gap)
        cv.rect(px, py, pw, ph, INK)
        cv.rect(px + 4, py + 4, pw - 8, ph - 8, PANEL)
        cv.rect(px + 4, py + 4, pw - 8, 40, color)
        draw_text(cv, px + 16, py + 13, kicker, 3.2, WHITE)
        draw_text(cv, px + 16, py + 56, title, title_s, INK)
        icon(cv, px + 14, py + 98)
        lines = wrap(caption, per_line)
        ly = py + ph - 14 - len(lines) * (7 * cap_s + 8) + 8
        for line in lines:
            draw_text(cv, px + 16, ly, line, cap_s, INK)
            ly += 7 * cap_s + 8
    return cv.downsample()


# ---------------------------------------------------------------- png
def png_bytes(rgb, w, h):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    stride = w * 3
    raw = b"".join(b"\x00" + bytes(rgb[y * stride:(y + 1) * stride]) for y in range(h))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(draw_page(), W, H)
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
