#!/usr/bin/env python3
"""pilot_059「日本アルプスが、ヒマラヤ山脈になったら？」の数字。出典と確認方法は ../fact_check.md。
    python himalaya.py → himalaya.json（plan.py が読む）"""
import json, math
from pathlib import Path

R = 6_371_000.0
EVEREST, FUJI, KITA = 8_849, 3_776, 3_193     # m（エベレストは 2020 年の中国・ネパールの共同測量 8,848.86 m）
LEN_H, LEN_HONSHU = 2_400, 1_300              # km（ヒマラヤの長さ、本州の長さ 約 1,300 km）
JET = 10_000                                  # 旅客機の巡航高度 m（目安）
P_RATIO = 1 / 3                               # 山頂の気圧は地上の約 1/3（2019 年の研究 309〜343 hPa）
see = math.sqrt(2 * R * EVEREST) / 1000       # 山頂が見える距離 km（見る人の目の高さ 0 m、光の屈折なし）
TOKYO_D = 200                                 # 東京〜北アルプスの中心のあたり km（目安）
PL = json.loads((Path(__file__).with_name("place.json")).read_text(encoding="utf-8"))   # place.py（置き方・平均標高）
AV_KM, AV_KMH = 16, 300                       # 1970 年ペルー・ワスカランの大雪崩：約 14.5〜18 km 先の町まで、平均 時速 約 280〜335 km（USGS ほか）
ANNAPURNA = 8_091
O = dict(everest=EVEREST, fuji=FUJI, kita=KITA, ratio=EVEREST / FUJI, len=LEN_H, len_ratio=LEN_H / LEN_HONSHU, jet=JET, gap=JET - EVEREST,
         see_km=see, tokyo_d=TOKYO_D, hidden_m=(TOKYO_D * 1000) ** 2 / (2 * R), p_ratio=P_RATIO, n8000=10,
         avg_now=PL["avg_now"], avg_new=PL["avg_new"], dT=PL["dT"], area_ratio=PL["area_new"] / PL["area_now"], tokyo_ev_km=PL["tokyo_km"],
         hidden_tokyo_m=(PL["tokyo_km"] * 1000) ** 2 / (2 * R), av_km=AV_KM, av_kmh=AV_KMH, annapurna=ANNAPURNA)
if __name__ == "__main__":
    (Path(__file__).with_name("himalaya.json")).write_text(json.dumps(O, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in O.items():
        print(f"{k:10s} {v:,.2f}")
