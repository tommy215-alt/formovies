"""計算の結果を、表（results.md）と地図の画像（maps/）にまとめる。

使い方：python report.py base roam ...（2 日までは macro_<名>.npz、その先は coarse_<名>.npz）
"""
import os, sys
import numpy as np
from PIL import Image
from build_grid import latlon_rc

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "maps")
os.makedirs(OUT, exist_ok=True)
FINE_OF = {"close": "base"}
K = 8


def fmt(n):
    n = float(n)
    if n >= 1e8:
        return f"{n/1e8:.2f} 億"
    if n >= 1e4:
        return f"{n/1e4:,.1f} 万"
    return f"{n:,.0f}"


def htxt(m):
    if m < 60:
        return f"{m:.0f} 分"
    if m < 2880:
        return f"{m/60:.1f} 時間"
    return f"{m/1440:.1f} 日"


def micro_table():
    rows = np.load(os.path.join(D, "micro.npz"))["rows"]
    lines = ["| 経過 | ゾンビ（かまれて変わる途中を含む） | かまれた人（累計） | 着いた警察官（倒した数） | 都庁からの広がり |", "|---|---|---|---|---|"]
    for sec in (10, 30, 60, 90, 120, 180, 240, 300, 420, 600):
        r = rows[np.argmin(abs(rows[:, 0] - sec))]
        lab = htxt(sec / 60) if sec >= 60 else f"{sec} 秒"
        lines.append(f"| {lab} | {fmt(r[1] + r[2])} | {fmt(r[3] + r[4])} | {r[5]:.0f}（{r[6]:.1f}） | {r[9]:,.0f} m |")
    return "\n".join(lines)


def load(name):
    fine = np.load(os.path.join(D, f"macro_{FINE_OF.get(name, name)}.npz"), allow_pickle=True)
    co = np.load(os.path.join(D, f"coarse_{name}.npz"), allow_pickle=True)
    rows = np.vstack([fine["rows"], co["rows"]])
    return fine, co, rows, float(fine["pop0"])


def macro_table(name):
    fine, co, rows, pop0 = load(name)
    lines = [f"計算の範囲の人口 {fmt(pop0)} 人", "",
             "| 経過 | ゾンビ | ゾンビのいる範囲 | 生き残っている人 | うち建物に籠城 | 自衛隊の隊員（倒したゾンビ） |", "|---|---|---|---|---|---|"]
    for mins in (30, 60, 180, 360, 720, 1440, 2880, 4320, 7 * 1440, 8 * 1440, 10 * 1440, 14 * 1440, 21 * 1440,
                 22 * 1440, 30 * 1440, 45 * 1440, 60 * 1440, 90 * 1440):
        if mins > rows[-1, 0] + 1:
            break
        r = rows[np.argmin(abs(rows[:, 0] - mins))]
        lines.append(f"| {htxt(mins)} | {fmt(r[1])} | {fmt(r[2])} km² | {fmt(r[3])} | {fmt(r[5] + r[6])} | {fmt(r[11])}（{fmt(r[12])}） |")
    arr = sorted(((k, float(v)) for k, v in co["arrive"]), key=lambda x: x[1])
    lines += ["", "着いた時刻：" + "、".join(f"{k} {htxt(v)}" for k, v in arr)]
    lk = [(n, float(t)) for n, t, _ in co["links"]]
    lines.append("海峡を渡った時刻：" + "、".join(f"{n} {htxt(t) if t > 0 else '90 日までに渡らない'}" for n, t in lk))
    return "\n".join(lines)


def render(z, ld, pn, path, scale):
    img = np.zeros(z.shape + (3,), np.uint8)
    lit = np.clip(np.log10(pn + 1) / 4.5, 0, 1)
    img[..., 0] = np.where(ld, 38 + 60 * lit, 12); img[..., 1] = np.where(ld, 44 + 70 * lit, 16); img[..., 2] = np.where(ld, 54 + 90 * lit, 26)
    zi = np.clip(np.log10(z + 1) / 4.5, 0, 1); m = z >= 1
    img[m, 0] = (150 + 105 * zi[m]).astype(np.uint8); img[m, 1] = (30 + 20 * zi[m]).astype(np.uint8); img[m, 2] = 40
    Image.fromarray(img[::-1]).resize((z.shape[1] * scale, z.shape[0] * scale), Image.NEAREST).save(path)


def maps(name):
    fine, co, _, _ = load(name)
    g = np.load(os.path.join(D, "grid.npz")); land = g["land"]; night = g["night"]
    regions = {"kanto": (((35.0, 138.6), (36.5, 140.9)), 2), "japan": (((31.0, 129.5), (45.5, 146.0)), 1)}
    layers = [(k[2:] + "h", fine[k]) for k in fine.files if k.startswith("Z_")]
    for k in co.files:
        if k.startswith("Z_"):
            layers.append((k[2:], np.kron(co[k], np.ones((K, K), np.float32)) / (K * K)))
    for key, zfull in layers:
        for rg, ((la0, lo0), (la1, lo1)), sc in [(r, *v) for r, v in regions.items()]:
            r0, c0 = latlon_rc(la0, lo0); r1, c1 = latlon_rc(la1, lo1)
            z = np.zeros(land.shape, np.float32); z[:zfull.shape[0], :zfull.shape[1]] = zfull
            render(z[r0:r1, c0:c1], land[r0:r1, c0:c1], night[r0:r1, c0:c1], os.path.join(OUT, f"{name}_{rg}_{key}.png"), sc)


if __name__ == "__main__":
    names = sys.argv[1:] or ["base"]
    parts = ["# 計算の結果（自動で作る：python report.py " + " ".join(names) + "）", "",
             "2 日までは 1 km メッシュ（最初の 10 分は 25 m）、3 日目からは 8 km のブロックのざっくりした計算。", "",
             "## 最初の 10 分（25 m のマス）", "", micro_table(), ""]
    for nm in names:
        parts += [f"## シナリオ {nm}", "", macro_table(nm), ""]
        maps(nm)
    open(os.path.join(HERE, "results.md"), "w", encoding="utf-8").write("\n".join(parts))
    print("\n".join(parts))
