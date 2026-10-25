"""Procedural chalk-writing animation.

Each board "program" is a list of drawing elements with local start/end times.
For every element we precompute a full chalk mask and a per-pixel "appear time",
so that a frame at time t is simply  mask * (time_map <= t).
Output: RGBA PNG sequence (white chalk, alpha = chalk density) + pen.json
(the chalk tip position per frame, in UV 0..1, used to animate the chalk stick in Blender).
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
FPS = 30
rng = np.random.default_rng(7)


def grain(h, w, seed):
    """Static chalk grain: speckled density 0.35..1 with fine streaks."""
    r = np.random.default_rng(seed)
    g = r.random((h, w)).astype(np.float32)
    g = np.array(Image.fromarray((g * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), np.float32) / 255
    streak = r.random((h, w // 6 + 1)).astype(np.float32)
    streak = np.array(Image.fromarray((streak * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR), np.float32) / 255
    d = np.clip((g - 0.5) * 2.2 + 0.62, 0, 1) * (0.75 + 0.25 * streak)
    return np.clip(d, 0.3, 1.0)


def warp(mask, amp, seed):
    """Small low-frequency displacement so glyphs look hand-drawn."""
    h, w = mask.shape
    r = np.random.default_rng(seed)
    def field():
        f = r.random((h // 40 + 2, w // 40 + 2)).astype(np.float32)
        return (np.array(Image.fromarray((f * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255 - 0.5) * 2 * amp
    yy, xx = np.mgrid[0:h, 0:w]
    sx = np.clip((xx + field()).astype(int), 0, w - 1); sy = np.clip((yy + field()).astype(int), 0, h - 1)
    return mask[sy, sx]


class Board:
    def __init__(self, w, h, seed=1):
        self.w, self.h = w, h
        self.elems = []   # (mask float, time map float, t0, kind)
        self.erases = []
        self.pen_paths = []  # (t0, t1, function t->(u,v))
        self.grain = grain(h, w, seed)
        self.seed = seed

    # ---------- elements ----------
    def text(self, s, x, y, size, t0, t1, spacing=1.04, seed=None):
        """x,y: top-left in UV (0..1, y down). size: glyph height as fraction of board height."""
        W, H = self.w, self.h
        px = int(size * H)
        font = ImageFont.truetype(FONT, px)
        img = Image.new("L", (W, H), 0); d = ImageDraw.Draw(img)
        tmap = np.full((H, W), np.inf, np.float32)
        cx = x * W; cy = y * H
        chars = [c for c in s]
        n = max(1, sum(1 for c in chars if not c.isspace()))
        dt = (t1 - t0) / n
        k = 0
        boxes = []
        for c in chars:
            adv = font.getlength(c) * spacing
            if c.isspace():
                cx += adv; continue
            jx = rng.normal(0, px * 0.02); jy = rng.normal(0, px * 0.03)
            d.text((cx + jx, cy + jy), c, fill=255, font=font)
            bx0, by0, bx1, by1 = int(cx + jx), int(cy + jy + px * 0.1), int(cx + jx + adv), int(cy + jy + px * 1.25)
            a, b = t0 + k * dt, t0 + (k + 0.85) * dt
            yy, xx = np.mgrid[max(0, by0):min(H, by1), max(0, bx0):min(W, bx1)]
            # writing order inside a glyph: top-to-bottom with slight left-to-right
            prog = ((yy - by0) / max(1, by1 - by0)) * 0.75 + ((xx - bx0) / max(1, bx1 - bx0)) * 0.25
            sub = tmap[max(0, by0):min(H, by1), max(0, bx0):min(W, bx1)]
            np.minimum(sub, a + prog * (b - a), out=sub)
            boxes.append((a, b, bx0 / W, by0 / H, bx1 / W, by1 / H))
            cx += adv; k += 1
        m = np.array(img, np.float32) / 255
        m = warp(m, px * 0.025, seed or (self.seed + len(self.elems)))
        self.elems.append((m, tmap, t0, "text"))

        def pen(t, boxes=boxes):
            for a, b, x0, y0, x1, y1 in boxes:
                if a <= t <= b:
                    p = (t - a) / (b - a)
                    zig = math.sin(p * math.pi * 5) * 0.35 + 0.5
                    return (x0 + (x1 - x0) * zig, y0 + (y1 - y0) * p)
            return None
        self.pen_paths.append((t0, t1, pen))

    def polyline(self, pts, t0, t1, width=0.012, closed=False):
        W, H = self.w, self.h
        P = [(u * W, v * H) for u, v in pts] + ([(pts[0][0] * W, pts[0][1] * H)] if closed else [])
        seg = [math.dist(P[i], P[i + 1]) for i in range(len(P) - 1)]
        L = sum(seg)
        img = Image.new("L", (W, H), 0); d = ImageDraw.Draw(img)
        lw = max(2, int(width * H))
        d.line(P, fill=255, width=lw, joint="curve")
        for p in (P[0], P[-1]):
            d.ellipse([p[0] - lw / 2, p[1] - lw / 2, p[0] + lw / 2, p[1] + lw / 2], fill=255)
        m = np.array(img, np.float32) / 255
        # appear time: arc length of nearest point (computed per segment within its bbox)
        tmap = np.full((H, W), np.inf, np.float32)
        acc = 0.0
        for i, sl in enumerate(seg):
            (x0, y0), (x1, y1) = P[i], P[i + 1]
            bx0, bx1 = int(max(0, min(x0, x1) - lw)), int(min(W, max(x0, x1) + lw + 1))
            by0, by1 = int(max(0, min(y0, y1) - lw)), int(min(H, max(y0, y1) + lw + 1))
            yy, xx = np.mgrid[by0:by1, bx0:bx1].astype(np.float32)
            vx, vy = x1 - x0, y1 - y0
            tt = np.clip(((xx - x0) * vx + (yy - y0) * vy) / max(1e-6, sl * sl), 0, 1)
            dist = np.hypot(xx - (x0 + tt * vx), yy - (y0 + tt * vy))
            val = np.where(dist <= lw, t0 + (acc + tt * sl) / L * (t1 - t0), np.inf).astype(np.float32)
            sub = tmap[by0:by1, bx0:bx1]; np.minimum(sub, val, out=sub)
            acc += sl
        m = warp(m, lw * 0.25, self.seed + 31 * len(self.elems))
        self.elems.append((m, tmap, t0, "line"))

        def pen(t, P=P, seg=seg, L=L):
            if not (t0 <= t <= t1): return None
            s = (t - t0) / (t1 - t0) * L
            for i, sl in enumerate(seg):
                if s <= sl or i == len(seg) - 1:
                    f = min(1, s / max(1e-6, sl))
                    return ((P[i][0] + (P[i + 1][0] - P[i][0]) * f) / W, (P[i][1] + (P[i + 1][1] - P[i][1]) * f) / H)
                s -= sl
        self.pen_paths.append((t0, t1, pen))

    def circle(self, c, r, t0, t1, width=0.012, start=-90, n=96):
        asp = self.w / self.h
        pts = [(c[0] + r / asp * math.cos(math.radians(start + 360 * i / n)), c[1] + r * math.sin(math.radians(start + 360 * i / n))) for i in range(n + 1)]
        self.polyline(pts, t0, t1, width)

    def erase(self, box, t0, t1):
        self.erases.append((box, t0, t1))

    # ---------- frame ----------
    def frame(self, t):
        acc = np.zeros((self.h, self.w), np.float32)
        for m, tmap, et0, kind in self.elems:
            vis = m * (tmap <= t)
            for (x0, y0, x1, y1), a, b in self.erases:
                if et0 < a and t > a:   # element existed before this erase started
                    X0, X1, Y0, Y1 = int(x0 * self.w), int(x1 * self.w), int(y0 * self.h), int(y1 * self.h)
                    front = X0 + (X1 - X0) * min(1, (t - a) / (b - a))
                    region = vis[Y0:Y1, X0:int(front)]
                    region *= 0.08
            acc = np.maximum(acc, vis)
        a = acc * self.grain
        img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
        halo = img.filter(ImageFilter.GaussianBlur(3))
        a = np.maximum(np.array(img, np.float32), np.array(halo, np.float32) * 0.35) / 255
        rgba = np.zeros((self.h, self.w, 4), np.uint8)
        rgba[..., :3] = 245
        rgba[..., 3] = (np.clip(a, 0, 1) * 255).astype(np.uint8)
        return Image.fromarray(rgba, "RGBA")

    def pen(self, t):
        for a, b, f in self.pen_paths:
            if a <= t <= b:
                p = f(t)
                if p: return p
        for (x0, y0, x1, y1), a, b in self.erases:
            if a <= t <= b:
                p = (t - a) / (b - a)
                return (x0 + (x1 - x0) * p, (y0 + y1) / 2 + math.sin(p * 30) * (y1 - y0) * 0.3)
        return None

    def render(self, name, duration, static=False):
        out = os.path.join(ROOT, "assets", "frames", "boards", name); os.makedirs(out, exist_ok=True)
        n = 1 if static else int(round(duration * FPS))
        pens = []
        for f in range(n):
            t = duration if static else f / FPS
            self.frame(t).save(os.path.join(out, f"{f + 1:04d}.png"), compress_level=1)
            pens.append(self.pen(t))
        json.dump(pens, open(os.path.join(out, "pen.json"), "w"))
        print(name, n, "frames")


# ---------------- board programs ----------------
def tri_diagram(b, x, y, s, t0, t1):
    """Right triangle in its circumscribed circle (Thales) — a classic 19th-century blackboard figure."""
    asp = b.w / b.h
    A = (x + 0.08 / asp, y + s); B = (x + 0.08 / asp + s * 1.1 / asp, y + s); C = (x + 0.08 / asp, y + s * 0.25)
    span = t1 - t0
    b.polyline([A, B, C, A], t0, t0 + span * 0.45)
    m = ((B[0] + C[0]) / 2, (B[1] + C[1]) / 2)
    r = math.hypot((B[0] - C[0]) * asp, B[1] - C[1]) / 2
    b.circle(m, r, t0 + span * 0.5, t0 + span * 0.9, start=0)
    q = 0.05
    b.polyline([(A[0], A[1] - q), (A[0] + q / asp, A[1] - q), (A[0] + q / asp, A[1])], t0 + span * 0.92, t1, 0.008)


def program(name):
    if name == "A1":   # hook — modern green board, 8.2 s
        b = Board(2048, 614, 11)
        b.text("この黒板、実は", 0.18, 0.08, 0.22, 1.0, 2.6)
        b.text("教育の歴史を変えた", 0.18, 0.37, 0.22, 2.7, 4.9)
        b.text("発明です。", 0.18, 0.66, 0.22, 5.0, 6.4)
        b.polyline([(0.18, 0.95), (0.67, 0.94)], 6.6, 7.2, 0.014)
        return b, 8.2, False
    if name == "B2":   # slate macro — write, erase, write again (4.3 s)
        b = Board(1024, 750, 21)
        b.text("a b c", 0.12, 0.12, 0.26, 0.2, 1.4)
        b.text("1 2 3", 0.12, 0.50, 0.26, 1.4, 2.2)
        b.erase((0.05, 0.05, 0.95, 0.95), 2.4, 3.0)
        b.text("4 5 6", 0.14, 0.30, 0.3, 3.15, 4.2)
        return b, 4.3, False
    if name == "C2":   # big black board — geometry being drawn (4.2 s)
        b = Board(2048, 745, 31)
        tri_diagram(b, 0.08, 0.12, 0.62, 0.0, 3.6)
        b.text("a² + b² = c²", 0.50, 0.30, 0.16, 1.6, 4.0)
        return b, 4.2, False
    if name == "C3":   # question mark (3.5 s)
        b = Board(2048, 745, 32)
        tri_diagram(b, 0.08, 0.12, 0.62, -10, -5)
        b.text("a² + b² = c²", 0.50, 0.30, 0.16, -10, -5)
        b.text("?", 0.80, 0.52, 0.36, 0.6, 1.6)
        return b, 3.5, False
    if name == "C4":   # board full of lessons (static)
        b = Board(2048, 745, 33)
        tri_diagram(b, 0.05, 0.12, 0.62, -10, -5)
        b.text("a² + b² = c²", 0.38, 0.12, 0.13, -10, -5)
        b.text("3² + 4² = 5²", 0.38, 0.32, 0.13, -10, -5)
        b.circle((0.80, 0.42), 0.28, -10, -5)
        b.polyline([(0.80 - 0.28 * 745 / 2048, 0.42), (0.80 + 0.28 * 745 / 2048, 0.42)], -10, -5)
        b.text("π r²", 0.76, 0.76, 0.12, -10, -5)
        b.text("12 × 12 = 144", 0.38, 0.62, 0.12, -10, -5)
        return b, 1, True
    if name == "D1":   # why green? (3.9 s)
        b = Board(2048, 614, 41)
        b.text("なぜ", 0.30, 0.18, 0.30, 0.5, 1.4)
        b.text("緑？", 0.30, 0.52, 0.34, 1.5, 2.6)
        return b, 3.9, False
    if name == "D5b":  # the name stays "黒板" (4.4 s)
        b = Board(2048, 614, 51)
        b.text("黒板", 0.33, 0.22, 0.48, 0.3, 2.2)
        b.polyline([(0.30, 0.86), (0.70, 0.85)], 2.6, 3.2, 0.016)
        return b, 4.4, False
    if name == "F1":   # one line grows into formulas & figures (6.4 s)
        b = Board(2048, 614, 61)
        b.polyline([(0.08, 0.55), (0.48, 0.55)], 0.2, 1.4, 0.014)
        b.polyline([(0.48, 0.55), (0.62, 0.20), (0.76, 0.55), (0.48, 0.55)], 1.6, 2.8)
        b.circle((0.62, 0.43), 0.12, 2.9, 3.6, 0.01)
        b.text("y = ax + b", 0.08, 0.12, 0.17, 3.2, 4.4)
        b.text("E = mc²", 0.80, 0.14, 0.15, 3.9, 4.9)
        b.text("S = ½ah", 0.10, 0.68, 0.15, 4.5, 5.6)
        b.polyline([(0.82, 0.80), (0.86, 0.62), (0.90, 0.74), (0.94, 0.58)], 5.2, 5.9, 0.01)
        return b, 6.4, False
    if name == "F2":   # finished board (static) for macro end shot
        b, _, _ = program("F1"); return b, 6.4, True
    if name.startswith("SLATE"):   # static scribbles for desk slates
        k = int(name[5:])
        b = Board(512, 375, 100 + k)
        items = ["abc", "1 2 3", "A B", "7+5", "cat", "2×3", "dog", "10-4", "xyz", "ABC", "9 8", "sun"]
        b.text(items[k % len(items)], 0.12, 0.15, 0.30, -10, -5)
        if k % 3 == 0: b.polyline([(0.12, 0.7), (0.8, 0.68)], -10, -5, 0.02)
        if k % 3 == 1: b.text("1 2", 0.15, 0.58, 0.25, -10, -5)
        return b, 1, True
    raise KeyError(name)


if __name__ == "__main__":
    names = sys.argv[1:] or ["A1", "B2", "C2", "C3", "C4", "D1", "D5b", "F1", "F2"] + [f"SLATE{i}" for i in range(12)]
    for nm in names:
        b, dur, static = program(nm)
        b.render(nm, dur, static)
