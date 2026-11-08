# pilot_047：人は逃げる（2026-11-09 ユーザー）。日ごとの「避難した人」と「逃げ場のない人」。
# 人口は pilot_045 の格子（scripts/pilot_045/sim/data/grid.npz、令和 2 年国勢調査の 1 km メッシュの常住人口）＋南の島。
# 避難の仮定（この回の仮定。fact_check.md）：
#   - 9 日目に東京中の窓が揺れ、「毎日 2 倍・毎日正午・都庁の真上」と分かる。その日から毎日、
#     次の日の被害の範囲（窓ガラスが割れる 6.9 kPa の円）の中の人が、その外へ避難する。避難は間に合うとする。
#   - 次の日の円が日本の人の住む所をすべて覆ったら、日本に逃げ場はない（海外への避難は考えない）。
#   - 爆風が地球の半周（20,000 km）を超えたら、地球に逃げ場はない。
# python population.py（先に impact.py）→ days.json に足し、results_pop.md を作る
import json, math
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
GRID = HERE.parents[1] / "pilot_045" / "sim" / "data" / "grid.npz"
ROW0, COL0 = 46 * 80, 28 * 80                  # pilot_045 build_grid.py と同じ
TOCHO = (35.68950, 139.69170)                  # 東京都庁
WORLD = 8.232e9                                # 世界の人口（2025 年、国連 World Population Prospects 2024 の中位推計）
R_E = 6371.0
EVAC_FROM = 9                                  # 避難を始める日


JAPAN_CENSUS = 126146099                       # 令和 2 年国勢調査の全国の人口
# pilot_045 の格子は北緯 30.67 度より北だけ。南の島を点で足す（令和 2 年国勢調査、沖縄県の資料）
OKINAWA = [  # (名前, 人口, 緯度, 経度)
    ("沖縄本島と周りの島", 1467480 - 52931 - 1058 - 47637 - 3942 - 1676 - 1285 - 590, 26.21, 127.68),
    ("宮古島・多良間", 52931 + 1058, 24.80, 125.28),
    ("石垣島・竹富・与那国", 47637 + 3942 + 1676, 24.34, 124.16),
    ("大東島", 1285 + 590, 25.85, 131.25),
]


def main():
    g = np.load(GRID)
    # 避難は住む場所から：常住人口（昼間人口の推定は合計が全国の人口より多くなるので使わない）
    grid_pop = g["night"].astype(np.float64)
    nr, nc = grid_pop.shape
    lat = (np.arange(nr) + ROW0 + 0.5) / 120.0
    lon = (np.arange(nc) + COL0 + 0.5) / 80.0 + 100.0
    la, lo = np.meshgrid(lat, lon, indexing="ij")
    m = grid_pop > 0
    rest = JAPAN_CENSUS - grid_pop.sum() - sum(p for _, p, _, _ in OKINAWA)
    pts = OKINAWA + [("奄美・小笠原など（残り）", rest, 28.38, 129.49)]
    pop = np.concatenate([grid_pop[m], [p for _, p, _, _ in pts]])
    la = np.radians(np.concatenate([la[m], [y for _, _, y, _ in pts]]))
    lo = np.radians(np.concatenate([lo[m], [x for _, _, _, x in pts]]))
    p0, l0 = math.radians(TOCHO[0]), math.radians(TOCHO[1])
    a = np.sin((la - p0) / 2) ** 2 + np.cos(la) * math.cos(p0) * np.sin((lo - l0) / 2) ** 2
    dist = 2 * R_E * np.arcsin(np.sqrt(a))
    japan = pop.sum()
    far = dist[pop > 0].max()                  # 人の住む一番遠い所（km）

    def within(km):
        return float(pop[dist <= km].sum()) if km > 0 else 0.0

    def refuge(km):
        """円の外に住む人と、その主な場所（緯度・経度の重心）"""
        m = (dist > km) & (pop > 0)
        if not m.any():
            return 0.0, None
        w = pop[m]
        return float(w.sum()), (float((np.degrees(la[m]) * w).sum() / w.sum()), float((np.degrees(lo[m]) * w).sum() / w.sum()))

    days = json.loads((HERE / "days.json").read_text(encoding="utf-8"))
    man = lambda x: "—" if x < 1 else (f"{x:,.0f}人" if x < 1e4 else (f"{x/1e4:,.0f}万人" if x < 1e8 else f"{x/1e8:,.2f}億人"))
    rows = ["# pilot_047 避難と逃げ場（population.py が作る）", "",
            f"住む人（pilot_045 の格子の常住人口＋沖縄などの南の島、日本の合計 {man(japan)}、人の住む一番遠い所は都庁から {far:,.0f} km）。",
            f"{EVAC_FROM} 日目から毎日、次の日の被害の範囲（窓ガラスが割れる円）の中の人がその外へ避難する（間に合うとする）。", "",
            "| 日 | 被害の範囲（窓ガラス） | その日までに避難した人 | 次の日の円の外（逃げ場）に住む人 | 画面の数 |",
            "|---|---|---|---|---|"]
    for i, d in enumerate(days):
        n = d["day"]
        nxt = days[i + 1]["glass_km"] if i + 1 < len(days) else 20000
        evac = within(d["glass_km"]) if n > EVAC_FROM else 0.0
        if n == EVAC_FROM:
            evac = 0.0
        ref, cen = refuge(nxt)
        d["evacuated"] = evac
        d["refuge_next"] = ref
        d["refuge_center"] = cen
        if d["glass_km"] >= 20000:
            d["counter"] = ("逃げ場のない人", WORLD)
        elif ref == 0 and n >= EVAC_FROM:              # 次の日の円が日本をすべて覆う
            d["counter"] = ("逃げ場のない人", japan)
        elif evac > 0:
            d["counter"] = ("避難した人", evac)
        else:
            d["counter"] = None
        c = d["counter"]
        rows.append(f"| {n} | {d['glass_km']:,.0f} km | {man(evac)} | {man(ref)}"
                    f"{'' if not cen else f'（重心 {cen[0]:.1f}°N {cen[1]:.1f}°E）'} | {c[0] + ' ' + man(c[1]) if c else '—'} |")
    (HERE / "days.json").write_text(json.dumps(days, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "results_pop.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("\n".join(rows[2:]))


if __name__ == "__main__":
    main()
