"""pilot_040 の操縦室の画面の画像（模式。実際の 767 の表示ではない）。blender/scene.py が読む。"""
import os, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); TEX = os.path.join(HERE, "tex")


def adi():   # 姿勢の表示：空（青）と地面（茶）、目盛り
    im = Image.new("RGB", (512, 512), (0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 512, 270], fill=(30, 110, 200)); d.rectangle([0, 270, 512, 512], fill=(130, 80, 40))
    for k in range(-3, 4):
        y = 270 - k * 40; w = 60 if k % 2 else 110
        d.line([(256 - w, y), (256 + w, y)], fill=(255, 255, 255), width=3)
    d.polygon([(176, 270), (226, 270), (236, 290)], fill=(255, 220, 0)); d.polygon([(336, 270), (286, 270), (276, 290)], fill=(255, 220, 0))
    return im


def nav():   # 地図の表示：航路の線と円弧
    im = Image.new("RGB", (512, 512), (0, 0, 0)); d = ImageDraw.Draw(im)
    for r in (120, 220, 320):
        d.arc([256 - r, 470 - r, 256 + r, 470 + r], 200, 340, fill=(255, 255, 255), width=2)
    d.line([(256, 470), (300, 60)], fill=(255, 0, 255), width=4); d.polygon([(246, 470), (266, 470), (256, 440)], fill=(255, 255, 255))
    for x, y in ((300, 60), (380, 200)):
        d.ellipse([x - 8, y - 8, x + 8, y + 8], outline=(0, 255, 200), width=3)
    return im


def eicas():   # エンジンの表示：円の計器と数字
    im = Image.new("RGB", (512, 512), (0, 0, 0)); d = ImageDraw.Draw(im)
    for cx in (150, 360):
        for cy in (120, 300):
            d.arc([cx - 70, cy - 70, cx + 70, cy + 70], 150, 390, fill=(255, 255, 255), width=4)
            d.line([(cx, cy), (cx + 50 * math.cos(math.radians(-30)), cy + 50 * math.sin(math.radians(-30)))], fill=(0, 255, 120), width=5)
    d.rectangle([60, 430, 450, 480], outline=(255, 190, 0), width=4)
    return im


if __name__ == "__main__":
    os.makedirs(TEX, exist_ok=True)
    for n, f in (("adi", adi), ("nav", nav), ("eicas", eicas)):
        f().rotate(180).save(os.path.join(TEX, n + ".png"))   # 面の向きの都合で 180 度回す（038 と同じ）
    print("ok")
