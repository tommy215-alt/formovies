#!/usr/bin/env python3
"""pilot_056「頭の小さなプロペラで空を飛んだら？」の計算（もしも設計）。
運動量理論（ホバリング）：推力 T = 2ρA v²（v：プロペラの面を通る風の速さ）、ずっと下の風は 2v、理想のパワー P = T·v。
実際のプロペラは損失で理想の約 2 倍（小さなロータの実験の例、検索の要約）→ 係数 2。
反動：プロペラを回す力（トルク Q = P/Ω）が、体を逆向きに回す（ヘリコプターのしっぽのプロペラがない）。
    python rotor.py → rotor.json・results.md
"""
import json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
RHO = 1.2            # kg/m³ 空気の密度（地上、20℃ 前後）
M = 35.0 + .5        # kg 10 歳の平均体重 35.2 kg（令和 6 年度 学校保健統計、全国、検索の要約）＋プロペラ 0.5 kg（仮定）
D = .20              # m プロペラの直径（仮定：手のひらより少し大きい）
LOSS = 2.0           # 実際は理想の約 2 倍のパワー
TIP = 200.0          # m/s 羽根の先の速さ（仮定：音の速さの約 6 割。小型のドローン・模型の目安）
I_BODY = .5          # kg·m² 立った子どもの、縦の軸まわりの回りにくさ（仮定：半径 約 0.14 m の筒＋腕）
TYPHOON = 54.0       # m/s 猛烈な台風（気象庁の強さの階級）
KEI_PS = 64.0        # 軽自動車の最高出力の上限（自主規制、64 馬力＝約 47 kW）


def main():
    g = 9.8; T = M * g; A = math.pi * (D / 2) ** 2
    v = math.sqrt(T / (2 * RHO * A)); wake = 2 * v; P = T * v * LOSS; ps = P / 735.5
    om = TIP / (D / 2); rpm = om * 60 / (2 * math.pi); Q = P / om; alpha = Q / I_BODY
    out = dict(mass=M, thrust_n=T, area_m2=A, v_disk=v, v_wake=wake, wake_kmh=wake * 3.6, disk_kmh=v * 3.6, power_w=P, power_ps=ps, kei_ratio=ps / KEI_PS,
               rpm=rpm, torque=Q, alpha=alpha, spin_rps_1s=alpha / (2 * math.pi), spin_rps_3s=3 * alpha / (2 * math.pi), typhoon_ratio=wake / TYPHOON, d=D)
    (HERE / "rotor.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["# pilot_056 計算の結果（rotor.py）", "",
         f"- 体重 {M:.1f} kg を浮かせる力 {T:.0f} N、プロペラの直径 {D * 100:.0f} cm（面積 {A * 1e4:.0f} cm²）",
         f"- プロペラを通る風 時速 {v * 3.6:.0f} km、足もとへ吹き下ろす風 時速 {wake * 3.6:.0f} km（猛烈な台風 54 m/s の {wake / TYPHOON:.1f} 倍）",
         f"- いるパワー 約 {P / 1000:.0f} kW＝約 {ps:.0f} 馬力（軽自動車の上限 64 馬力の {ps / KEI_PS:.0%}）",
         f"- 回転 毎分 約 {rpm:,.0f} 回、反動の力 {Q:.0f} N·m → 体が逆に回る：1 秒後に 毎秒 {alpha / 6.283:.1f} 回転、3 秒後に 毎秒 {3 * alpha / 6.283:.0f} 回転"]
    (HERE / "results.md").write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))


if __name__ == "__main__":
    main()
