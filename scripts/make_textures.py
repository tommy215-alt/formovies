"""Static textures: comparison chalk, Showa board, whiteboard (marker), interactive display, gallery boards, logo."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from chalk import Board, tri_diagram, ROOT, FONT

OUT = os.path.join(ROOT, "assets", "frames", "boards")
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def chalk_static(name, build, w=2048, h=614, seed=5):
    b = Board(w, h, seed); build(b); b.render(name, 1, static=True)


def tri_px(d, x, y, s, color, width, asp=1.0):
    A = (x, y + s); B = (x + s * 1.1, y + s); C = (x, y + s * 0.25)
    d.line([A, B, C, A], fill=color, width=width, joint="curve")
    m = ((B[0] + C[0]) / 2, (B[1] + C[1]) / 2); r = math.dist(B, C) / 2
    d.ellipse([m[0] - r, m[1] - r, m[0] + r, m[1] + r], outline=color, width=width)
    q = s * 0.07
    d.line([(A[0], A[1] - q), (A[0] + q, A[1] - q), (A[0] + q, A[1])], fill=color, width=max(2, width // 2))


def whiteboard(path, w=2048, h=614):
    img = Image.new("RGB", (w, h), (236, 238, 238)); d = ImageDraw.Draw(img)
    # faint ghosting of old marker
    ghost = Image.new("L", (w, h), 0); gd = ImageDraw.Draw(ghost)
    gd.text((1300, 380), "x² − 4 = 0", font=ImageFont.truetype(FONT, 90), fill=40)
    img.paste((205, 212, 220), mask=ghost.filter(ImageFilter.GaussianBlur(6)))
    tri_px(d, 230, 80, 380, (25, 60, 160), 9)
    f = ImageFont.truetype(BOLD, 110)
    d.text((900, 120), "a² + b² = c²", font=f, fill=(30, 30, 35))
    d.text((900, 330), "3² + 4² = 5²", font=ImageFont.truetype(BOLD, 96), fill=(190, 30, 35))
    d.line([(900, 290), (1560, 285)], fill=(190, 30, 35), width=7)
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    img.save(path)


def eboard(path, w=2048, h=614):
    yy = np.linspace(0, 1, h)[:, None]
    bg = np.zeros((h, w, 3), np.float32)
    bg[...] = (np.array([14, 26, 48]) * (1 - yy) + np.array([8, 14, 30]) * yy)[:, None, :]
    img = Image.fromarray(bg.astype(np.uint8)); d = ImageDraw.Draw(img)
    for x in range(0, w, 64): d.line([(x, 0), (x, h)], fill=(22, 40, 70), width=1)
    for y in range(0, h, 64): d.line([(0, y), (w, y)], fill=(22, 40, 70), width=1)
    # toolbar
    d.rounded_rectangle([20, 20, 110, h - 20], 18, fill=(30, 46, 80))
    cols = [(255, 255, 255), (255, 210, 60), (90, 200, 255), (255, 90, 110), (120, 230, 140)]
    for i, c in enumerate(cols): d.ellipse([42, 50 + i * 95, 88, 96 + i * 95], fill=c)
    # diagram with fill
    x, y, s = 230, 90, 380
    A = (x, y + s); B = (x + s * 1.1, y + s); C = (x, y + s * 0.25)
    d.polygon([A, B, C], fill=(40, 90, 150))
    tri_px(d, x, y, s, (120, 220, 255), 7)
    f = ImageFont.truetype(BOLD, 104)
    d.text((900, 110), "a² + b² = c²", font=f, fill=(255, 255, 255))
    d.text((900, 310), "3² + 4² = 5²", font=ImageFont.truetype(BOLD, 92), fill=(255, 210, 60))
    # slide indicator
    for i in range(5): d.ellipse([1700 + i * 50, 545, 1722 + i * 50, 567], fill=(255, 255, 255) if i == 2 else (60, 80, 120))
    img.save(path)


def logo(path):
    W, H = 1020, 300
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    # mark: a chalk-board square with a single line
    d.rounded_rectangle([20, 50, 220, 250], 26, fill=(30, 74, 56, 255), outline=(235, 235, 225, 255), width=8)
    d.line([(60, 190), (180, 110)], fill=(250, 250, 245, 255), width=14)
    d.ellipse([168, 98, 192, 122], fill=(255, 205, 70, 255))
    f = ImageFont.truetype(BOLD, 96)
    d.text((255, 92), "当たり前の裏側", font=f, fill=(255, 255, 255, 255))
    img.save(path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    chalk_static("CMP", lambda b: (b.text("あいう", 0.12, 0.14, 0.30, -10, -5), b.text("ABC 123", 0.12, 0.55, 0.28, -10, -5)), 1024, 768, 8)
    def showa(b):
        b.text("日直", 0.90, 0.10, 0.10, -10, -5)
        b.text("7月20日", 0.86, 0.26, 0.08, -10, -5)
        b.text("こくばん", 0.06, 0.10, 0.13, -10, -5)
        b.polyline([(0.06, 0.30), (0.40, 0.29)], -10, -5, 0.01)
    chalk_static("SHOWA", showa, seed=9)
    chalk_static("GAL_CHALK", lambda b: (tri_diagram(b, 0.06, 0.12, 0.62, -10, -5), b.text("a² + b² = c²", 0.44, 0.20, 0.17, -10, -5), b.text("3² + 4² = 5²", 0.44, 0.54, 0.15, -10, -5)), seed=12)
    whiteboard(os.path.join(OUT, "WHITE.png"))
    eboard(os.path.join(OUT, "EBOARD.png"))
    logo(os.path.join(ROOT, "assets", "logo.png"))
    print("ok")
