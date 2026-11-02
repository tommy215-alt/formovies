"""pilot_038 の管制室の画面の画像（模式）を作る。blender/scene.py が読む。"""
import os, random
HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "tex")


def screens():
    """画面の画像（模式）：普段の数字の列と、崩れた表示"""
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(TEX, exist_ok=True)
    try:
        f = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 22)
    except Exception:
        f = ImageFont.load_default()
    rr = random.Random(5)
    labels = ["BUS A V", "BUS B V", "FC1 AMP", "FC2 AMP", "FC3 AMP", "AC1 V", "AC2 V", "BAT A", "BAT B", "O2 TK1", "O2 TK2", "H2 TK1", "CAB P", "SUIT P", "CO2 PP", "GLY T"]
    for kind in ("ok", "bad"):
        im = Image.new("RGB", (640, 480), (4, 10, 6)); d = ImageDraw.Draw(im)
        for i, lb in enumerate(labels):
            y = 18 + i * 28
            if kind == "ok":
                v = f"{rr.uniform(20, 32):6.1f}"; d.text((28, y), f"{lb:<9}", fill=(110, 230, 140), font=f); d.text((300, y), v, fill=(150, 255, 170), font=f)
            else:
                junk = "".join(rr.choice("0123456789#*@%&$+-=XO ") for _ in range(10))
                d.text((28 + rr.randint(-6, 6), y), f"{lb:<9}" if rr.random() < .4 else junk, fill=(110, 230, 140), font=f); d.text((300, y), rr.choice(["  0.0", "-----", "######", f"{rr.uniform(0, 99):6.1f}", "OFFSCL"]), fill=(255, 120, 90) if rr.random() < .3 else (150, 255, 170), font=f)
        for y in range(0, 480, 3):
            d.line([(0, y), (640, y)], fill=(0, 0, 0))
        im.rotate(180).save(os.path.join(TEX, f"screen_{kind}.png"))   # 面の向きの都合で 180 度回して保存（画面では正しい向き）


def wall():
    """正面の大きな画面（模式）：世界地図のかわりの格子と、発射からの軌跡"""
    from PIL import Image, ImageDraw
    import math
    im = Image.new("RGB", (1280, 720), (6, 16, 28)); d = ImageDraw.Draw(im)
    for x in range(0, 1280, 64):
        d.line([(x, 0), (x, 720)], fill=(20, 50, 80))
    for y in range(0, 720, 64):
        d.line([(0, y), (1280, y)], fill=(20, 50, 80))
    pts = [(80 + i * 7, 520 - 300 * math.sin(i / 160 * math.pi / 2) + 30 * math.sin(i / 20)) for i in range(160)]
    d.line(pts, fill=(255, 210, 120), width=5)
    for i in range(3):
        d.ellipse([200 + i * 300, 200 + (i % 2) * 120, 360 + i * 300, 330 + (i % 2) * 120], outline=(80, 160, 210), width=3)
    im.rotate(180).save(os.path.join(TEX, "wall.png"))


if __name__ == "__main__":
    screens(); wall()
