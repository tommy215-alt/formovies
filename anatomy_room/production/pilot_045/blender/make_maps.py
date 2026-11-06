"""計算の結果（scripts/pilot_045/sim/data）から、Blender の地図の素材（PNG）を作る。→ work/maps/

人の光：1 km メッシュの人口を、人数に比例した小さな光の点にばらまく（夜景のように見える）。
ゾンビ：同じくゾンビの数に比例した赤い点。時刻ごとに 1 枚（log の明るさ）。Blender で 2 枚を混ぜて動かす。
  city …… 新宿（最初の 10 分、25 m のマス、16 km 四方）
  kanto … 関東（2 日まで 1 km、3 日目からは 8 km のブロックをなめらかに）
  japan … 日本（同じ）
範囲（Blender の平面の大きさ）は maps.json。座標は都庁前（35.6893, 139.6920）が原点、x が東、y が北（m）。
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(HERE, "..", "..", "..", "scripts", "pilot_045", "sim")
sys.path.insert(0, SIM)
from build_grid import latlon_rc, ROW0, COL0  # noqa: E402

OUT = os.path.join(HERE, "..", "work", "maps")
os.makedirs(OUT, exist_ok=True)
D = os.path.join(SIM, "data")
LAT0, LON0 = 35.6893, 139.6920
KX = 111320 * math.cos(math.radians(LAT0)); KY = 110950
rng = np.random.default_rng(45)


def box(a, r):
    if r < 1:
        return a
    k = 2 * r + 1
    p = np.pad(a, r, mode="edge")
    c = np.cumsum(p, 0); c = np.vstack([np.zeros((1, c.shape[1])), c]); a = (c[k:] - c[:-k]) / k
    c = np.cumsum(a, 1); c = np.hstack([np.zeros((c.shape[0], 1)), c]); return (c[:, k:] - c[:, :-k]) / k


def blur(a, r):
    return box(box(box(a, r), r), r)


def dots(cnt, lat_of, lon_of, region, size, per_dot, jitter_deg):
    """cnt[i]：人数、lat_of/lon_of：その点の中心。region=(lat0, lat1, lon0, lon1)、size：画像の幅と高さ。人数 per_dot ごとに 1 点"""
    la0, la1, lo0, lo1 = region
    n = np.floor(cnt / per_dot + rng.random(cnt.shape)).astype(int)
    keep = n > 0
    n, la, lo = n[keep], lat_of[keep], lon_of[keep]
    la = np.repeat(la, n) + rng.normal(0, .55, n.sum()) * jitter_deg[0]   # 隣のマスまでなめらかに（1 km の四角を見せない）
    lo = np.repeat(lo, n) + rng.normal(0, .55, n.sum()) * jitter_deg[1]
    W, H = size
    x = ((lo - lo0) / (lo1 - lo0) * W).astype(int); y = ((la1 - la) / (la1 - la0) * H).astype(int)
    ok = (x >= 0) & (x < W) & (y >= 0) & (y < H)
    img = np.zeros((H, W), np.float32)
    np.add.at(img, (y[ok], x[ok]), 1.0)
    return img


def mesh_centers():
    g = np.load(os.path.join(D, "grid.npz"))
    r, c = np.mgrid[0:g["night"].shape[0], 0:g["night"].shape[1]]
    lat = (r + ROW0 + .5) / 120.0; lon = (c + COL0 + .5) / 80.0 + 100
    return g, lat, lon


def save_gray(a, path, gamma=1.0):
    Image.fromarray((np.clip(a, 0, 1) ** gamma * 255).astype(np.uint8)).save(path)


def region_info(region, size):
    la0, la1, lo0, lo1 = region
    return {"x0": (lo0 - LON0) * KX, "x1": (lo1 - LON0) * KX, "y0": (la0 - LAT0) * KY, "y1": (la1 - LAT0) * KY, "w": size[0], "h": size[1]}


def big_maps(name, region, size, per_dot_pop, per_dot_z, blur_r, coarse_blur):
    g, lat, lon = mesh_centers()
    la0, la1, lo0, lo1 = region
    r0, c0 = latlon_rc(la0, lo0); r1, c1 = latlon_rc(la1, lo1)
    sl = (slice(r0, r1 + 1), slice(c0, c1 + 1))
    jit = (1 / 120, 1 / 80)
    land = g["land"][sl].astype(np.float32)
    # 陸地（なめらかに拡大）
    L = np.array(Image.fromarray((land[::-1] * 255).astype(np.uint8)).resize(size, Image.BICUBIC), np.float32) / 255
    save_gray(blur(L, 5), os.path.join(OUT, f"{name}_land.png"))
    pop = g["night"][sl].astype(np.float64)
    P = dots(pop.ravel(), lat[sl].ravel(), lon[sl].ravel(), region, size, per_dot_pop, jit)
    P = np.log1p(blur(P, blur_r) * 8) / math.log1p(8 * 3)
    save_gray(P, os.path.join(OUT, f"{name}_pop.png"))
    keys = []
    fine = np.load(os.path.join(D, "macro_base.npz"), allow_pickle=True)
    co = np.load(os.path.join(D, "coarse_base.npz"), allow_pickle=True)
    layers = [(k[2:] + "h", fine[k][sl]) for k in fine.files if k.startswith("Z_")]
    for k in co.files:
        if k.startswith("Z_"):
            z = np.kron(co[k], np.ones((8, 8), np.float32)) / 64
            full = np.zeros(g["land"].shape, np.float32); full[:z.shape[0], :z.shape[1]] = z
            full = blur(full, coarse_blur) * g["land"]   # 8 km のブロックの角を消す
            layers.append((k[2:], full[sl]))
    for key, z in layers:
        # ゾンビの密度（1 km² あたり、log）をなめらかに広げ、街の光の点で模様を付ける（人の多い所ほど明るい赤）
        f = np.clip(np.log10(np.maximum(z, 0) / 1.045 + 1) / math.log10(3000), 0, 1).astype(np.float32)
        F = np.array(Image.fromarray(f[::-1]).resize(size, Image.BICUBIC), np.float32).clip(0, 1)
        Zt = F * (.5 + .5 * np.clip(P * 1.4, 0, 1))
        save_gray(Zt, os.path.join(OUT, f"{name}_z_{key}.png")); keys.append(key)
    return region_info(region, size), keys


def city_maps():
    m = np.load(os.path.join(D, "micro.npz"))
    N, DX = 640, 25.0
    half = N * DX / 2
    size = (2560, 2560)
    keys = []
    yy, xx = np.mgrid[0:N, 0:N]
    for k in m.files:
        if not k.startswith("Z_"):
            continue
        z = (m[k] + m["E_" + k[2:]]).astype(np.float64)
        # セルの中心（x 東・y 北、m）→ 画像
        cx = (xx + .5) * DX - half; cy = (yy + .5) * DX - half
        n = np.floor(z.ravel() + rng.random(z.size)).astype(int); keep = n > 0
        px = np.repeat(cx.ravel()[keep], n[keep]) + (rng.random(n.sum()) - .5) * DX
        py = np.repeat(cy.ravel()[keep], n[keep]) + (rng.random(n.sum()) - .5) * DX
        ix = ((px + half) / (2 * half) * size[0]).astype(int); iy = ((half - py) / (2 * half) * size[1]).astype(int)
        ok = (ix >= 0) & (ix < size[0]) & (iy >= 0) & (iy < size[1])
        img = np.zeros(size[::-1], np.float32); np.add.at(img, (iy[ok], ix[ok]), 1.0)
        img = np.log1p(blur(img, 1) * 4) / math.log1p(4 * 2)
        save_gray(img, os.path.join(OUT, f"city_z_{k[2:]}.png")); keys.append(k[2:])
    # 昼間人口の濃さ（建物の高さに使う）
    pop = np.zeros((N, N))
    g = np.load(os.path.join(D, "grid.npz"))["day"]
    for a in range(N):
        la = LAT0 + ((a + .5) * DX - half) / KY
        for b in range(0, N, 8):
            lo = LON0 + ((b + .5) * DX - half) / KX
            r, c = latlon_rc(la, lo); pop[a, b:b + 8] = g[r, c]
    np.save(os.path.join(OUT, "city_daypop.npy"), pop.astype(np.float32))
    return {"x0": -half, "x1": half, "y0": -half, "y1": half, "w": size[0], "h": size[1]}, keys


if __name__ == "__main__":
    info = {}
    info["city"], kc = city_maps(); info["city"]["keys"] = kc
    info["kanto"], kk = big_maps("kanto", (34.6, 37.2, 138.2, 141.3), (4096, 4096), 25, 25, 1, 6); info["kanto"]["keys"] = kk
    info["japan"], kj = big_maps("japan", (30.7, 45.6, 128.05, 146.5), (4096, 4096), 250, 250, 1, 4); info["japan"]["keys"] = kj
    json.dump(info, open(os.path.join(OUT, "maps.json"), "w"), indent=1)
    print(json.dumps({k: (v["keys"], round(v["x1"] - v["x0"]), round(v["y1"] - v["y0"])) for k, v in info.items()}, ensure_ascii=False))
