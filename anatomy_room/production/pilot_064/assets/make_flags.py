"""pilot_064 の国旗（日本・アメリカ・インド・チャド）を Pillow で描く（国旗は著作権の対象外。公式の比率と色の目安で自前に描画）→ assets/flags/*.png"""
import math
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent / "flags"; OUT.mkdir(exist_ok=True)
S = 4   # 描いてから縮める（なめらかに）


def save(im, name, w):
    im.resize((w, int(w * im.size[1] / im.size[0])), Image.LANCZOS).save(OUT / f"{name}.png")


def star(d, cx, cy, r, col):
    pts = [(cx + (r if k % 2 == 0 else r * .382) * math.sin(k * math.pi / 5), cy - (r if k % 2 == 0 else r * .382) * math.cos(k * math.pi / 5)) for k in range(10)]
    d.polygon(pts, fill=col)


W, H = 900 * S, 600 * S                                  # 日本 2:3、日の丸の直径は縦の 3/5
im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im); r = H * 3 / 10
d.ellipse((W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r), fill=(188, 0, 45)); save(im, "jp", 900)

W, H = 1140 * S, 600 * S                                 # アメリカ 10:19、縞 13 本、カントンは縦 7/13・横 0.76/1.9
im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im); sh = H / 13
for i in range(0, 13, 2):
    d.rectangle((0, i * sh, W, (i + 1) * sh), fill=(178, 34, 52))
cw, ch = W * .76 / 1.9, sh * 7; d.rectangle((0, 0, cw, ch), fill=(60, 59, 110))
for row in range(9):
    n = 6 if row % 2 == 0 else 5
    for c in range(n):
        x = cw / 12 * (2 * c + 1 + (row % 2)); y = ch / 10 * (row + 1); star(d, x, y, ch * .0616 / 2 * 1.6, "white")
save(im, "us", 1140)

W, H = 900 * S, 600 * S                                  # インド 2:3、サフラン・白・緑、中央に紺の法輪（24 本の輻）
im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
d.rectangle((0, 0, W, H / 3), fill=(255, 103, 31)); d.rectangle((0, H * 2 / 3, W, H), fill=(4, 106, 56))
cx, cy, R = W / 2, H / 2, H / 3 * .45; nv = (6, 3, 141); lw = int(R * .07)
d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=nv, width=lw); d.ellipse((cx - R * .17, cy - R * .17, cx + R * .17, cy + R * .17), fill=nv)
for k in range(24):
    a = k * 2 * math.pi / 24; d.line((cx, cy, cx + R * .95 * math.cos(a), cy + R * .95 * math.sin(a)), fill=nv, width=max(2, lw // 2))
save(im, "in", 900)

W, H = 900 * S, 600 * S                                  # チャド 2:3、縦の 3 色（青・黄・赤）
im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
for i, col in enumerate(((0, 38, 100), (254, 203, 0), (198, 12, 48))):
    d.rectangle((i * W / 3, 0, (i + 1) * W / 3, H), fill=col)
save(im, "td", 900)
print("ok")
