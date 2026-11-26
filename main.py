#!/usr/bin/env python3
"""THE WORLD TODAY — Thursday 26 November 2026.

A one-page newspaper front page summing up 26 November 2026 world news,
drawn entirely with Python 3 standard library code: a hand-built 5x7
bitmap typeface, hand-built PNG encoder (zlib + CRC32), no network,
deterministic output (two runs are byte-identical).

Usage:
    python3 main.py            # writes /output/entry.png
    MAKEFUN_OUTPUT_DIR=out python3 main.py   # writes out/entry.png
"""

import os
import struct
import zlib
from math import sqrt

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER   = (0xFB, 0xF3, 0xDC)   # warm newsprint
INK     = (0x1B, 0x1B, 0x1B)   # near-black body text
NAVY    = (0x16, 0x22, 0x4E)   # masthead / sport band / footer
NAVY_LT = (0x2A, 0x3A, 0x6E)   # lighter navy for rules inside bands
SLATE   = (0x9A, 0xA0, 0xC0)   # pale slate text on navy
RED     = (0xB3, 0x27, 0x1E)   # lead red
GOLD    = (0xC9, 0xA2, 0x27)   # masthead accent
GOLD_LT = (0xE8, 0xC8, 0x4A)   # pale gold text on navy
GREY    = (0x6E, 0x6A, 0x5E)   # muted grey text
TEAL    = (0x0F, 0x7A, 0x6E)   # europe accent
ORANGE  = (0xD9, 0x6A, 0x1E)   # india accent
WHITE   = (0xFF, 0xFF, 0xFF)
BLUE    = (0x1F, 0x5F, 0xB0)   # globe blue
GREEN   = (0x1E, 0x8A, 0x3C)   # globe green / india green
SAFFRON = (0xF0, 0x93, 0x1B)   # india saffron
PINK    = (0xF2, 0xD8, 0xD8)   # futures strip background

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is blank.
# Written from scratch for this page.
FONT = {
    'A': ("..#..",
          ".#.#.",
          "#...#",
          "#...#",
          "#####",
          "#...#",
          "#...#"),
    'B': ("####.",
          "#...#",
          "#...#",
          "####.",
          "#...#",
          "#...#",
          "####."),
    'C': (".####",
          "#....",
          "#....",
          "#....",
          "#....",
          "#....",
          ".####"),
    'D': ("####.",
          "#...#",
          "#...#",
          "#...#",
          "#...#",
          "#...#",
          "####."),
    'E': ("#####",
          "#....",
          "#....",
          "####.",
          "#....",
          "#....",
          "#####"),
    'F': ("#####",
          "#....",
          "#....",
          "####.",
          "#....",
          "#....",
          "#...."),
    'G': (".####",
          "#....",
          "#....",
          "#.###",
          "#...#",
          "#...#",
          ".###."),
    'H': ("#...#",
          "#...#",
          "#...#",
          "#####",
          "#...#",
          "#...#",
          "#...#"),
    'I': ("#####",
          "..#..",
          "..#..",
          "..#..",
          "..#..",
          "..#..",
          "#####"),
    'J': ("..###",
          "...#.",
          "...#.",
          "...#.",
          "...#.",
          "#..#.",
          ".##.."),
    'K': ("#...#",
          "#..#.",
          "#.#..",
          "##...",
          "#.#..",
          "#..#.",
          "#...#"),
    'L': ("#....",
          "#....",
          "#....",
          "#....",
          "#....",
          "#....",
          "#####"),
    'M': ("#...#",
          "##.##",
          "#.#.#",
          "#.#.#",
          "#...#",
          "#...#",
          "#...#"),
}

FONT.update({
    'N': ("#...#",
          "##..#",
          "#.#.#",
          "#..##",
          "#...#",
          "#...#",
          "#...#"),
    'O': (".###.",
          "#...#",
          "#...#",
          "#...#",
          "#...#",
          "#...#",
          ".###."),
    'P': ("####.",
          "#...#",
          "#...#",
          "####.",
          "#....",
          "#....",
          "#...."),
    'Q': (".###.",
          "#...#",
          "#...#",
          "#...#",
          "#.#.#",
          "#..#.",
          ".##.#"),
    'R': ("####.",
          "#...#",
          "#...#",
          "####.",
          "#.#..",
          "#..#.",
          "#...#"),
    'S': (".####",
          "#....",
          "#....",
          ".###.",
          "....#",
          "....#",
          "####."),
    'T': ("#####",
          "..#..",
          "..#..",
          "..#..",
          "..#..",
          "..#..",
          "..#.."),
    'U': ("#...#",
          "#...#",
          "#...#",
          "#...#",
          "#...#",
          "#...#",
          ".###."),
    'V': ("#...#",
          "#...#",
          "#...#",
          "#...#",
          "#...#",
          ".#.#.",
          "..#.."),
    'W': ("#...#",
          "#...#",
          "#...#",
          "#.#.#",
          "#.#.#",
          "##.##",
          "#...#"),
    'X': ("#...#",
          "#...#",
          ".#.#.",
          "..#..",
          ".#.#.",
          "#...#",
          "#...#"),
    'Y': ("#...#",
          "#...#",
          ".#.#.",
          "..#..",
          "..#..",
          "..#..",
          "..#.."),
    'Z': ("#####",
          "....#",
          "...#.",
          "..#..",
          ".#...",
          "#....",
          "#####"),
    '0': (".###.",
          "#...#",
          "#..##",
          "#.#.#",
          "##..#",
          "#...#",
          ".###."),
    '1': ("..#..",
          ".##..",
          "..#..",
          "..#..",
          "..#..",
          "..#..",
          ".###."),
    '2': (".###.",
          "#...#",
          "....#",
          "...#.",
          "..#..",
          ".#...",
          "#####"),
    '3': ("####.",
          "....#",
          "....#",
          ".###.",
          "....#",
          "....#",
          "####."),
    '4': ("...#.",
          "..##.",
          ".#.#.",
          "#..#.",
          "#####",
          "...#.",
          "...#."),
    '5': ("#####",
          "#....",
          "####.",
          "....#",
          "....#",
          "#...#",
          ".###."),
    '6': (".###.",
          "#....",
          "#....",
          "####.",
          "#...#",
          "#...#",
          ".###."),
    '7': ("#####",
          "....#",
          "...#.",
          "..#..",
          "..#..",
          "..#..",
          "..#.."),
    '8': (".###.",
          "#...#",
          "#...#",
          ".###.",
          "#...#",
          "#...#",
          ".###."),
    '9': (".###.",
          "#...#",
          "#...#",
          ".####",
          "....#",
          "....#",
          ".###."),
    ' ': (".....",
          ".....",
          ".....",
          ".....",
          ".....",
          ".....",
          "....."),
    '-': (".....",
          ".....",
          ".....",
          ".###.",
          ".....",
          ".....",
          "....."),
    '.': (".....",
          ".....",
          ".....",
          ".....",
          ".....",
          ".##..",
          ".##.."),
    ',': (".....",
          ".....",
          ".....",
          ".....",
          ".##..",
          ".##..",
          ".#..."),
    '%': ("#...#",
          "#..#.",
          "...#.",
          "..#..",
          ".#...",
          "#..#.",
          "#...#"),
    '$': ("..#..",
          ".####",
          "#.#.#",
          ".###.",
          "..#.#",
          "####.",
          "..#.."),
    '/': ("....#",
          "....#",
          "...#.",
          "..#..",
          ".#...",
          "#....",
          "#...."),
    ':': (".....",
          ".##..",
          ".##..",
          ".....",
          ".##..",
          ".##..",
          "....."),
    ';': (".....",
          ".##..",
          ".##..",
          ".....",
          ".##..",
          ".##..",
          ".#..."),
    '(': ("...#.",
          "..#..",
          ".#...",
          ".#...",
          ".#...",
          "..#..",
          "...#."),
    ')': (".#...",
          "..#..",
          "...#.",
          "...#.",
          "...#.",
          "..#..",
          ".#..."),
    '+': (".....",
          "..#..",
          "..#..",
          ".###.",
          "..#..",
          "..#..",
          "....."),
    '!': ("..#..",
          "..#..",
          "..#..",
          "..#..",
          "..#..",
          ".....",
          "..#.."),
    '?': (".###.",
          "#...#",
          "....#",
          "...#.",
          "..#..",
          ".....",
          "..#.."),
    '=': (".....",
          ".....",
          ".####",
          ".....",
          ".####",
          ".....",
          "....."),
    '&': (".##..",
          "#..#.",
          "#.#..",
          ".#...",
          "#.#.#",
          "#..#.",
          ".##.#"),
    "'": ("..#..",
          "..#..",
          ".#...",
          ".....",
          ".....",
          ".....",
          "....."),
})

# ------------------------------------------------------------------ canvas
class Page:
    """An RGB bitmap with drawing helpers."""

    def __init__(self):
        self.buf = bytearray(PAPER * (W * H))

    def put(self, x, y, colour):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.buf[i:i + 3] = bytes(colour)

    def rect(self, x, y, w, h, colour):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        row = bytes(colour) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * W + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x, y, w, colour, thick=1):
        self.rect(x, y, w, thick, colour)

    def vline(self, x, y, h, colour, thick=1):
        self.rect(x, y, thick, h, colour)

    def line(self, x0, y0, x1, y1, colour):
        """Bresenham line."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.put(x0, y0, colour)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, colour):
        """Filled disc."""
        for dy in range(-r, r + 1):
            half = int(sqrt(r * r - dy * dy))
            self.rect(cx - half, cy + dy, 2 * half + 1, 1, colour)

    def ring(self, cx, cy, r, colour, thick=2):
        self.disc(cx, cy, r, colour)
        self.disc(cx, cy, r - thick, PAPER)

    def triangle(self, x, y, w, h, colour):
        """Right-pointing filled triangle with tip at (x+w, y+h//2)."""
        for i in range(w):
            span = int(h * (i + 1) / w)
            self.rect(x + i, y + (h - span) // 2, 1, span, colour)

# -------------------------------------------------------------------- text
def char_w(scale):
    return 6 * scale


def text_w(text, scale):
    return len(text) * char_w(scale) - scale if text else 0


def draw_glyph(page, x, y, ch, scale, colour):
    glyph = FONT.get(ch.upper(), FONT['?'])
    for row_i, row in enumerate(glyph):
        for col_i, cell in enumerate(row):
            if cell == '#':
                page.rect(x + col_i * scale, y + row_i * scale,
                          scale, scale, colour)


def draw_text(page, x, y, text, scale, colour):
    cx = x
    for ch in text:
        draw_glyph(page, cx, y, ch, scale, colour)
        cx += char_w(scale)
    return cx


def draw_centred(page, cx, y, text, scale, colour):
    draw_text(page, cx - text_w(text, scale) // 2, y, text, scale, colour)


def wrap_lines(text, scale, max_w):
    """Greedy word wrap; returns a list of lines."""
    lines = []
    for chunk in text.split('\n'):
        words = chunk.split()
        cur = ''
        for word in words:
            trial = word if not cur else cur + ' ' + word
            if text_w(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


def draw_para(page, x, y, text, scale, colour, max_w, leading=None):
    """Draw a wrapped paragraph; returns the y below the last line."""
    if leading is None:
        leading = 7 * scale + 4
    for line in wrap_lines(text, scale, max_w):
        draw_text(page, x, y, line, scale, colour)
        y += leading
    return y


def kicker(page, x, y, label, colour):
    """Small section label with a solid square bullet."""
    page.rect(x, y + 2, 10, 10, colour)
    draw_text(page, x + 16, y, label, 2, colour)
    return y + 16


# -------------------------------------------------------------- PNG output
def _chunk(kind, data):
    body = kind + data
    return (struct.pack('>I', len(data)) + body +
            struct.pack('>I', zlib.crc32(body) & 0xFFFFFFFF))


def encode_png(page):
    ihdr = struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = W * 3
    for yy in range(H):
        raw.append(0)  # filter: none
        raw += page.buf[yy * stride:(yy + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    return (b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', ihdr) +
            _chunk(b'IDAT', idat) + _chunk(b'IEND', b''))


# ------------------------------------------------------------- chart block
def draw_falling_chart(page, x, y, w, h):
    """Lead chart: a steeply falling line with % axis labels."""
    page.rect(x, y, w, h, WHITE)
    page.rect(x, y, w, 2, INK)
    page.rect(x, y, 2, h, INK)
    # axis labels and gridlines: 0% at top, -3% mid, -6% bottom
    top = y + 14
    mid = y + h // 2
    bot = y + h - 22
    for label, yy in (("0%", top), ("-3%", mid), ("-6%", bot)):
        draw_text(page, x + 6, yy - 7, label, 1, GREY)
        page.hline(x + 34, yy, w - 40, (0xD8, 0xD2, 0xC2))
    # falling polyline through five points
    xs = [x + 44, x + 44 + (w - 90) // 4, x + 44 + (w - 90) // 2,
          x + 44 + 3 * (w - 90) // 4, x + w - 34]
    ys = [top + 6, top + 26, mid + 4, bot - 22, bot - 4]
    for i in range(len(xs) - 1):
        page.line(xs[i], ys[i], xs[i + 1], ys[i + 1], RED)
        page.line(xs[i], ys[i] + 1, xs[i + 1], ys[i + 1] + 1, RED)
    for px, py in zip(xs, ys):
        page.disc(px, py, 4, RED)
        page.disc(px, py, 2, WHITE)
    # arrowhead at the end of the fall
    page.triangle(xs[-1] - 2, ys[-1] - 12, 20, 24, RED)
    # legend
    draw_text(page, x + 6, y + h - 40, "NIKKEI -3%", 2, BLUE)
    draw_text(page, x + 6, y + h - 20, "KOSPI -6%", 2, RED)
    # futures strip
    page.rect(x, y + h + 6, w, 22, PINK)
    draw_centred(page, x + w // 2, y + h + 11, "US FUTURES SLIDE", 1, RED)


# -------------------------------------------------------------- masthead
def draw_masthead(page):
    page.rect(0, 0, W, 108, NAVY)
    draw_text(page, 24, 22, "THE WORLD TODAY", 5, WHITE)
    draw_text(page, 24, 70, "ONE DAY - ONE PAGE - THE NEWS THAT MATTERED",
              2, GOLD_LT)
    # right-hand date block, right-aligned to x=1000
    draw_text(page, 1000 - text_w("THURSDAY", 4), 20, "THURSDAY", 4, WHITE)
    draw_text(page, 1000 - text_w("26 NOVEMBER 2026", 4), 52,
              "26 NOVEMBER 2026", 4, GOLD_LT)
    draw_text(page, 1000 - text_w("WORLD NEWS IN ONE IMAGE", 2), 84,
              "WORLD NEWS IN ONE IMAGE", 2, SLATE)
    page.rect(0, 108, W, 4, GOLD)


# -------------------------------------------------------------- top row
def draw_lead(page):
    x, y = 24, 126
    kicker(page, x, y, "LEAD - MARKETS", RED)
    draw_text(page, x, y + 26, "TARIFF SHOCK SINKS", 4, RED)
    draw_text(page, x, y + 58, "ASIAN MARKETS", 4, RED)
    chart_x, chart_y = x, y + 104
    draw_falling_chart(page, chart_x, chart_y, 212, 190)
    body_x = x + 228
    body_w = 600 - body_x
    end = draw_para(
        page, body_x, chart_y,
        "THE US UNVEILS A NEW TARIFF PLAN AIMED AT FACTORY "
        "OVERCAPACITY IN 16 TRADING PARTNERS. SEOUL FALLS 6%, "
        "TOKYO 3%, AND US FUTURES SLIDE AS INVESTORS BRACE FOR "
        "HIGHER PRICES AND A SLOWER ECONOMY.",
        2, INK, body_w)
    draw_para(
        page, body_x, end + 10,
        "THE PLAN LANDS DAYS AFTER A DEMOCRATIC MIDTERM WIN AND "
        "JUST BEFORE THANKSGIVING.",
        2, INK, body_w)


def draw_space_europe(page):
    x, y = 624, 126
    col_w = 1000 - x
    kicker(page, x, y, "SPACE - CHINA", RED)
    draw_text(page, x, y + 26, "FIRST PAKISTANI IN", 3, INK)
    draw_text(page, x, y + 50, "ORBIT", 3, INK)
    draw_para(
        page, x, y + 82,
        "SHENZHOU-24 DOCKS AT TIANGONG. ZEESHAN ALI IS THE FIRST "
        "FOREIGN VISITOR TO CHINA'S STATION.",
        2, INK, col_w)
    page.hline(x, y + 176, col_w, TEAL, 3)
    kicker(page, x, y + 188, "EUROPE - BRUSSELS", TEAL)
    draw_text(page, x, y + 214, "EU LEADERS MEET IN", 3, INK)
    draw_text(page, x, y + 238, "BRUSSELS", 3, INK)
    draw_para(
        page, x, y + 270,
        "A EURO SUMMIT AND A SPECIAL EUROPEAN COUNCIL OPEN IN "
        "BRUSSELS, WITH TRADE AND DEFENCE ON THE AGENDA.",
        2, INK, col_w)


# ------------------------------------------------------------ middle row
def draw_peace(page):
    x, y = 24, 532
    col_w = 312
    page.hline(x, y - 8, col_w, GOLD, 3)
    kicker(page, x, y, "PEACE - COLOMBIA", GOLD)
    draw_text(page, x, y + 26, "10 YEARS OF", 3, INK)
    draw_text(page, x, y + 50, "PEACE", 3, INK)
    draw_para(
        page, x, y + 82,
        "COLOMBIA MARKS A DECADE SINCE ITS HISTORIC PEACE ACCORD. "
        "THE UN CHIEF PRAISES PROGRESS BUT WARNS OF UNFINISHED "
        "COMMITMENTS.",
        2, INK, col_w)
    # anniversary badge: gold disc with a big 10, beside the headline
    page.disc(x + 262, y + 40, 26, GOLD)
    page.disc(x + 262, y + 40, 22, NAVY)
    draw_text(page, x + 244, y + 28, "10", 3, GOLD_LT)


def draw_india(page):
    x, y = 352, 532
    col_w = 312
    page.hline(x, y - 8, col_w, ORANGE, 3)
    kicker(page, x, y, "INDIA - CONSTITUTION DAY", ORANGE)
    draw_text(page, x, y + 26, "INDIA MARKS", 3, INK)
    draw_text(page, x, y + 50, "CONSTITUTION DAY", 3, INK)
    draw_para(
        page, x, y + 82,
        "NOVEMBER 26 IS SAMVIDHAN DIVAS. IITS WILL ADD 6,000 "
        "SEATS IN ROBOTICS, AI AND SPACE TECHNOLOGY FROM 2027.",
        2, INK, col_w)
    # tricolour bars
    bar_y = y + 178
    page.rect(x, bar_y, 150, 10, SAFFRON)
    page.rect(x, bar_y + 10, 150, 10, WHITE)
    page.rect(x, bar_y + 20, 150, 10, GREEN)
    page.disc(x + 75, bar_y + 15, 6, NAVY)


def draw_venezuela(page):
    x, y = 680, 532
    col_w = 320
    page.hline(x, y - 8, col_w, RED, 3)
    kicker(page, x, y, "ECONOMY - VENEZUELA", RED)
    draw_text(page, x, y + 26, "VENEZUELA", 3, INK)
    draw_text(page, x, y + 50, "REVEALS", 3, INK)
    draw_text(page, x, y + 74, "$237.5BN DEBT", 3, INK)
    draw_para(
        page, x, y + 106,
        "THE GOVERNMENT PUTS PUBLIC DEBT AT $237.5 BILLION AS IT "
        "PREPARES A HISTORIC ECONOMIC RESTRUCTURE.",
        2, INK, col_w)
    # globe: blue disc with green land and white grid, clear of the body
    cx, cy = x + 282, y + 200
    page.disc(cx, cy, 30, BLUE)
    page.disc(cx - 10, cy - 8, 10, GREEN)
    page.disc(cx + 12, cy + 10, 8, GREEN)
    page.vline(cx, cy - 30, 60, WHITE)
    page.hline(cx - 30, cy, 60, WHITE)


# -------------------------------------------------------------- sport band
def draw_sport(page):
    y = 772
    page.rect(0, y, W, 96, NAVY)
    draw_text(page, 24, y + 12, "SPORT", 2, GOLD_LT)
    draw_text(page, 24, y + 36, "REAL MADRID 5-1 PSV", 3, WHITE)
    draw_text(page, 24, y + 66, "BELLINGHAM STUNNER, MBAPPE BRACE", 2, WHITE)
    page.vline(512, y + 12, 72, NAVY_LT, 2)
    draw_text(page, 536, y + 12, "CRICKET", 2, GOLD_LT)
    draw_text(page, 536, y + 36, "IPL AUCTION DRAWS 1,220", 3, WHITE)
    draw_text(page, 536, y + 66, "GUKESH IN WORLD CHESS TITLE FIGHT", 2, WHITE)


# -------------------------------------------------------------- also today
def draw_also_today(page):
    y = 884
    draw_text(page, 24, y, "ALSO TODAY", 3, RED)
    page.hline(24, y + 28, 976, INK, 2)
    left = [
        ("1.", "MUMBAI MARKS 18 YEARS SINCE THE 26/11 ATTACKS."),
        ("3.", "NORTH KOREA ORDERS SWITZERLAND TO CLOSE ITS "
              "PYONGYANG OFFICE."),
    ]
    right = [
        ("2.", "BANGLADESH RAISES GARMENT WORKERS MINIMUM WAGE "
              "BY 36%."),
        ("4.", "SHEIKH HASINA SEEKS RETURN TO BANGLADESH ON "
              "DECEMBER 16."),
    ]
    for col_x, items in ((24, left), (524, right)):
        yy = y + 40
        for num, text in items:
            draw_text(page, col_x, yy, num, 2, RED)
            draw_para(page, col_x + 28, yy, text, 2, INK, 448, leading=16)
            yy += 34


# ------------------------------------------------------------------ footer
def draw_footer(page):
    page.rect(0, 990, W, 34, NAVY)
    page.rect(0, 990, W, 3, GOLD)
    draw_centred(
        page, W // 2, 1002,
        "THURSDAY 26 NOVEMBER 2026 - AS REPORTED BY REUTERS, "
        "XINHUA AND OTHERS",
        2, WHITE)


# -------------------------------------------------------------------- main
def build_page():
    page = Page()
    draw_masthead(page)
    draw_lead(page)
    draw_space_europe(page)
    page.hline(24, 520, 976, INK, 2)
    draw_peace(page)
    draw_india(page)
    draw_venezuela(page)
    draw_sport(page)
    draw_also_today(page)
    draw_footer(page)
    return page


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(build_page())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
