#!/usr/bin/env python3
"""pilot_061 もしも世界中の現金が、いま金に変わったら（同じ値段の金に置き換える）。
python scripts/pilot_061/sim/gold.py  → 同じフォルダの gold.json
数字の出典と確認方法は ../fact_check.md（すべて検索の要約・抜粋）。"""
import json
from pathlib import Path

OZ = 31.1034768                     # 1 トロイオンス（g）
GOLD_USD_OZ = 3885                  # 2026-11-17 ごろの金の値段（ドル／オンス）
USD_G = GOLD_USD_OZ / OZ            # 1 g の値段（ドル）
FX = {"USD": 1, "EUR": 1.122, "CNY": 1 / 6.67, "JPY": 1 / 157.94, "INR": 1 / 93.62,   # 1 単位＝何ドル
      "GBP": 1.32, "CHF": 1 / 0.839, "RUB": 1 / 80, "KRW": 1 / 1337, "BRL": 1 / 5.66, "MXN": 1 / 18.59,
      "SAR": 1 / 3.75, "IDR": 1 / 18245, "AUD": 0.679, "CAD": 1 / 1.426, "HKD": 1 / 7.8}   # 11 月中ごろ（ECB の参照レートから換算）。RUB は目安
ALL_GOLD_T = 224_200                # 人類が掘った金の総量（地上在庫、2026 年 7〜9 月、WGC）
US_RESERVE_T = 8_133                # アメリカの公的な金（政府・中央銀行）
JP_RESERVE_T = 846                  # 日本の公的な金（2026 年はじめ）

# 地域：(現金の量, 通貨, 人口)
REGIONS = {
    "アメリカ": (2.47e12, "USD", 342e6),        # 2026-06 FRB H.6。約 45% は国外で持たれている（FRB の推計 2021）
    "ユーロ圏": (1.62e12, "EUR", 351e6),        # 2025 年末 €1,619.5bn、2026-09 も「1.6 兆ユーロ超」
    "中国": (15.02e12, "CNY", 1.408e9),          # 2026-09 末 M0
    "日本": (115.0e12, "JPY", 1.233e8),          # 2026-07 流通中の日銀券 約 115 兆円（硬貨は含まない）
    "インド": (42.9e12, "INR", 1.46e9),          # 2026-08-15 RBI 42.90 lakh crore
    "アフリカ": (190e9, "USD", 1.55e9),          # 国別の合計の目安（下の AFRICA）
    "イギリス": (94e9, "GBP", 69.3e6),           # 2026-09 BoE 約 940 億ポンド
    "スイス": (73.3e9, "CHF", 9.0e6),            # 2024 年平均 SNB（2026 年の値は見つからず）
    "ロシア": (21.0e12, "RUB", 146e6),           # 2026-10-01 M0 21.0 兆ルーブル（相場は目安）
    "韓国": (215e12, "KRW", 51.7e6),             # 2026 年 3 月末 約 215 兆ウォン
    "ブラジル": (345e9, "BRL", 213e6),           # 中銀「約 3,450 億レアルで横ばい」（年は要確認）
    "メキシコ": (3.4e12, "MXN", 132e6),          # 2026-03 Banxico 3.4 兆ペソ
    "サウジアラビア": (248e9, "SAR", 35e6),      # 2026-02 銀行の外の現金 2,480 億リヤル
    "インドネシア": (1206.3e12, "IDR", 284e6),   # 2026-03 銀行の外の現金
    "オーストラリア": (103.8e9, "AUD", 27.6e6),  # RBA（業者のブログ経由、2024〜25）
    "カナダ": (125.6e9, "CAD", 41.5e6),          # 2026-06-30 Bank of Canada
    "香港": (670.1e9, "HKD", 7.5e6),             # 2026-05 HKMA 硬貨を含む
}
AFRICA = {  # 10 億ドル。年がそろわない目安
    "アルジェリア": 60, "モロッコ": 40, "エジプト": 25, "南アフリカ": 10, "CEMAC（中部アフリカ 6 か国）": 10,
    "ナイジェリア": 4, "チュニジア": 8, "そのほか（西アフリカの CFA・ケニア・エチオピアなど）": 33,
}


def main():
    out = {"gold_usd_oz": GOLD_USD_OZ, "usd_per_g": round(USD_G, 2), "regions": []}
    tot_t = 0
    for name, (amt, cur, pop) in REGIONS.items():
        usd = amt * FX[cur]; t = usd / USD_G / 1e6; g = usd / pop / USD_G
        tot_t += t
        out["regions"].append({"name": name, "usd_bn": round(usd / 1e9), "tonnes": round(t), "pop": pop,
                               "usd_pp": round(usd / pop), "g_pp": round(g, 1)})
    out["pop_total"] = sum(p for _, _, p in REGIONS.values()); out["total_tonnes"] = round(tot_t); out["share_of_all_gold"] = round(tot_t / ALL_GOLD_T, 3)
    us = out["regions"][0]; out["us_vs_reserve"] = round(us["tonnes"] / US_RESERVE_T, 2)
    jp, af = out["regions"][3], out["regions"][5]; out["jp_vs_reserve"] = round(jp["tonnes"] / JP_RESERVE_T, 1); out["japan_vs_africa_pp"] = round(jp["g_pp"] / af["g_pp"])
    out["africa_sum_bn"] = sum(AFRICA.values())
    # 金の延べ棒 1 本＝約 12.4 kg（ロンドンの標準の延べ棒、400 オンス）
    out["bars_japan"] = round(jp["tonnes"] * 1000 / 12.44)
    Path(__file__).with_name("gold.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in sorted(out["regions"], key=lambda r: -r["g_pp"]):
        print(f'{r["name"]:8} {r["usd_bn"]:>6} 十億$  {r["tonnes"]:>6} t  1人 {r["usd_pp"]:>6} $  {r["g_pp"]:>5} g')
    print({k: v for k, v in out.items() if k != "regions"})


if __name__ == "__main__":
    main()
