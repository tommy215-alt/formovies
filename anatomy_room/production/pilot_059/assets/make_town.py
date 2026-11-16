#!/usr/bin/env python3
"""冒頭（松本から見た山が盛り上がる）用の標高：松本のまわり 120 km 四方の、今の地形（town_now）と、ヒマラヤを置いたときの地形（town_new）を同じ格子で。
ヒマラヤの置き方は scripts/pilot_059/sim/place.py と同じ（真ん中を日本アルプスの真ん中に、本州の向きに回す）。
    python assets/make_town.py → assets/dem/town_now.npy・town_new.npy・town.json"""
import io, json, math, sys, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts" / "pilot_059" / "sim"))
import place as P                                                                     # noqa: E402
from get_dem import tile_xy, URL, UA                                                   # noqa: E402

C = (36.15, 137.85); HALF = 60.0; STEP = .12                                        # 中心、±60 km、120 m ごと
Z = 11
cache = {}


def tile(x, y):
    if (x, y) not in cache:
        with urllib.request.urlopen(urllib.request.Request(URL.format(z=Z, x=x, y=y), headers=UA), timeout=60) as r:
            a = np.asarray(Image.open(io.BytesIO(r.read())).convert("RGB"), np.float32)
        cache[(x, y)] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    return cache[(x, y)]


def sample(lat, lon):
    n = 2 ** Z; tx = (lon + 180) / 360 * n; ty = (1 - np.arcsinh(np.tan(np.radians(lat))) / math.pi) / 2 * n
    out = np.zeros(lat.shape, np.float32); ix, iy = np.floor(tx).astype(int), np.floor(ty).astype(int)
    for (x, y) in set(zip(ix.ravel().tolist(), iy.ravel().tolist())):
        m = (ix == x) & (iy == y); T = tile(x, y); px = ((tx[m] - x) * 256).astype(int).clip(0, 255); py = ((ty[m] - y) * 256).astype(int).clip(0, 255); out[m] = T[py, px]
    return out


xs = np.arange(-HALF, HALF + 1e-6, STEP); X, Y = np.meshgrid(xs, xs[::-1])
lat, lon = P.unlocal(X, Y, *C); now = sample(lat, lon)
jx, jy = P.local(lat, lon, *P.ALPS) if False else (None, None)
x, y = (np.radians(lon - P.ALPS[1]) * P.R * np.cos(np.radians(P.ALPS[0])), np.radians(lat - P.ALPS[0]) * P.R)
hx, hy = x * P.c + y * P.s, -x * P.s + y * P.c; hx += P.M[0]; hy += P.M[1]; hla, hlo = P.unlocal(hx, hy, *P.ref)
cache.clear(); new = sample(hla, hlo)
np.save(HERE / "dem" / "town_now.npy", np.maximum(now, 0)); np.save(HERE / "dem" / "town_new.npy", np.maximum(new, 0))
mat = (36.238, 137.972); mx, my = P.local(*mat, *C)
(HERE / "dem" / "town.json").write_text(json.dumps({"center": C, "half_km": HALF, "step_km": STEP, "matsumoto_km": [mx, my], "now_max": float(now.max()), "new_max": float(new.max())}), encoding="utf-8")
print("now max", now.max(), "new max", new.max(), "matsumoto", round(mx, 1), round(my, 1), "now at matsumoto", float(sample(np.array([mat[0]]), np.array([mat[1]]))[0]))
