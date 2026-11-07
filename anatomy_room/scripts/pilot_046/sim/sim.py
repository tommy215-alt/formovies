#!/usr/bin/env python3
"""pilot_046「全人類の体重が1日10%ずつ増加したら？」（もしも設計）の計算。

条件（U＝ユーザー）：全人類の体重が 1 日 10% ずつ増える。見た目・大きさはそのまま（密度だけ上がる）。体重が増えること自体の健康被害・自重で体が潰れることはない。
人類だけが重くなる。
F＝出典のある値（fact_check.md）、A＝Claude の仮定。
    python sim.py   → results.md（何日目に何を超えるか、月と惑星の軌道）
"""
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
G, C = 6.674e-11, 2.998e8
DAY = 86400.0
K = math.log(1.1)   # 1 日 10%（U）

# --- 人 ---
M_ADULT = 62.0        # F：大人の平均体重（Walpole ほか 2012、2005 年の推計 62 kg）
POP = 8.2e9           # A：世界人口（約 82 億人、2026 年の目安）
M_MEAN = 50.0         # A：子どもを含めた平均体重（大人 62 kg、子ども・高齢者を含めた目安）
M_HUMANITY0 = POP * M_MEAN
RHO_BODY = 985.0      # F：人の体の平均密度（kg/m³、教科書の値）
RHO_SEA = 1025.0      # F：海水の密度（kg/m³）
FOOT_AREA = 0.03      # A：両足の裏が地面に触れる面積（m²、片足 150 cm²）

# --- 限界の値 ---
ELEV_KG = 65.0        # F：エレベーターの定員は 1 人 65 kg で計算（建築基準法施行令 129 条の 6 第 5 号）
FLOOR = {"住宅の居室": 1800, "事務室": 2900, "劇場などの客席（固定席）": 2900, "劇場などの客席（その他）": 3500}   # F：床の積載荷重 N/m²（施行令 85 条、床の構造計算）
SOIL = {"粘土質地盤": 20e3, "ローム層": 50e3, "密実な砂質地盤": 200e3, "岩盤": 1000e3}   # F：地盤の長期許容応力度 N/m²（施行令 93 条）
CONCRETE = 30e6       # A＋F：建物のコンクリートの設計基準強度の目安 30 N/mm²（一般に 21〜36）
GRANITE = 200e6       # F：花崗岩の圧縮強さ 100〜250 MPa の上の方
DENSITY = {"立って詰めた客席・通路": 2.0, "満員電車": 3.0}   # A：1 m² あたりの人数

# --- 天体（NASA の Planetary Fact Sheet） ---
M_ATM, M_OCEAN = 5.15e18, 1.4e21                       # F：大気・海の質量
M_MOON, M_EARTH, M_JUP, M_SUN = 7.346e22, 5.972e24, 1.898e27, 1.989e30
R_EARTH, A_MOON, RHO_MOON = 6.371e6, 3.844e8, 3344.0
AU = 1.496e11


def mass_person(d):
    return M_ADULT * math.exp(K * d)


def mass_humanity(d):
    return M_HUMANITY0 * math.exp(K * d)


def day_for_person(m):
    return math.log(m / M_ADULT) / K


def day_for_humanity(m):
    return math.log(m / M_HUMANITY0) / K


def moon_orbit():
    """地球（＋人類）の重さが増えると、月の軌道は縮んでゆがむ（増え方が月の周期 27 日より速いので、ゆっくりの近似は使えない）。
    地球＋人類と月の 2 体を数値で追い、近点が月の砕ける距離（流体のロッシュ限界）より内側になる日を出す。
    人類は地球の中に沈んでいる（地球の半径は変わらない）として、ロッシュ限界は地球の平均密度で決める。"""
    d0 = 316.0   # 人類の重さが地球と同じになる少し前から追う（それまでは地球の重さはほぼ変わらない）
    d0 = day_for_humanity(M_EARTH * .01)
    r = np.array([A_MOON, 0.0]); v = np.array([0.0, math.sqrt(G * (M_EARTH + mass_humanity(d0) + M_MOON) / A_MOON)])
    t, dt, out = d0 * DAY, 600.0, []
    def acc(r, t):
        M = M_EARTH + mass_humanity(t / DAY) + M_MOON
        return -G * M * r / np.linalg.norm(r) ** 3
    while t < 600 * DAY:
        k1v = acc(r, t); k1r = v
        k2v = acc(r + .5 * dt * k1r, t + .5 * dt); k2r = v + .5 * dt * k1v
        k3v = acc(r + .5 * dt * k2r, t + .5 * dt); k3r = v + .5 * dt * k2v
        k4v = acc(r + dt * k3r, t + dt); k4r = v + dt * k3v
        r = r + dt / 6 * (k1r + 2 * k2r + 2 * k3r + k4r); v = v + dt / 6 * (k1v + 2 * k2v + 2 * k3v + k4v); t += dt
        M = M_EARTH + mass_humanity(t / DAY)
        rho = M / (4 / 3 * math.pi * R_EARTH ** 3)
        roche = 2.44 * R_EARTH * (rho / RHO_MOON) ** (1 / 3)
        dist = np.linalg.norm(r)
        out.append((t / DAY, dist, roche))
        if dist < roche:
            return t / DAY, out
    return None, out


def schwarzschild_day():
    """人類が地球の中心に集まったとき（体の大きさは変わらない）、その大きさがシュワルツシルト半径より小さくなる日（ブラックホール）"""
    V = M_HUMANITY0 / RHO_BODY          # 人類全員の体積（大きさは変わらない）
    R = (3 * V / (4 * math.pi)) ** (1 / 3)
    M = R * C ** 2 / (2 * G)
    return day_for_humanity(M), R, M, V


def planets():
    """太陽・金星・地球（＋人類）・火星・木星を数値で追い、地球の重さが増えると周りの惑星の軌道がどう変わるかを見る（平面、円軌道から）。"""
    bodies = [("太陽", M_SUN, 0.0), ("金星", 4.867e24, .723), ("地球", M_EARTH, 1.0), ("火星", 6.417e23, 1.524), ("木星", M_JUP, 5.203)]
    n = len(bodies); m = np.array([b[1] for b in bodies]); pos = np.zeros((n, 2)); vel = np.zeros((n, 2))
    for i, (_, mi, a) in enumerate(bodies):
        if a > 0:
            ang = i * 1.3; pos[i] = a * AU * np.array([math.cos(ang), math.sin(ang)]); vel[i] = math.sqrt(G * M_SUN / (a * AU)) * np.array([-math.sin(ang), math.cos(ang)])
    d0 = 300.0; t, dt = d0 * DAY, 3600.0 * 3; rec = []
    def masses(t):
        mm = m.copy(); mm[2] = M_EARTH + mass_humanity(t / DAY); return mm
    def acc(pos, mm):
        a = np.zeros_like(pos)
        for i in range(n):
            d = pos - pos[i]; r3 = np.maximum(np.sum(d * d, 1), 1e10) ** 1.5; r3[i] = np.inf
            a[i] = np.sum((G * mm / r3)[:, None] * d, 0)
        return a
    while t < 470 * DAY:
        mm = masses(t); a = acc(pos, mm); vel += .5 * dt * a; pos += dt * vel; a = acc(pos, masses(t + dt)); vel += .5 * dt * a; t += dt
        if int(t / DAY) != int((t - dt) / DAY):
            cm = np.sum(mm[:, None] * pos, 0) / mm.sum()
            rec.append((t / DAY, [np.linalg.norm(pos[i] - pos[0]) / AU for i in range(n)], np.linalg.norm(pos[0] - cm) / AU, mm[2] / M_SUN))
    return bodies, rec


def main():
    L = ["# pilot_046 計算の結果（自動で作る：python sim.py）", "",
         f"1 人の体重 = {M_ADULT:.0f} kg × 1.1^日、人類の重さ = {M_HUMANITY0:.2e} kg × 1.1^日（人口 {POP:.2e}・平均 {M_MEAN:.0f} kg）。2 倍 {math.log(2)/K:.1f} 日、10 倍 {math.log(10)/K:.1f} 日。", ""]
    L += ["## 1 人の体重", "", "| 日 | 1 人 | 人類の合計 |", "|---|---|---|"]
    for d in (0, .5, 1, 2, 3, 5, 7, 10, 14, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 120, 150):
        L.append(f"| {d} | {mass_person(d):,.0f} kg | {mass_humanity(d):.2e} kg |")
    ev = []
    ev.append(("人が海に浮かなくなる（体の密度が海水を超える）", math.log(RHO_SEA / RHO_BODY) / K))
    ev.append(("定員いっぱいのエレベーターが重さの上限を超える（1 人 65 kg で計算）", day_for_person(ELEV_KG)))
    ev.append(("エレベーターに定員の半分しか乗れない", day_for_person(2 * ELEV_KG)))
    for k, n_ in DENSITY.items():
        for fk in ("劇場などの客席（その他）",):
            ev.append((f"{k}（1 m² に {n_} 人）が床の設計の重さ（{fk} {FLOOR[fk]} N/m²）を超える", day_for_person(FLOOR[fk] / 9.8 / n_)))
    ev.append(("家族 4 人が 10 m² の部屋にいると住宅の床の設計の重さ（1,800 N/m²）を超える", day_for_person(FLOOR["住宅の居室"] / 9.8 * 10 / 4)))
    for k, p in SOIL.items():
        ev.append((f"立っているだけで{k}の許容応力度（長期 {p/1e3:,.0f} kN/m²）を超える（足の裏 {FOOT_AREA} m²）", day_for_person(p * FOOT_AREA / 9.8)))
    ev.append((f"コンクリート（{CONCRETE/1e6:.0f} N/mm²）が足の下で砕ける", day_for_person(CONCRETE * FOOT_AREA / 9.8)))
    ev.append((f"花崗岩（{GRANITE/1e6:.0f} MPa）も足の下で砕ける", day_for_person(GRANITE * FOOT_AREA / 9.8)))
    for k, mm in (("車（1.5 t）", 1500), ("ゾウ（6 t）", 6000), ("シロナガスクジラ（150 t）", 150e3), ("ジャンボジェット（最大 400 t）", 400e3), ("東京タワー（約 4,000 t）", 4e6)):
        ev.append((f"1 人が{k}より重くなる", day_for_person(mm)))
    for k, mm in (("大気", M_ATM), ("海", M_OCEAN), ("月", M_MOON), ("地球", M_EARTH), ("木星", M_JUP), ("太陽", M_SUN)):
        ev.append((f"人類の重さが{k}を超える", day_for_humanity(mm)))
    dm, orbit = moon_orbit()
    if dm:
        ev.append(("月が地球（＋人類）に近づきすぎて砕ける（近点が流体のロッシュ限界の内側に）", dm))
    db, R, MB, V = schwarzschild_day()
    ev.append((f"人類（全員の体積 {V:.1e} m³、集まると半径 {R:.0f} m の球）がブラックホールになる（重さ {MB:.1e} kg＝太陽の {MB/M_SUN:.2f} 倍）", db))
    L += ["", "## 何日目に何を超えるか", "", "| 日 | 出来事 |", "|---|---|"]
    for k, d in sorted(ev, key=lambda x: x[1]):
        L.append(f"| {d:.1f} | {k} |")
    L += ["", "## 月の軌道（地球＋人類との距離、ロッシュ限界）", "", "| 日 | 月までの距離 | ロッシュ限界 |", "|---|---|---|"]
    for t, dist, roche in orbit[:: max(1, len(orbit) // 30)]:
        L.append(f"| {t:.1f} | {dist/1e3:,.0f} km | {roche/1e3:,.0f} km |")
    bodies, rec = planets()
    L += ["", "## 惑星の軌道（太陽からの距離 AU）と、太陽系の重心", "", "| 日 | " + " | ".join(b[0] for b in bodies[1:]) + " | 太陽のずれ（AU） | 地球の重さ／太陽 |", "|---|" + "---|" * (len(bodies) + 1)]
    for d, rr, cm, ratio in rec[:: 10]:
        L.append(f"| {d:.0f} | " + " | ".join(f"{x:.2f}" for x in rr[1:]) + f" | {cm:.3f} | {ratio:.2e} |")
    (HERE / "results.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:60]))


if __name__ == "__main__":
    main()
