"""3D の小物の絵（自作）：どこの国のものでもないお札（記号だけ）、スマホの残高の画面、カードの表。assets/gen/ に。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import random
HERE = Path(__file__).resolve().parents[1]; OUT = HERE / "assets" / "gen"; OUT.mkdir(exist_ok=True)
DG = str(HERE / "assets" / "fonts" / "DelaGothicOne-Regular.ttf"); BZ = str(HERE / "assets" / "fonts" / "BIZUDPGothic-Bold.ttf")
NOTES = [("usd", (62, 107, 74), (156, 199, 164), "$"), ("jpy", (91, 63, 114), (196, 169, 218), "¥"), ("eur", (47, 90, 128), (166, 200, 230), "€"), ("gbp", (122, 74, 42), (224, 184, 148), "£")]
for key, d, l, s in NOTES:
    W, H = 1024, 480; im = Image.new("RGB", (W, H), l); g = ImageDraw.Draw(im); r = random.Random(key)
    for i in range(0, W, 6):
        g.line([(i, 0), (i + 120, H)], fill=tuple(int(c * .93) for c in l), width=1)
    g.rectangle([18, 18, W - 18, H - 18], outline=d, width=10); g.rectangle([44, 44, W - 44, H - 44], outline=d, width=3)
    for k in range(6):
        g.ellipse([120 + k * 18, 120 + k * 10, 420 - k * 18, 360 - k * 10], outline=tuple(int(c * .85) for c in l), width=2)
    g.ellipse([640, 120, 880, 360], fill=d); f = ImageFont.truetype(DG, 170); g.text((760, 236), s, font=f, fill=l, anchor="mm")
    f2 = ImageFont.truetype(DG, 70); g.text((80, 400), "1000", font=f2, fill=d, anchor="ls"); g.text((W - 80, 110), "1000", font=f2, fill=d, anchor="rs")
    im.filter(ImageFilter.GaussianBlur(.6)).save(OUT / f"note_{key}.jpg", quality=92)
# スマホの残高の画面（数字は飾り）
W, H = 720, 1480; im = Image.new("RGB", (W, H), (14, 18, 28)); g = ImageDraw.Draw(im)
for y in range(H):
    c = int(28 + 30 * y / H); g.line([(0, y), (W, y)], fill=(c // 2, c // 2 + 6, c + 12))
fb = ImageFont.truetype(BZ, 44); fd = ImageFont.truetype(DG, 92); fs = ImageFont.truetype(BZ, 34)
g.rounded_rectangle([50, 260, W - 50, 640], 40, fill=(34, 46, 72)); g.text((90, 320), "残高", font=fb, fill=(170, 190, 220)); g.text((W - 80, 520), "1,234,567", font=fd, fill=(255, 255, 255), anchor="rs")
for k in range(5):
    y = 720 + k * 130; g.rounded_rectangle([50, y, W - 50, y + 100], 24, fill=(26, 34, 52)); g.ellipse([80, y + 22, 136, y + 78], fill=(70, 110, 170)); g.rectangle([160, y + 34, 420, y + 50], fill=(90, 105, 130)); g.rectangle([W - 230, y + 34, W - 90, y + 62], fill=(120, 140, 170))
im.save(OUT / "phone.jpg", quality=92)
# カード
W, H = 856, 540; im = Image.new("RGB", (W, H)); g = ImageDraw.Draw(im)
for x in range(W):
    t = x / W; g.line([(x, 0), (x, H)], fill=(int(30 + 40 * t), int(60 + 30 * t), int(110 + 40 * t)))
g.rounded_rectangle([90, 190, 220, 290], 14, fill=(226, 196, 106)); [g.line([(90, 215 + i * 25), (220, 215 + i * 25)], fill=(170, 140, 60), width=3) for i in range(3)]
fc = ImageFont.truetype(BZ, 52)
for i in range(4):
    g.text((90 + i * 180, 400), "••••", font=fc, fill=(230, 235, 245))
im.save(OUT / "card.jpg", quality=92)
print("ok")
# 定規（1 cm ごとの数字、1 mm の目盛り）
for length_cm in (5, 10):
    Wd, Hd = 200 * length_cm, 360; im = Image.new("RGB", (Wd, Hd), (236, 228, 208)); g = ImageDraw.Draw(im); fnt = ImageFont.truetype(BZ, 64)
    for mm in range(length_cm * 10 + 1):
        x = min(Wd - 3, int(mm * Wd / (length_cm * 10))); hh = 150 if mm % 10 == 0 else 95 if mm % 5 == 0 else 60; g.line([(x, 0), (x, hh)], fill=(40, 34, 28), width=5 if mm % 10 == 0 else 3)
        if mm % 10 == 0 and 0 < mm < length_cm * 10:
            g.text((x, 240), str(mm // 10), font=fnt, fill=(40, 34, 28), anchor="mm")
    g.text((Wd - 30, 240), "cm", font=ImageFont.truetype(BZ, 44), fill=(40, 34, 28), anchor="rm")
    im.save(OUT / f"ruler{length_cm}.png")
print("ruler ok")
