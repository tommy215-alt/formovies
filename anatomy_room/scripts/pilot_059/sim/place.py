#!/usr/bin/env python3
"""ヒマラヤの真ん中（尾根の線の長さの半分の所）を日本アルプスの真ん中に置き、本州の向きに回す。
エベレストの来る場所、日本の平均標高の変化（標高データから計算）、大雪崩の届く範囲。 → place.json
標高：production/pilot_059/assets/dem/（japan：約 1.2 km ごと、himalaya：約 3 km ごと）"""
import json, math
from pathlib import Path
import numpy as np

A = Path(__file__).resolve().parents[3] / "production" / "pilot_059" / "assets" / "dem"
R = 6371.0
ALPS = (36.3, 137.6)
ARC = [(35.24, 74.59), (33.0, 77.5), (30.4, 81.3), (28.6, 84.5), (27.99, 86.93), (27.7, 88.15), (27.9, 91.5), (29.63, 95.06)]
EVEREST = (27.988, 86.925)


def local(lat, lon, lat0, lon0):
    return R * math.radians(lon - lon0) * math.cos(math.radians(lat0)), R * math.radians(lat - lat0)


def unlocal(x, y, lat0, lon0):
    return lat0 + np.degrees(y / R), lon0 + np.degrees(x / (R * np.cos(np.radians(lat0))))


# 尾根の線の真ん中
ref = ARC[4]; P = np.array([local(a, b, *ref) for a, b in ARC]); seg = np.hypot(*np.diff(P, axis=0).T); cum = np.concatenate([[0], np.cumsum(seg)]); L = cum[-1]
k = np.searchsorted(cum, L / 2) - 1; q = (L / 2 - cum[k]) / seg[k]; M = P[k] + q * (P[k + 1] - P[k])
ang_h = math.atan2(P[-1, 1] - P[0, 1], P[-1, 0] - P[0, 0])
j0, j1 = local(34.0, 131.0, *ALPS), local(41.0, 140.9, *ALPS); rot = math.atan2(j1[1] - j0[1], j1[0] - j0[0]) - ang_h
c, s = math.cos(rot), math.sin(rot)


def to_japan(lat, lon):
    """ヒマラヤの点 → 日本に置いたときの緯度・経度"""
    x, y = local(lat, lon, *ref); x -= M[0]; y -= M[1]; X, Y = x * c - y * s, x * s + y * c; la, lo = unlocal(X, Y, *ALPS); return float(la), float(lo)


ev = to_japan(*EVEREST)


def load(name):
    H = np.load(A / f"{name}.npy"); Mj = json.loads((A / f"{name}.json").read_text(encoding="utf-8")); return H, Mj


def sample(H, Mj, lat, lon):
    z = Mj["z"]; n = 2 ** z; N = H.shape[0]
    tx = (lon + 180) / 360 * n; ty = (1 - np.arcsinh(np.tan(np.radians(lat))) / math.pi) / 2 * n
    x0 = (Mj["lon"][0] + 180) / 360 * n; y0 = (1 - math.asinh(math.tan(math.radians(Mj["lat"][1]))) / math.pi) / 2 * n
    px = ((tx - x0) * 256).astype(int); py = ((ty - y0) * 256).astype(int); ok = (px >= 0) & (px < N) & (py >= 0) & (py < N)
    return np.where(ok, H[py.clip(0, N - 1), px.clip(0, N - 1)], np.nan)


# 日本の格子（2 km ごと、緯度・経度）
step = 2.0; xs = np.arange(-1500, 1500, step); X, Y = np.meshgrid(xs, xs); LAT, LON = unlocal(X, Y, *ALPS)
Hj, Mj = load("japan"); EJ = sample(Hj, Mj, LAT, LON)
jp = (EJ > 0) & (LON > 128.5) & (LAT > 30.0) & (LAT < 45.6) & ~((LON < 130.6) & (LAT > 33.9)) & ~((LON < 131.5) & (LAT > 37.0)) & ~((LAT > 42.5) & (LON < 139.3)) & ~((LAT > 44.0) & (LON > 145.9))
# 日本の点 → ヒマラヤの点
x, y = X, Y; hx, hy = x * c + y * s, -x * s + y * c; hx += M[0]; hy += M[1]; hla, hlo = unlocal(hx, hy, *ref)
Hh, Mh = load("himalaya"); EH = sample(Hh, Mh, hla, hlo)
d = np.full(X.shape, 1e9)
for i in range(len(P) - 1):
    p0, p1 = P[i], P[i + 1]; v = p1 - p0; t = np.clip(((hx - p0[0]) * v[0] + (hy - p0[1]) * v[1]) / (v @ v), 0, 1); d = np.minimum(d, np.hypot(hx - (p0[0] + t * v[0]), hy - (p0[1] + t * v[1])))
band = (d < 150) & np.isfinite(EH)
new = np.where(band, np.maximum(EH, 0), np.where(jp, EJ, 0)); land_new = jp | (band & (EH > 0))
a0 = float(EJ[jp].mean()); a1 = float(new[land_new].mean()); area0 = jp.sum() * step * step; area1 = land_new.sum() * step * step
out = dict(rot_deg=math.degrees(rot), mid_km=M.tolist(), arc_km=L, everest_lat=ev[0], everest_lon=ev[1], tokyo_km=float(np.hypot(*local(35.681, 139.767, *ev))),
           avg_now=a0, avg_new=a1, area_now=float(area0), area_new=float(area1), dT=(a1 - a0) * 6.5 / 1000,
           band_land_km2=float((band & (EH > 0)).sum() * step * step))
if __name__ == "__main__":
    (Path(__file__).with_name("place.json")).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for k_, v_ in out.items():
        print(k_, v_)
    # 地図・立体地図の素材（make_map.py の japan.png と同じ格子：±1,500 km、2 km ごと、北が上）
    np.save(A / "japan_now.npy", np.where(jp, EJ, 0)[::-1].astype(np.float32)); np.save(A / "japan_new.npy", np.where(land_new, new, 0)[::-1].astype(np.float32))
    np.save(A / "band.npy", (band & (EH > 3500))[::-1])
    from PIL import Image
    E = np.where(band, EH, 0)[::-1]; a = np.clip((E - 3500) / 2500, 0, 1) * band[::-1]; snow = np.clip((E - 4500) / 1500, 0, 1)
    gy, gx = np.gradient(E, step * 1000); sh = np.clip(.75 + (gx * -.7 + gy * .7) * 4, .35, 1.25)
    col = np.stack([(.55 + .45 * snow) * sh, (.5 + .5 * snow) * sh, (.48 + .52 * snow) * sh], -1).clip(0, 1)
    Image.fromarray(np.concatenate([col * 255, a[..., None] * 255], -1).astype(np.uint8), "RGBA").save(A.parent / "photo" / "himalaya_ov.png")
    print("saved grids and overlay")
