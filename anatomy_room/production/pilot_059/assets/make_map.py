#!/usr/bin/env python3
"""l01 の地図の素材：日本のまわりの衛星画像（world.jpg を切り抜き、km の座標に）と、ヒマラヤの形（標高データから、本州の向きに回して重ねる用の透明な PNG）。
    python assets/make_map.py → assets/photo/japan.png・himalaya_ov.png・map.json"""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = 6371.0
KM = 2.0                                                     # 出力の 1 ピクセル＝2 km
ALPS = (36.3, 137.6)                                         # 日本アルプスの中心のあたり（ここにヒマラヤの真ん中を置く）
ARC = [(35.24, 74.59), (33.0, 77.5), (30.4, 81.3), (28.6, 84.5), (27.99, 86.93), (27.7, 88.15), (27.9, 91.5), (29.63, 95.06)]   # ヒマラヤの尾根（ナンガ・パルバット〜ナムチャ・バルワ）


def local(lat, lon, lat0, lon0):
    return R * math.radians(lon - lon0) * math.cos(math.radians(lat0)), R * math.radians(lat - lat0)


def japan():
    W = Image.open(HERE / "photo" / "world.jpg").convert("RGB"); w, h = W.size
    lat0, lon0 = ALPS; half = 1500                               # ±1,500 km
    n = int(2 * half / KM); out = np.zeros((n, n, 3), np.uint8); src = np.asarray(W)
    ys, xs = np.mgrid[0:n, 0:n]; X = xs * KM - half; Y = half - ys * KM
    lat = lat0 + np.degrees(Y / R); lon = lon0 + np.degrees(X / (R * math.cos(math.radians(lat0))))
    px = ((lon + 180) / 360 * w).astype(int).clip(0, w - 1); py = ((90 - lat) / 180 * h).astype(int).clip(0, h - 1)
    Image.fromarray(src[py, px]).save(HERE / "photo" / "japan.png"); return half


def himalaya():
    H = np.load(HERE / "dem" / "himalaya.npy"); M = json.loads((HERE / "dem" / "himalaya.json").read_text(encoding="utf-8")); z = M["z"]; nN = H.shape[0]
    mid = ARC[4]; ax, ay = zip(*[local(a, b, *mid) for a, b in ARC]); ax, ay = np.array(ax), np.array(ay)
    ang_h = math.atan2(ay[-1] - ay[0], ax[-1] - ax[0])
    jp0, jp1 = local(34.0, 131.0, *ALPS), local(41.0, 140.9, *ALPS); ang_j = math.atan2(jp1[1] - jp0[1], jp1[0] - jp0[0])
    rot = ang_j - ang_h; half = 1500; n = int(2 * half / KM)
    ys, xs = np.mgrid[0:n, 0:n]; X = xs * KM - half; Y = half - ys * KM                     # 日本の座標（km）
    c, s = math.cos(-rot), math.sin(-rot); hx = X * c - Y * s; hy = X * s + Y * c              # ヒマラヤの座標に戻す
    lat = mid[0] + np.degrees(hy / R); lon = mid[1] + np.degrees(hx / (R * math.cos(math.radians(mid[0]))))
    N = 2 ** z; tx = (lon + 180) / 360 * N; ty = (1 - np.arcsinh(np.tan(np.radians(lat))) / math.pi) / 2 * N
    x0 = (M["lon"][0] + 180) / 360 * N; y0 = (1 - math.asinh(math.tan(math.radians(M["lat"][1]))) / math.pi) / 2 * N
    px = ((tx - x0) * 256).astype(int); py = ((ty - y0) * 256).astype(int); ok = (px >= 0) & (px < nN) & (py >= 0) & (py < nN)
    E = np.where(ok, H[py.clip(0, nN - 1), px.clip(0, nN - 1)], 0.0)
    d = np.full(X.shape, 1e9)                                                                    # 尾根の線からの距離（ヒマラヤだけ取り出す。チベットの高原は除く）
    for i in range(len(ax) - 1):
        p0 = np.array([ax[i], ay[i]]); p1 = np.array([ax[i + 1], ay[i + 1]]); v = p1 - p0; L2 = v @ v
        t = np.clip(((hx - p0[0]) * v[0] + (hy - p0[1]) * v[1]) / L2, 0, 1); d = np.minimum(d, np.hypot(hx - (p0[0] + t * v[0]), hy - (p0[1] + t * v[1])))
    band = np.clip((150 - d) / 60, 0, 1); hi = np.clip((E - 3500) / 2500, 0, 1)
    gy, gx = np.gradient(E, KM * 1000); shade = np.clip(.75 + (gx * -.7 + gy * .7) * 4, .35, 1.25)       # 陰影（左上から光）
    a = band * hi; snow = np.clip((E - 4500) / 1500, 0, 1)
    col = np.stack([(.55 + .45 * snow) * shade, (.5 + .5 * snow) * shade, (.48 + .52 * snow) * shade], -1).clip(0, 1)
    rgba = np.concatenate([col * 255, a[..., None] * 255], -1).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(HERE / "photo" / "himalaya_ov.png")
    return math.degrees(rot), float((a > .5).sum() * KM * KM)


if __name__ == "__main__":
    half = japan(); rot, area = himalaya()
    (HERE / "photo" / "map.json").write_text(json.dumps({"half_km": half, "km_per_px": KM, "rot_deg": rot, "alps": ALPS}), encoding="utf-8")
    print("rot", round(rot, 1), "deg; himalaya mask area", round(area), "km2")
