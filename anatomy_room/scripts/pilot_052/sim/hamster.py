#!/usr/bin/env python3
"""pilot_052「ハムスターの回し車で、東京の電気をまかなうには何匹？」の計算（もしも設計）。
値の出典・確認方法は ../fact_check.md。出典のない値は「仮定」。結果は hamster.json と results.md。
    python hamster.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---- 元の値
M = 0.12              # ハムスターの体重 kg（ゴールデンハムスターの目安、仮定）
V_KMH = 1.56          # 走り続けられる速さ km/h（持久走の訓練をしたゴールデンハムスターの研究、検索の要約）
DIST_KM = 9.0         # 1 晩に走る距離 km（Wikipedia「hamster wheel」、検索の要約）
EFF_MUSCLE = 0.25     # 筋肉の効率（仮定。哺乳類の目安）
EFF_GEN = 0.70        # 小さな発電機の効率（仮定）
BULB_W = 2.5 * 0.3    # 豆電球 2.5 V・0.3 A（よくある豆電球の規格、目安）
HOUSE_KWH_Y = 4008    # 1 世帯の年間の電気（環境省「家庭部門の CO2 排出実態統計調査」令和 7 年度、検索の要約）
TOWN_HOUSES = 4000    # 人口 1 万人ほどの町の世帯数（仮定）
TOKYO_KWH_Y = 780e8   # 東京都の年間の電力消費量（東京都環境局の推計 2024 年度 約 780 億 kWh、検索の要約）
CAGE_M2 = 0.3 * 0.3   # 回し車 1 台を置く広さ（仮定）
SHIKOKU_KM2 = 18802   # 四国 4 県の面積（国土地理院、検索の要約）
FOOD_G = 10           # 1 日に食べる量 g（目安、仮定）


def main():
    v = V_KMH / 3.6
    # 走るのに使うエネルギー（Taylor・Heglund・Maloiy 1982 の式の、速さに比例する部分）W/kg → W
    run_metab = 10.7 * M ** -0.316 * v * M
    p_mech = run_metab * EFF_MUSCLE                  # 走りに上乗せして回し車を回せる仕事（仮定：走りに使う分の効率 25%）
    p_elec = p_mech * EFF_GEN                         # 発電機から出る電気 W（1 匹、走っている間）
    hours = DIST_KM / V_KMH                           # 1 日に走る時間
    wh_day = p_elec * hours                           # 1 匹が 1 日に作る電気 Wh
    house_wh_day = HOUSE_KWH_Y * 1000 / 365
    tokyo_wh_day = TOKYO_KWH_Y * 1000 / 365
    n = dict(
        bulb=BULB_W / p_elec,                         # 豆電球を「同時に」つけるのに要る匹数（走っている間）
        house=house_wh_day / wh_day,                  # 家 1 軒の 1 日分（電池にためて使う）
        town=TOWN_HOUSES * house_wh_day / wh_day,     # 町の家ぜんぶ
        tokyo=tokyo_wh_day / wh_day,                  # 東京都ぜんぶ
    )
    area_km2 = n["tokyo"] * CAGE_M2 / 1e6
    out = dict(mass_kg=M, speed_kmh=V_KMH, dist_km=DIST_KM, run_metab_w=run_metab, p_mech_w=p_mech, p_elec_w=p_elec, hours=hours, wh_day=wh_day,
               house_wh_day=house_wh_day, tokyo_wh_day=tokyo_wh_day, n=n, area_km2=area_km2, area_vs_shikoku=area_km2 / SHIKOKU_KM2,
               food_t_day=n["tokyo"] * FOOD_G / 1e6, bulb_w=BULB_W)
    (HERE / "hamster.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = ["# pilot_052 計算の結果（hamster.py）", "",
             f"- 走るのに使うエネルギー：{run_metab:.2f} W → 回し車を回す仕事 {p_mech:.3f} W → 電気 **{p_elec:.3f} W**（1 匹、走っている間）",
             f"- 1 日に走る時間：{hours:.1f} 時間 → 1 匹が 1 日に作る電気：**{wh_day:.2f} Wh**",
             f"- 豆電球（{BULB_W:.2f} W）を同時につける：**{n['bulb']:.1f} 匹**",
             f"- 家 1 軒の 1 日分（{house_wh_day / 1000:.1f} kWh）：**{n['house']:,.0f} 匹**",
             f"- 町（家 {TOWN_HOUSES:,} 軒）：**{n['town']:,.0f} 匹**",
             f"- 東京都（1 日 {tokyo_wh_day / 1e9:.0f} 百万 kWh）：**{n['tokyo']:,.0f} 匹**（約 {n['tokyo'] / 1e8:,.0f} 億匹）",
             f"- 回し車を並べる広さ：{area_km2:,.0f} km²（四国の {area_km2 / SHIKOKU_KM2:.2f} 倍）",
             f"- えさ：1 日 {out['food_t_day']:,.0f} トン"]
    (HERE / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
