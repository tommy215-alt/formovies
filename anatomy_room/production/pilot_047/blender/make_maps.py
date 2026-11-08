"""地図の素材（PNG）を作る → work/maps/。pilot_047（毎日2倍の隕石）。

都庁を中心にした正距方位図法（中心からの距離と向きが正しい）。被害の円（都庁からの距離）が地図の上でそのまま円になる。
  land … 陸地（Natural Earth 10m の陸地、パブリックドメイン。pilot_045 の data/ne_10m_land.geojson）
  pop  … 住む人の光（令和 2 年国勢調査の 1 km メッシュの常住人口〔pilot_045 の格子〕＋沖縄などの南の島の点。人数に比例した光の点）
範囲：kanto ±200 km、japan ±2,300 km（石垣島・与那国島まで）。座標は都庁が原点、x が東、y が北（m）。maps.json に大きさ。
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "..")
D45 = os.path.join(ROOT, "scripts", "pilot_045", "sim", "data")
sys.path.insert(0, os.path.join(ROOT, "scripts", "pilot_047", "sim"))
from population import OKINAWA, JAPAN_CENSUS, ROW0, COL0, TOCHO  # noqa: E402

OUT = os.path.join(HERE, "..", "work", "maps")
os.makedirs(OUT, exist_ok=True)
R_E = 6371000.0
LAT0, LON0 = map(math.radians, TOCHO)
rng = np.random.default_rng(47)


def fwd(lat, lon):
    """緯度・経度（度）→ 正距方位図法の x（東）, y（北）m"""
    la, lo = np.radians(lat), np.radians(lon)
    c = np.arccos(np.clip(math.sin(LAT0) * np.sin(la) + math.cos(LAT0) * np.cos(la) * np.cos(lo - LON0), -1, 1))
    k = np.where(c > 1e-9, c / np.maximum(np.sin(c), 1e-12), 1.0)
    x = R_E * k * np.cos(la) * np.sin(lo - LON0)
    y = R_E * k * (math.cos(LAT0) * np.sin(la) - math.sin(LAT0) * np.cos(la) * np.cos(lo - LON0))
    return x, y


def inv(x, y):
    """正距方位図法の x, y（m）→ 緯度・経度（度）"""
    rho = np.hypot(x, y); c = rho / R_E
    la = np.arcsin(np.clip(np.cos(c) * math.sin(LAT0) + np.where(rho > 0, y * np.sin(c) * math.cos(LAT0) / np.maximum(rho, 1e-9), 0), -1, 1))
    lo = LON0 + np.arctan2(x * np.sin(c), rho * math.cos(LAT0) * np.cos(c) - y * math.sin(LAT0) * np.sin(c))
    return np.degrees(la), np.degrees(lo)


def box(a, r):
    if r < 1:
        return a
    k = 2 * r + 1
    p = np.pad(a, r, mode="edge")
    c = np.cumsum(p, 0); c = np.vstack([np.zeros((1, c.shape[1])), c]); a = (c[k:] - c[:-k]) / k
    c = np.cumsum(a, 1); c = np.hstack([np.zeros((c.shape[0], 1)), c]); return (c[:, k:] - c[:, :-k]) / k


def blur(a, r):
    return box(box(box(a, r), r), r)


def save_gray(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(path)


# 陸地：緯度・経度の細かい格子（0.01 度）に Natural Earth の多角形を塗る
LA0, LA1, LO0, LO1, RES = 15.0, 62.0, 100.0, 165.0, 0.01


def land_latlon():
    W, H = int((LO1 - LO0) / RES), int((LA1 - LA0) / RES)
    im = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(im)
    gj = json.load(open(os.path.join(D45, "ne_10m_land.geojson"), encoding="utf-8"))
    for ft in gj["features"]:
        g = ft["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            for k, ring in enumerate(poly):
                pts = [((lo - LO0) / RES, (LA1 - la) / RES) for lo, la in ring]
                if max(p[0] for p in pts) < 0 or min(p[0] for p in pts) > W or max(p[1] for p in pts) < 0 or min(p[1] for p in pts) > H:
                    continue
                dr.polygon(pts, fill=0 if k else 255)
    return np.array(im, np.float32) / 255


def people():
    """住む人の点：(人数, 緯度, 経度)。格子の 1 km メッシュ＋南の島"""
    g = np.load(os.path.join(D45, "grid.npz")); pop = g["night"].astype(np.float64)
    r, c = np.nonzero(pop > 0)
    lat = (r + ROW0 + .5) / 120.0; lon = (c + COL0 + .5) / 80.0 + 100.0; n = pop[r, c]
    extra = [(p, la, lo) for _, p, la, lo in OKINAWA]
    rest = JAPAN_CENSUS - pop.sum() - sum(p for p, _, _ in extra)
    extra += [(rest * .8, 28.38, 129.49), (rest * .2, 27.09, 142.19)]   # 奄美と小笠原（残りを大まかに分ける）
    return np.concatenate([n, [e[0] for e in extra]]), np.concatenate([lat, [e[1] for e in extra]]), np.concatenate([lon, [e[2] for e in extra]]), len(extra)


def make(name, half, size, per_dot, jitter_m):
    W = H = size
    xs = (np.arange(W) + .5) / W * 2 * half - half; ys = half - (np.arange(H) + .5) / H * 2 * half
    X, Y = np.meshgrid(xs, ys)
    la, lo = inv(X, Y)
    L = LAND
    ix = ((lo - LO0) / RES).astype(int); iy = ((LA1 - la) / RES).astype(int)
    ok = (ix >= 0) & (ix < L.shape[1]) & (iy >= 0) & (iy < L.shape[0])
    land = np.zeros((H, W), np.float32); land[ok] = L[iy[ok], ix[ok]]
    save_gray(blur(land, 2), os.path.join(OUT, f"{name}_land.png"))
    n, plat, plon, ne = PEOPLE
    k = np.floor(n / per_dot + rng.random(n.shape)).astype(int)
    # 南の島の点はまとめて置いたので、島の大きさ（約 15 km）に散らす
    jit = np.full(len(n), jitter_m); jit[-ne:] = 15000
    px, py = fwd(plat, plon)
    px = np.repeat(px, k) + rng.normal(0, 1, k.sum()) * np.repeat(jit, k); py = np.repeat(py, k) + rng.normal(0, 1, k.sum()) * np.repeat(jit, k)
    jx = ((px + half) / (2 * half) * W).astype(int); jy = ((half - py) / (2 * half) * H).astype(int)
    ok = (jx >= 0) & (jx < W) & (jy >= 0) & (jy < H)
    img = np.zeros((H, W), np.float32); np.add.at(img, (jy[ok], jx[ok]), 1.0)
    img = np.log1p(blur(img, 1) * 8) / math.log1p(8 * 3)
    save_gray(img * (blur(land, 1) > .2), os.path.join(OUT, f"{name}_pop.png"))
    return {"x0": -half, "x1": half, "y0": -half, "y1": half, "w": W, "h": H}


if __name__ == "__main__":
    LAND = land_latlon(); PEOPLE = people()
    info = {"kanto": make("kanto", 200000, 4096, 25, 450), "japan": make("japan", 2300000, 4096, 400, 900)}
    cities = {"横浜": (35.4437, 139.6380), "さいたま": (35.8617, 139.6455), "千葉": (35.6074, 140.1065), "名古屋": (35.1815, 136.9066),
              "大阪": (34.6937, 135.5023), "仙台": (38.2682, 140.8694), "札幌": (43.0618, 141.3545), "福岡": (33.5902, 130.4017),
              "那覇": (26.2124, 127.6809), "石垣島": (24.3448, 124.1572)}
    info["cities"] = {k: [float(v) for v in fwd(*ll)] for k, ll in cities.items()}
    json.dump(info, open(os.path.join(OUT, "maps.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: [round(x / 1000) for x in v] for k, v in info["cities"].items()}, ensure_ascii=False))
