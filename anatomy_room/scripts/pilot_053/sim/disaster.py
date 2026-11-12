#!/usr/bin/env python3
"""pilot_053「日本の観測史上最大の記録が、東京で同時に起きたら？」の計算（もしも設計）。
記録は気象庁「歴代全国ランキング」（本文で確認、../fact_check.md）。計算の式と仮定も fact_check.md。
    python disaster.py → disaster.json・results.md
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---- 観測史上 1 位（気象庁）
T_MAX = 41.8          # ℃ 伊勢崎 2025-08-05
SNOW = 11.82          # m 最深積雪 伊吹山 1927-02-14
R_1H = 153.0          # mm 1 時間降水量 香取 1999-10-27
R_DAY = 922.5         # mm 日降水量 箱根 2019-10-12
U = 72.5              # m/s 最大風速 富士山 1942-04-05
U_GUST = 91.0         # m/s 最大瞬間風速 富士山 1966-09-25
# ---- 仮定・基準
RHO_SNOW = 400.       # kg/m³ 深く積もって締まった雪の密度（仮定）
CH = .003             # 熱が風で運ばれる係数（バルク輸送係数、目安）
RHO_AIR, CP_AIR = 1.2, 1005.
LF = 334000.          # J/kg 氷がとける熱
CW = 4186.            # J/kg/K 水の比熱
SEWER = 50.           # mm/h 東京の下水道が流せる雨（区部の計画、目安 50〜75）
SNOW_UNIT = 20.       # N/m²/cm 建築基準法の積雪の単位荷重（一般の地域）
TOKYO_SNOW_DESIGN = 30.  # cm 東京の垂直積雪量（建築の基準、目安）
V0_TOKYO = 34.        # m/s 東京の基準風速（建築の基準）


def main():
    swe = SNOW * RHO_SNOW / 1000                                  # 雪をとかした水の深さ m
    h_air = RHO_AIR * CP_AIR * CH * U * T_MAX                     # 暑い風が雪に運ぶ熱 W/m²
    h_rain = R_1H / 1000 / 3600 * 1000 * CW * T_MAX               # 41.8℃の雨が運ぶ熱 W/m²
    melt_mm_h = (h_air + h_rain) / LF * 3600                      # 1 時間にとける水 mm
    hours_melt = swe * 1000 / melt_mm_h
    water_in = swe * 1000 + R_DAY                                 # 1 日にたまる水 mm（雪どけ＋雨）
    water_left = water_in - SEWER * 24
    roof = SNOW * 100 * SNOW_UNIT                                 # N/m²
    roof_design = TOKYO_SNOW_DESIGN * SNOW_UNIT
    q = .5 * RHO_AIR * U ** 2; q_g = .5 * RHO_AIR * U_GUST ** 2; q0 = .5 * RHO_AIR * V0_TOKYO ** 2
    out = dict(swe_m=swe, h_air=h_air, h_rain=h_rain, melt_mm_h=melt_mm_h, hours_melt=hours_melt, inflow_mm_h=melt_mm_h + R_1H,
               water_in_mm=water_in, water_left_m=water_left / 1000, roof_n=roof, roof_t=roof / 9.8 / 1000, roof_ratio=roof / roof_design,
               q=q, q_gust=q_g, q_ratio=q / q0, q_gust_ratio=q_g / q0, snow_floors=SNOW / 3.0)
    (HERE / "disaster.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["# pilot_053 計算の結果（disaster.py）", "",
         f"- 雪 11.82 m：建物の約 {SNOW / 3.0:.1f} 階分。とかすと水 {swe:.1f} m",
         f"- 屋根の雪の重さ：1 m² に約 {roof / 9.8 / 1000:.1f} トン（建築基準法の単位荷重）＝東京の基準の {roof / roof_design:.0f} 倍",
         f"- 41.8℃・風 72.5 m/s が雪に運ぶ熱 {h_air:,.0f} W/m²、41.8℃の雨 153 mm/h が運ぶ熱 {h_rain:,.0f} W/m²",
         f"- 雪がとける速さ：1 時間に {melt_mm_h:.0f} mm（水）→ 全部とけるまで 約 {hours_melt:.0f} 時間",
         f"- 雪どけ＋雨：1 時間に {melt_mm_h + R_1H:.0f} mm（下水道が流せるのは {SEWER:.0f} mm）",
         f"- 1 日の水：雪どけ {swe * 1000:,.0f} mm＋雨 {R_DAY} mm ＝ {water_in:,.0f} mm、下水道が流して残るのは 約 {water_left / 1000:.1f} m",
         f"- 風の力：平均 72.5 m/s で建物の基準の {q / q0:.1f} 倍、瞬間 91.0 m/s で {q_g / q0:.1f} 倍"]
    (HERE / "results.md").write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))


if __name__ == "__main__":
    main()
