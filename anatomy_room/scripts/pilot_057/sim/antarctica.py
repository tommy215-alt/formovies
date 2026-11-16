#!/usr/bin/env python3
"""pilot_057「犬ぞりで、南極を横断したら？」の数字。出典と確認方法は ../fact_check.md。
    python antarctica.py → antarctica.json（plan.py が読む）"""
import json
from pathlib import Path

AREA = 14.0e6          # 南極大陸の面積 km²（14.0〜14.2 百万 km²、小さい方）
JAPAN = 377_975        # 日本の面積 km²（国土地理院）
ROUTE = 6_000          # 1989–90 国際南極横断隊の道のり km（Wikipedia 6,021 km／Guinness 6,048 km → 約 6,000 km）
DAYS = 220             # 同、日数（1989-07-26 → 1990-03-03）
JP_LEN = 3_000         # 日本列島の長さ km（北海道〜沖縄、約 3,000 km）
TMIN_F = -54           # 最低気温 °F（National Geographic、検索の要約）
WIND_MPH = 100         # 風 mph（同）
DOG_KCAL = 10_000      # 走るそり犬の 1 日のエネルギー kcal（Iditarod 公式の教材 10,000–12,000 の下限）
HUMAN_KCAL = 2_000     # おとなの 1 日（目安）

O = dict(area_ratio=AREA / JAPAN, route_km=ROUTE, days=DAYS, km_per_day=ROUTE / DAYS, route_vs_japan=ROUTE / JP_LEN,
         tmin_c=(TMIN_F - 32) / 1.8, wind_kmh=WIND_MPH * 1.609, dog_kcal=DOG_KCAL, dog_vs_human=DOG_KCAL / HUMAN_KCAL)
if __name__ == "__main__":
    (Path(__file__).with_name("antarctica.json")).write_text(json.dumps(O, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in O.items():
        print(f"{k:16s} {v:,.2f}")
