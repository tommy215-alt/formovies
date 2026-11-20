"""pilot_064 の背景：紺の地に金の大陸の世界地図（NASA Visible Earth の地表画像〔パブリックドメイン〕から陸の形だけを取り出して自前で着色）→ assets/worldmap.png
緯度 80°N〜60°S を切り出す（正距円筒図法のまま）。経度 −170°〜190° にずらして、日本が右端で切れないように"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
src = Image.open(HERE / ".." / ".." / "common" / "vendor" / "earth" / "land_2048.jpg").convert("RGB")
a = np.asarray(src).astype(np.float32) / 255; r, g, b = a[..., 0], a[..., 1], a[..., 2]
ocean = (b > r + .04) & (b > g - .02) & (a.max(-1) < .55)          # 海は暗い青
land = (~ocean).astype(np.float32)
H, W = land.shape
land = np.roll(land, int(W * 10 / 360), axis=1)                      # 左端を 170°W に
lum = np.roll(a.mean(-1), int(W * 10 / 360), axis=1)
y0, y1 = int(H * (90 - 80) / 180), int(H * (90 + 60) / 180)
land, lum = land[y0:y1], lum[y0:y1]
m = Image.fromarray((land * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5)).resize((W * 2, (y1 - y0) * 2), Image.LANCZOS)
m = np.asarray(m.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
lum = np.asarray(Image.fromarray((lum * 255).astype(np.uint8)).resize(m.shape[::-1], Image.LANCZOS)).astype(np.float32) / 255
hh, ww = m.shape
navy = np.array([.035, .06, .13]); gold_hi = np.array([1.0, .82, .45]); gold_lo = np.array([.62, .42, .16])
k = np.clip((lum - .15) / .6, 0, 1)[..., None]
goldc = gold_lo * (1 - k) + gold_hi * k
out = navy * (1 - m[..., None]) + goldc * m[..., None]
yy, xx = np.mgrid[0:hh, 0:ww]
for lon in range(-180, 181, 30):                                     # 経線・緯線（細い金）
    x = int((lon + 170) % 360 / 360 * ww); out[:, max(0, x - 1):x + 1] = out[:, max(0, x - 1):x + 1] * .7 + np.array([.5, .4, .2]) * .3
for lat in range(-60, 81, 20):
    y = int((80 - lat) / 140 * hh); out[max(0, y - 1):y + 1] = out[max(0, y - 1):y + 1] * .7 + np.array([.5, .4, .2]) * .3
Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(HERE / "worldmap.png")
print("ok", ww, hh)
