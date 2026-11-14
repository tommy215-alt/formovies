#!/usr/bin/env python3
"""pilot_054「全人類が渋谷のスクランブル交差点に集まったら？」の計算（新もしも設計）。
渋谷のスクランブル交差点を中心に、陸の上だけに人を並べていく（1 m² に 2 人）。近い陸から順に埋め、何人でどこまで届くかを出す。
地図は Natural Earth 10m（パブリックドメイン）の陸と都県の境。100 m の格子で数える。
    python crowd.py → crowd.json・results.md、地図の画像 ../../../production/pilot_054/assets/map/land.png・pref.png
"""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
MAP = HERE.parents[2] / "production" / "pilot_054" / "assets" / "map"
LAT0, LON0 = 35.6595, 139.7005          # 渋谷のスクランブル交差点
WORLD = 8.2e9                           # 世界の人口 約 82 億（国連 WPP2024：2024 年 8.2 億人の 10 倍…＝8.2 billion）
JAPAN = 1.22811e8                       # 日本の総人口 1 億 2281 万 1 千人（総務省 人口推計 2026-03-01 確定値）
SHIBUYA_KU = 15.11                      # km² 渋谷区（国土地理院 令和8年7月1日）
TOKYO = 2199.94                         # km² 東京都（同、境界未定を含む参考値）
DENS = 2.0                              # 人/m²（英国のイベントの安全の目安。4 人を超えると押しつぶしの危険）
HALF, RES = 80.0, .1                    # 中心から ±80 km、100 m の格子
N = int(2 * HALF / RES)
KX = 111.320 * math.cos(math.radians(LAT0)); KY = 110.574


def xy(lon, lat):   # km（東・北）→ 画像の座標
    return ((lon - LON0) * KX + HALF) / RES, (HALF - (lat - LAT0) * KY) / RES


def polys(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    return geom["coordinates"] if geom["type"] == "MultiPolygon" else []


def near(ring):
    return any(abs(lo - LON0) < 1.6 and abs(la - LAT0) < 1.3 for lo, la in ring[::5] + ring[-1:])


def main():
    land = Image.new("L", (N, N), 0); d = ImageDraw.Draw(land)
    for f in json.load(open(MAP / "ne_10m_land.geojson", encoding="utf-8"))["features"]:
        for p in polys(f["geometry"]):
            if near(p[0]):
                d.polygon([xy(*c) for c in p[0]], fill=255)
                for h in p[1:]:
                    d.polygon([xy(*c) for c in h], fill=0)
    pref = Image.new("L", (N, N), 0); dp = ImageDraw.Draw(pref); names = {}
    for f in json.load(open(MAP / "ne_10m_admin_1_states_provinces.geojson", encoding="utf-8"))["features"]:
        if f["properties"].get("adm0_a3") != "JPN":
            continue
        for p in polys(f["geometry"]):
            if near(p[0]):
                dp.line([xy(*c) for c in p[0]], fill=255, width=3)
                names[f["properties"].get("name_ja") or f["properties"]["name"]] = 1
    m = np.array(land) > 127
    yy, xx = np.mgrid[0:N, 0:N]; dist = np.hypot((xx + .5) * RES - HALF, (yy + .5) * RES - HALF)
    dl = np.sort(dist[m]); cum = np.arange(1, len(dl) + 1) * RES * RES            # 近い陸から足した面積 km²
    def r_for(people):
        a = people / DENS / 1e6; i = min(len(cum) - 1, np.searchsorted(cum, a)); return float(dl[i]), a
    out = {"dens": DENS, "world": WORLD, "japan": JAPAN, "tokyo_km2": TOKYO, "half_km": HALF, "res_km": RES}
    for k, n in (("shibuya", SHIBUYA_KU * 1e6 * DENS), ("japan", JAPAN), ("world", WORLD)):
        r, a = r_for(n); out[k] = {"people": n, "area_km2": a, "radius_km": r}
    out["world_vs_tokyo"] = out["world"]["area_km2"] / TOKYO
    out["japan_share"] = JAPAN / WORLD
    # 半径ごとの人数（映像の数を数える表）
    rs = np.linspace(0, out["world"]["radius_km"], 121)
    out["curve"] = [[float(r), float(np.searchsorted(dl, r) * RES * RES * 1e6 * DENS)] for r in rs]
    # 町までの距離（渋谷のスクランブル交差点から、まっすぐ。座標は各駅の目安）
    towns = {"横浜": (139.6223, 35.4657), "大宮": (139.6239, 35.9064), "千葉": (140.1233, 35.6131), "八王子": (139.3389, 35.6556), "成田空港": (140.3864, 35.7720)}
    out["towns"] = {k: {"km": math.hypot((lo - LON0) * KX, (la - LAT0) * KY), "x": (lo - LON0) * KX, "y": (la - LAT0) * KY} for k, (lo, la) in towns.items()}
    (HERE / "crowd.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    land.save(MAP / "land.png"); pref.save(MAP / "pref.png")
    W = out["world"]; J = out["japan"]; S = out["shibuya"]
    L = ["# pilot_054 計算の結果（crowd.py）", "",
         f"- 1 m² に {DENS:.0f} 人。陸の上だけに、交差点から近い順に並べる（100 m の格子、Natural Earth 10m の陸）",
         f"- 渋谷区（{SHIBUYA_KU} km²）に {S['people'] / 1e4:,.0f} 万人（交差点から半径 約 {S['radius_km']:.1f} km の陸）",
         f"- 日本の全員 {JAPAN / 1e8:.3f} 億人 → {J['area_km2']:.1f} km²（半径 約 {J['radius_km']:.1f} km）＝ 世界の {out['japan_share'] * 100:.1f}%",
         f"- 全人類 {WORLD / 1e8:.0f} 億人 → {W['area_km2']:,.0f} km² ＝ 東京都（{TOKYO:,.0f} km²）の {out['world_vs_tokyo']:.2f} 倍、陸だけで半径 約 {W['radius_km']:.1f} km",
         "- 町までの距離：" + "、".join(f"{k} {v['km']:.0f} km" for k, v in out["towns"].items())]
    (HERE / "results.md").write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L)); print(list(names)[:12])


if __name__ == "__main__":
    main()
