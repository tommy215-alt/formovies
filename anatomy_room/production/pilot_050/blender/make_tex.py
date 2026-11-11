"""pilot_050 の 3D に貼る文字の画像（python blender/make_tex.py → blender/tex/*.png）。
ゼッケン・門・看板。実在の大会の名前・ロゴは使わない。フォントは Windows の BIZ UDゴシック Bold。"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "tex"); os.makedirs(OUT, exist_ok=True)
FONT = r"C:\Windows\Fonts\BIZ-UDGothicB.ttc"


def board(name, w, h, text, bg, fg, size, border=None, checker=False, sub=None):
    im = Image.new("RGB", (w, h), bg); d = ImageDraw.Draw(im)
    if checker:                                   # ゴールの市松模様（左右の端）
        c = h // 4
        for side in (0, 1):
            for j in range(4):
                for i in range(6):
                    if (i + j) % 2 == 0:
                        x = i * c if side == 0 else w - (i + 1) * c
                        d.rectangle([x, j * c, x + c - 1, j * c + c - 1], fill=fg)
    if border:
        d.rectangle([0, 0, w - 1, h - 1], outline=border, width=max(4, h // 28))
    f = ImageFont.truetype(FONT, size); b = d.textbbox((0, 0), text, font=f)
    y = (h - (b[3] - b[1])) / 2 - b[1] - (h * .1 if sub else 0)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], y), text, font=f, fill=fg)
    if sub:
        f2 = ImageFont.truetype(FONT, int(size * .3)); b2 = d.textbbox((0, 0), sub, font=f2)
        d.text(((w - (b2[2] - b2[0])) / 2 - b2[0], h * .76 - b2[1]), sub, font=f2, fill=fg)
    im.save(os.path.join(OUT, name + ".png")); print(name, im.size)


BLUE = (18, 62, 150); WHITE = (245, 245, 240); BLACK = (16, 16, 18)
board("bib", 512, 352, "66", WHITE, BLACK, 270, border=(30, 30, 34))
board("start", 2048, 176, "スタート", BLUE, WHITE, 132)
board("goal", 2048, 176, "ゴール", BLUE, WHITE, 132, checker=True)
board("km20", 512, 512, "20km", BLUE, WHITE, 190)
board("water", 768, 320, "給水", WHITE, BLUE, 230, border=BLUE)
