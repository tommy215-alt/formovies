"""地図の一覧の画像（maps/sheet_<名>.png）。関東の 7 枚（2 日まで）＋日本の 7 枚（3 日目から）。"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
M = os.path.join(HERE, "maps")
name = sys.argv[1] if len(sys.argv) > 1 else "base"
font = ImageFont.truetype(r"C:\Windows\Fonts\meiryo.ttc", 22)
rows = [("kanto", [("0.5h", "30 分"), ("1h", "1 時間"), ("3h", "3 時間"), ("6h", "6 時間"), ("12h", "12 時間"), ("24h", "1 日"), ("48h", "2 日")]),
        ("japan", [("3d", "3 日"), ("7d", "7 日"), ("8d", "8 日"), ("14d", "14 日"), ("22d", "22 日"), ("30d", "30 日"), ("90d", "90 日")])]
tiles = []
for rg, keys in rows:
    line = []
    for k, lab in keys:
        p = os.path.join(M, f"{name}_{rg}_{k}.png")
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        im.thumbnail((300, 360))
        c = Image.new("RGB", (300, 400), (10, 12, 18)); c.paste(im, ((300 - im.width) // 2, 36))
        ImageDraw.Draw(c).text((10, 4), lab, fill=(235, 235, 235), font=font)
        line.append(c)
    tiles.append(line)
W = 300 * max(len(l) for l in tiles); H = 400 * len(tiles)
sheet = Image.new("RGB", (W, H), (10, 12, 18))
for i, line in enumerate(tiles):
    for j, c in enumerate(line):
        sheet.paste(c, (j * 300, i * 400))
sheet.save(os.path.join(M, f"sheet_{name}.png"))
print(os.path.join(M, f"sheet_{name}.png"))
