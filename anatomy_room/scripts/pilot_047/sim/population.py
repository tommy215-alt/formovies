# pilot_047：日ごとの「被害の範囲に住む人」（正午なので昼間人口）。
# 人口は pilot_045 の格子（scripts/pilot_045/sim/data/grid.npz、令和 2 年国勢調査の 1 km メッシュと昼間人口の推定）。
# python population.py（先に impact.py）→ days.json に人数を足し、results_pop.md を作る
import json, math
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
GRID = HERE.parents[1] / "pilot_045" / "sim" / "data" / "grid.npz"
ROW0, COL0 = 46 * 80, 28 * 80                  # pilot_045 build_grid.py と同じ
TOCHO = (35.68950, 139.69170)                  # 東京都庁
WORLD = 8.2e9                                  # 世界の人口（2025 年ごろ、国連の推計。fact_check.md）
R_E = 6371.0

# 被害の段階（impact.py の距離）
LEVELS = [("bldg_km", "ビルが崩れる"), ("wood_km", "木造が倒れる"), ("glass_km", "窓ガラスが割れる"),
          ("glass_may_km", "窓が割れるかも")]


def main():
    g = np.load(GRID)
    pop = g["day"].astype(np.float64)
    nr, nc = pop.shape
    lat = (np.arange(nr) + ROW0 + 0.5) / 120.0
    lon = (np.arange(nc) + COL0 + 0.5) / 80.0 + 100.0
    la, lo = np.meshgrid(np.radians(lat), np.radians(lon), indexing="ij")
    p0, l0 = math.radians(TOCHO[0]), math.radians(TOCHO[1])
    a = np.sin((la - p0) / 2) ** 2 + np.cos(la) * math.cos(p0) * np.sin((lo - l0) / 2) ** 2
    dist = 2 * R_E * np.arcsin(np.sqrt(a))
    japan = pop.sum()
    order = np.argsort(dist, axis=None)
    cum = np.cumsum(pop.ravel()[order])
    dsorted = dist.ravel()[order]

    def within(km):
        if km <= 0:
            return 0.0
        i = np.searchsorted(dsorted, km, side="right")
        return float(cum[i - 1]) if i else 0.0

    days = json.loads((HERE / "days.json").read_text(encoding="utf-8"))
    rows = ["# pilot_047 被害の範囲に住む人（population.py が作る）", "",
            f"正午の昼間人口（pilot_045 の格子、日本の合計 {japan/1e4:,.0f} 万人）。都庁からの距離の円の中の人数。",
            "「被害の範囲」は窓ガラスが割れる（6.9 kPa、Collins ほか 2005 の基準）より内側。死者数ではない。",
            "日本全体が入ったあと、爆風が地球全体（半周 20,000 km）に届いた日から世界の人口にする。", "",
            "| 日 | ビルが崩れる | 木造が倒れる | 窓ガラスが割れる（被害の範囲） | 窓が割れるかも | 画面の数 |",
            "|---|---|---|---|---|---|"]
    for d in days:
        cnt = {k: within(d[k]) for k, _ in LEVELS}
        d["pop"] = cnt
        if d["glass_km"] >= 20000:
            shown, label = WORLD, "全人類"
        elif cnt["glass_km"] >= japan * 0.9999:
            shown, label = japan, "日本全体"
        else:
            shown, label = cnt["glass_km"], ""
        d["shown_pop"], d["shown_label"] = shown, label
        man = lambda x: "—" if x < 1 else (f"{x:,.0f} 人" if x < 1e4 else f"{x/1e4:,.0f} 万人")
        rows.append(f"| {d['day']} | {man(cnt['bldg_km'])} | {man(cnt['wood_km'])} | {man(cnt['glass_km'])} | "
                    f"{man(cnt['glass_may_km'])} | {label or man(shown)} |")
    (HERE / "days.json").write_text(json.dumps(days, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "results_pop.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("\n".join(rows[6:]))


if __name__ == "__main__":
    main()
