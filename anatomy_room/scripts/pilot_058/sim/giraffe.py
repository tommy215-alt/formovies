#!/usr/bin/env python3
"""pilot_058「キリンぞりで、南極を横断したら？」の数字。出典と確認方法は ../fact_check.md（pilot_057 の犬ぞりの続き）。
    python giraffe.py → giraffe.json（plan.py が読む）"""
import json, math
from pathlib import Path

ROUTE, DOG_DAYS = 6_000, 220      # 1989–90 国際南極横断隊（pilot_057）
VMAX = 60                         # キリンの最高速 km/h（短い間だけ）
FOOD = 34                         # キリン 1 頭の 1 日のエサ kg（San Diego Zoo「最大 75 ポンド」）
N = 4                             # そりを引くキリン（2 頭ずつ 2 列、演出の仮定）
ZOO_C = 10                        # 動物園で室内に入れる目安 ℃（10〜16℃、検索の要約）
TMIN = -48                        # pilot_057 と同じ
# 横風で倒れるか（仮定つきの計算）：南極の高原（標高 約 2,800 m、−48℃）の空気
P, T = 71_000, 273.15 + TMIN; RHO = P / (287.05 * T)
A, CD, HC = 3.7, 1.0, 2.3         # 横から見た面積 m²、抗力係数、風の力がかかる高さ m（仮定）
M, HALF = 1_200, .25              # 体重 kg（オス）、左右の脚の間の半分 m（仮定）
v_tip = math.sqrt(M * 9.8 * HALF / HC / (.5 * RHO * CD * A))

O = dict(route_km=ROUTE, dog_days=DOG_DAYS, vmax=VMAX, days_at_vmax=ROUTE / VMAX / 24, food=FOOD, n=N,
         food_total_kg=FOOD * N * round(ROUTE / VMAX / 24), zoo_c=ZOO_C, tmin=TMIN, colder=ZOO_C - TMIN, rho=RHO, tip_kmh=v_tip * 3.6)
if __name__ == "__main__":
    (Path(__file__).with_name("giraffe.json")).write_text(json.dumps(O, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in O.items():
        print(f"{k:14s} {v:,.2f}")
