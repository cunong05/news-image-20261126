#!/usr/bin/env python3
"""news-image-20261126 -- one image summing up Thursday 26 November 2026.

Pure Python standard library. Renders a one-page newspaper front page
(1024x1024) with a hand-built 5x7 bitmap typeface and a hand-built PNG
writer (zlib + CRC32, no timestamps anywhere), so running it twice writes
byte-identical files. No network, no files read besides this script.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   (default output: /output)
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (250, 247, 238)
INK = (18, 20, 28)
NAVY = (13, 32, 66)
NAVY2 = (24, 52, 96)
RED = (178, 34, 34)
GOLD = (201, 162, 39)
TEAL = (14, 110, 105)
SKY = (125, 178, 214)
SEA = (46, 111, 164)
GREEN = (52, 130, 72)
GREY = (88, 90, 96)
LIGHT = (233, 229, 219)
WHITE = (255, 255, 255)
CREAM = (255, 251, 235)
ORANGE = (214, 96, 20)
SAFFRON = (255, 153, 51)

# ------------------------------------------------- 5x7 typeface, 35 bits
# One string of 35 bits per glyph, row-major, 5 bits per row, 7 rows.
GLYPHS = {
    "A": "01110100011000111111100011000110001",
    "B": "11110100011000111110100011000111110",
    "C": "01110100011000010000100001000101110",
    "D": "11110100011000110001100011000111110",
    "E": "11111100001000011110100001000011111",
    "F": "11111100001000011110100001000010000",
    "G": "01110100011000010111100011000101111",
    "H": "10001100011000111111100011000110001",
    "I": "01110001000010000100001000010001110",
    "J": "00111000100001000010000101001001100",
    "K": "10001100101010011000101001001010001",
    "L": "10000100001000010000100001000011111",
    "M": "10001110111010110101100011000110001",
    "N": "10001110011010110011100011000110001",
    "O": "01110100011000110001100011000101110",
    "P": "11110100011000111110100001000010000",
    "Q": "01110100011000110001101011001001101",
    "R": "11110100011000111110101001001010001",
    "S": "01111100001000001110000010000111110",
    "T": "11111001000010000100001000010000100",
    "U": "10001100011000110001100011000101110",
    "V": "10001100011000110001100010101000100",
    "W": "10001100011000110101101011101110001",
    "X": "10001100010101000100010101000110001",
    "Y": "10001100010101000100001000010000100",
    "Z": "11111000010001000100010001000011111",
    "0": "01110100011001110101110011000101110",
    "1": "00100011000010000100001000010001110",
    "2": "01110100010000100110010001000011111",
    "3": "11110000010000101110000010000111110",
    "4": "00010001100101010010111110001000010",
    "5": "11111100001111000001000011000101110",
    "6": "00110010001000011110100011000101110",
    "7": "11111000010001000100010000100001000",
    "8": "01110100011000101110100011000101110",
    "9": "01110100011000101111000010001001100",
    " ": "00000000000000000000000000000000000",
    ".": "00000000000000000000000000110001100",
    ",": "00000000000000000000011000010001000",
    "-": "00000000000000001110000000000000000",
    "'": "00100001000100000000000000000000000",
    "/": "00001000100001000100010001000010000",
    "(": "00010001000100001000010000010000010",
    ")": "01000001000001000010000100010001000",
    "%": "11001110100001000100010000101110011",
    "$": "00100011111010001110001011111000100",
    "&": "01100100101010001000101011001001101",
    "!": "00100001000010000100001000000000100",
    "?": "01110100010000100110001000000000100",
    "+": "00000001000010011111001000010000000",
    "=": "00000000001111100000111110000000000",
    ":": "00000011000000001100011000000000000",
    ";": "00000011000000001100011000010001000",
    '"': "01010010100101000000000000000000000",
    "*": "00000101010111010101000000000000000",
    "<": "00010001000100010000010000010000010",
    ">": "01000001000001000001000100010001000",
}


def glyph_rows(ch):
    bits = GLYPHS.get(ch, GLYPHS["?"])
    return [bits[i * 5:(i + 1) * 5] for i in range(7)]


def measure(text, scale):
    return len(text) * 6 * scale - scale


def wrap_words(text, max_chars):
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------- page
class Page:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bg * (w * h))

    def put(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def box(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            self.buf[base:base + (x1 - x0) * 3] = bytes(color) * (x1 - x0)

    def hbar(self, x, y, w, color, thick=1):
        self.box(x, y, w, thick, color)

    def vbar(self, x, y, h, color, thick=1):
        self.box(x, y, thick, h, color)

    def disc(self, cx, cy, r, color):
        for yy in range(-r, r + 1):
            dx = int((r * r - yy * yy) ** 0.5)
            for xx in range(-dx, dx + 1):
                self.put(cx + xx, cy + yy, color)

    def ring(self, cx, cy, r, color, thick=3):
        for yy in range(-r - 1, r + 2):
            for xx in range(-r - 1, r + 2):
                d = (xx * xx + yy * yy) ** 0.5
                if r - thick <= d <= r:
                    self.put(cx + xx, cy + yy, color)

    def tri(self, x, y, w, h, color):
        for yy in range(h):
            span = int(w * (yy + 1) / h)
            x0 = x + (w - span) // 2
            self.box(x0, y + yy, span, 1, color)

    def draw_text(self, x, y, s, scale, color):
        cx = x
        for ch in s.upper():
            for row in range(7):
                bits = glyph_rows(ch)[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.box(cx + col * scale, y + row * scale,
                                 scale, scale, color)
            cx += 6 * scale
        return cx

    def draw_centred(self, cx, y, s, scale, color):
        self.draw_text(cx - measure(s, scale) // 2, y, s, scale, color)

    def headline(self, x, y, w, title, scale, color=INK):
        chars = max(6, w // (6 * scale))
        yy = y
        for line in wrap_words(title, chars):
            self.draw_text(x, yy, line, scale, color)
            yy += 7 * scale + 4
        return yy

    def body(self, x, y, s, scale, color, max_chars, leading):
        yy = y
        for line in wrap_words(s, max_chars):
            self.draw_text(x, yy, line, scale, color)
            yy += leading
        return yy


# -------------------------------------------------------------- pictograms
def draw_falling_chart(pg, x, y, w, h):
    """Share-price chart falling off a cliff, with a red arrow."""
    pg.box(x, y, w, h, WHITE)
    pg.box(x, y, w, 3, INK)
    # grid
    for gy in range(1, 4):
        pg.hbar(x + 8, y + gy * h // 4, w - 16, (220, 222, 226), 1)
    # descending line: five segments, steeper each time
    pts = [(x + 10, y + 18), (x + w // 3, y + 34),
           (x + 2 * w // 3, y + 52), (x + w - 26, y + h - 26)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        steps = max(abs(bx - ax), abs(by - ay), 1)
        for i in range(steps + 1):
            px = ax + (bx - ax) * i // steps
            py = ay + (by - ay) * i // steps
            pg.box(px - 2, py - 2, 5, 5, RED)
    # arrowhead at the end
    ex, ey = pts[-1]
    pg.tri(ex - 4, ey + 2, 22, 16, RED)
    # small bars at the bottom
    for i, bh in enumerate((14, 22, 10, 26)):
        pg.box(x + 14 + i * 18, y + h - 8 - bh, 10, bh, NAVY2)


def draw_ten_badge(pg, cx, cy, r):
    pg.disc(cx, cy, r, GOLD)
    pg.ring(cx, cy, r, NAVY, 3)
    pg.draw_centred(cx, cy - 11, "10", 3, NAVY)


def draw_tricolour(pg, x, y, w, h):
    pg.box(x, y, w, h // 3, SAFFRON)
    pg.box(x, y + h // 3, w, h // 3, WHITE)
    pg.box(x, y + 2 * h // 3, w, h - 2 * h // 3, GREEN)
    pg.ring(x + w // 2, y + h // 2, h // 6, NAVY2, 2)


def draw_globe(pg, cx, cy, r):
    pg.disc(cx, cy, r, SEA)
    pg.disc(cx - r // 3, cy - r // 4, r // 4, GREEN)
    pg.disc(cx + r // 4, cy + r // 5, r // 5, GREEN)
    pg.disc(cx + r // 10, cy - r // 2, r // 6, GREEN)
    pg.ring(cx, cy, r, WHITE, 2)
    for k in range(-2, 3):
        pg.vbar(cx + k * r // 3, cy - r + 4, 2 * r - 8, (210, 225, 240), 1)
    pg.hbar(cx - r + 4, cy, 2 * r - 8, (210, 225, 240), 1)


# ------------------------------------------------------------------ layout
def kicker(pg, x, y, label, color=RED):
    pg.box(x, y, 10, 10, color)
    pg.draw_text(x + 16, y - 1, label, 2, color)


def build():
    pg = Page(W, H, PAPER)

    # ---- masthead ------------------------------------------------------
    pg.box(0, 0, W, 118, NAVY)
    pg.box(0, 118, W, 5, GOLD)
    pg.draw_text(24, 18, "THE WORLD TODAY", 6, WHITE)
    pg.draw_text(24, 66, "ONE DAY  -  ONE PAGE  -  THE NEWS THAT MATTERED", 2, GOLD)
    pg.draw_text(700, 22, "THURSDAY", 4, WHITE)
    pg.draw_text(700, 58, "26 NOVEMBER 2026", 3, GOLD)
    pg.draw_text(700, 92, "WORLD NEWS IN ONE IMAGE", 2, (180, 195, 220))

    # ---- LEAD: tariff shock --------------------------------------------
    lx, ly, lw, lh = 24, 134, 600, 336
    pg.box(lx, ly, lw, lh, CREAM)
    pg.box(lx, ly, lw, 4, RED)
    kicker(pg, lx + 16, ly + 16, "LEAD  -  MARKETS")
    y = pg.headline(lx + 16, ly + 38, lw - 32, "TARIFF SHOCK SINKS ASIAN MARKETS", 5, RED)
    draw_falling_chart(pg, lx + 16, y + 8, 190, 150)
    tx = lx + 222
    yy = pg.body(tx, y + 8,
                 "THE US UNVEILS A NEW TARIFF PLAN AIMED AT FACTORY "
                 "OVERCAPACITY IN 16 TRADING PARTNERS. SEOUL FALLS 6%, "
                 "TOKYO 3%, AND US FUTURES SLIDE AS INVESTORS BRACE FOR "
                 "HIGHER PRICES AND A SLOWER ECONOMY.",
                 2, INK, 30, 19)
    pg.body(tx, yy + 10,
            "THE PLAN LANDS DAYS AFTER A DEMOCRATIC MIDTERM WIN AND "
            "JUST BEFORE THANKSGIVING.",
            2, GREY, 30, 19)

    # ---- right column: space + EU summit --------------------------------
    rx, rw = 640, 360
    # space
    ry, rh = 134, 168
    pg.box(rx, ry, rw, rh, WHITE)
    pg.box(rx, ry, rw, 4, NAVY2)
    kicker(pg, rx + 12, ry + 12, "SPACE  -  CHINA")
    y = pg.headline(rx + 12, ry + 32, rw - 24,
                    "FIRST PAKISTANI IN ORBIT", 3)
    pg.body(rx + 12, y + 4,
            "SHENZHOU-24 DOCKS AT TIANGONG. ZEESHAN ALI IS THE FIRST "
            "FOREIGN VISITOR TO CHINA'S STATION.",
            2, INK, 28, 18)
    # EU summit
    ry2, rh2 = 310, 160
    pg.box(rx, ry2, rw, rh2, WHITE)
    pg.box(rx, ry2, rw, 4, TEAL)
    kicker(pg, rx + 12, ry2 + 12, "EUROPE  -  BRUSSELS")
    y = pg.headline(rx + 12, ry2 + 32, rw - 24,
                    "EU LEADERS MEET IN BRUSSELS", 3)
    pg.body(rx + 12, y + 4,
            "A EURO SUMMIT AND A SPECIAL EUROPEAN COUNCIL OPEN IN "
            "BRUSSELS, WITH TRADE AND DEFENCE ON THE AGENDA.",
            2, INK, 28, 18)

    # ---- middle row: three stories --------------------------------------
    my, mh = 486, 246
    # Colombia
    x, w = 24, 320
    pg.box(x, my, w, mh, WHITE)
    pg.box(x, my, w, 4, GOLD)
    kicker(pg, x + 12, my + 12, "PEACE  -  COLOMBIA", GOLD)
    y = pg.headline(x + 12, my + 32, w - 24, "10 YEARS OF PEACE", 3)
    pg.body(x + 12, y + 4,
            "COLOMBIA MARKS A DECADE SINCE ITS HISTORIC PEACE ACCORD. "
            "THE UN CHIEF PRAISES PROGRESS BUT WARNS OF UNFINISHED "
            "COMMITMENTS.",
            2, INK, 21, 18)
    draw_ten_badge(pg, x + w - 44, my + mh - 44, 30)
    # India
    x, w = 360, 320
    pg.box(x, my, w, mh, WHITE)
    pg.box(x, my, w, 4, ORANGE)
    kicker(pg, x + 12, my + 12, "INDIA  -  CONSTITUTION DAY", ORANGE)
    y = pg.headline(x + 12, my + 32, w - 24,
                    "INDIA MARKS CONSTITUTION DAY", 3)
    pg.body(x + 12, y + 4,
            "NOVEMBER 26 IS SAMVIDHAN DIVAS. IITS WILL ADD 6,000 SEATS "
            "IN ROBOTICS, AI AND SPACE TECHNOLOGY FROM 2027.",
            2, INK, 23, 18)
    draw_tricolour(pg, x + w - 66, my + mh - 40, 54, 28)
    # Venezuela
    x, w = 696, 304
    pg.box(x, my, w, mh, WHITE)
    pg.box(x, my, w, 4, RED)
    kicker(pg, x + 12, my + 12, "ECONOMY  -  VENEZUELA", RED)
    y = pg.headline(x + 12, my + 32, w - 24,
                    "VENEZUELA REVEALS $237.5BN DEBT", 3)
    pg.body(x + 12, y + 4,
            "THE GOVERNMENT PUTS PUBLIC DEBT AT $237.5 BILLION AS IT "
            "PREPARES A HISTORIC ECONOMIC RESTRUCTURE.",
            2, INK, 22, 18)
    draw_globe(pg, x + w - 46, my + mh - 48, 32)

    # ---- sport band ------------------------------------------------------
    sy, sh = 748, 118
    pg.box(24, sy, 976, sh, NAVY)
    pg.draw_text(44, sy + 14, "SPORT", 3, GOLD)
    pg.draw_text(44, sy + 44, "REAL MADRID 5-1 PSV", 3, WHITE)
    pg.draw_text(44, sy + 78, "BELLINGHAM STUNNER, MBAPPE BRACE", 2,
                 (200, 210, 230))
    pg.draw_text(532, sy + 14, "CRICKET", 3, GOLD)
    pg.draw_text(532, sy + 44, "IPL AUCTION DRAWS 1,220", 3, WHITE)
    pg.draw_text(532, sy + 78, "GUKESH IN WORLD CHESS TITLE FIGHT", 2,
                 (200, 210, 230))

    # ---- also-today strip ------------------------------------------------
    ay = 882
    pg.draw_text(24, ay, "ALSO TODAY", 3, RED)
    pg.hbar(24, ay + 28, 976, INK, 2)
    briefs = [
        "MUMBAI MARKS 18 YEARS SINCE THE 26/11 ATTACKS.",
        "BANGLADESH RAISES GARMENT WORKERS' MINIMUM WAGE BY 36%.",
        "NORTH KOREA ORDERS SWITZERLAND TO CLOSE ITS PYONGYANG OFFICE.",
        "SHEIKH HASINA SEEKS RETURN TO BANGLADESH ON DECEMBER 16.",
    ]
    yy = ay + 38
    for b in briefs:
        pg.draw_text(24, yy, "*", 2, RED)
        pg.draw_text(44, yy, b, 2, INK)
        yy += 17

    pg.draw_text(24, 994,
                 "THURSDAY 26 NOVEMBER 2026  -  AS REPORTED BY REUTERS, "
                 "XINHUA AND OTHERS",
                 2, GREY)
    return pg


# ------------------------------------------------------------------- PNG
def png_chunk(tag, payload):
    out = struct.pack(">I", len(payload)) + tag + payload
    return out + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)


def encode_png(pg):
    raw = bytearray()
    for y in range(pg.h):
        raw.append(0)
        raw += pg.buf[y * pg.w * 3:(y + 1) * pg.w * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", struct.pack(">IIBBBBB", pg.w, pg.h, 8, 2, 0, 0, 0))
    png += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += png_chunk(b"IEND", b"")
    return png


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(build())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} ({len(data)} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
