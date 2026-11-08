# pilot_047：毎日正午、都庁の真上に隕石。1 日目 10 cm、毎日 2 倍。
# 式は Collins, Melosh, Marcus (2005) "Earth Impact Effects Program"（MAPS 40）。
# 係数は論文の本文でまだ確かめていない（fact_check.md に記録する）。
# python impact.py → results_days.md
import math
from pathlib import Path

RHO_I, V0, THETA = 3000.0, 20000.0, 45.0      # 岩石・秒速 20 km・45 度
RHO_T, G, RE = 2500.0, 9.81, 6.371e6          # 地面は堆積岩
H, CD, FP = 8000.0, 2.0, 7.0                  # 大気のスケールハイト・抗力係数・パンケーキの広がり
KT = 4.184e12
HIROSHIMA = 15 * KT                           # 広島型 約 15 kt
SIN = math.sin(math.radians(THETA))

# 他の目安（概算。fact_check.md で出典を確かめる）
OCEAN_BOIL_J = 5e27      # 海 1.4e21 kg を温めて蒸発させる熱（約 2.6 MJ/kg）
EARTH_BIND_J = 2.24e32   # 地球の重力による結合エネルギー
EARTH_D = 12742e3

def rho_air(z): return math.exp(-z / H)

def entry(L):
    """大気に入ってからの壊れ方。(着地速度 m/s, 空中爆発の高さ m or None, 壊れ始めの高さ)"""
    Y = 10 ** (2.107 + 0.0624 * math.sqrt(RHO_I))
    If = 4.07 * CD * H * Y / (RHO_I * L * V0**2 * SIN)
    if If >= 1:
        return V0 * math.exp(-3 * CD * H / (4 * RHO_I * L * SIN)), None, None
    zs = -H * (math.log(Y / V0**2) + 1.308 - 0.314 * If - 1.303 * math.sqrt(1 - If))
    vs = V0 * math.exp(-3 * rho_air(zs) * CD * H / (4 * RHO_I * L * SIN))
    l = L * SIN * math.sqrt(RHO_I / (CD * rho_air(zs)))
    zb = zs - 2 * H * math.log(1 + l / (2 * H) * math.sqrt(FP**2 - 1))
    zend = max(zb, 0.0)
    # 壊れ始めから zend までの減速（式の積分を数値で）
    n, acc = 2000, 0.0
    for i in range(n):
        z = zs - (zs - zend) * (i + 0.5) / n
        Lz = L * math.sqrt(1 + (2 * H / l) ** 2 * (math.exp((zs - z) / (2 * H)) - 1) ** 2)
        acc += math.exp((zs - z) / H) * Lz**2 * (zs - zend) / n
    v = vs * math.exp(-0.75 * CD * rho_air(zs) / (RHO_I * L**3 * SIN) * acc)
    return v, (zb if zb > 0 else None), zs

def overpressure(r, Ekt, zb):
    """地面の最大の過圧 Pa（空中爆発は高さを考える）"""
    r1 = r / Ekt ** (1 / 3)
    surf = 75000 * 290 / (4 * r1) * (1 + 3 * (290 / r1) ** 1.3)
    if not zb:
        return surf
    zb1 = zb / Ekt ** (1 / 3)
    if zb1 >= 550:
        # 式の範囲より高い爆発：地表の爆発の式を、爆発点からの斜めの距離で使う（この回の近似）
        rs1 = math.hypot(r, zb) / Ekt ** (1 / 3)
        return 75000 * 290 / (4 * rs1) * (1 + 3 * (290 / rs1) ** 1.3)
    rm1 = 550 * zb1 / (1.2 * (550 - zb1))
    if r1 < rm1:
        return 3.14e11 * zb1 ** -2.6 * math.exp(-34.87 * zb1 ** -1.73 * r1)
    return surf

def reach(fn, lim, lo=10.0, hi=2.0e7):
    """fn(r) >= lim となる一番遠い距離（m）。届かなければ 0"""
    if fn(lo) < lim:
        return 0.0
    for _ in range(80):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if fn(mid) >= lim else (lo, mid)
    return lo

def day(n):
    L = 0.1 * 2 ** (n - 1)
    m = RHO_I * math.pi * L**3 / 6
    E0 = 0.5 * m * V0**2
    v, zb, zs = entry(L)
    E = 0.5 * m * v**2                      # 地面に衝突したときの運動エネルギー
    # 空気に渡った分も地面の近くで爆風になる → 爆風は最初のエネルギーで（この回の仮定）
    Ekt = E0 / KT
    d = dict(n=n, L=L, E0=E0, E=E, v=v, zb=zb, zs=zs)
    d["hiro"] = E0 / HIROSHIMA
    if E0 > EARTH_BIND_J:
        d["note"] = "地球の結合エネルギーを超える（地球が砕ける）"
    elif E0 > OCEAN_BOIL_J:
        d["note"] = "海をすべて蒸発させるエネルギーを超える"
    # 地上の被害（爆風）：ガラス 6.9 kPa、木造 26.8 kPa、鉄筋のビル 42.6 kPa（Collins の表）
    # 一部の窓が割れる 1 kPa（チェリャビンスクの目安。出典を確かめる）
    for key, kpa in (("crack", 1.0), ("glass", 6.9), ("wood", 26.8), ("bldg", 42.6)):
        d[key] = reach(lambda r: overpressure(r, Ekt, zb), kpa * 1000) / 1000
    # クレーター（地面に届いたとき）
    if zb is None:
        Dtc = 1.161 * (RHO_I / RHO_T) ** (1 / 3) * L**0.78 * v**0.44 * G**-0.22 * SIN ** (1 / 3)
        Dfr = 1.25 * Dtc if Dtc < 3200 else 1.17 * Dtc**1.13 / 3200**0.13
        d["crater"] = Dfr / 1000
        d["M"] = 0.67 * math.log10(E) - 5.87
        # 火の玉の熱：服が燃える（1 Mt で 1.0 MJ/m²、E^(1/6) で増える）
        Rf = 0.002 * E ** (1 / 3)
        s = (E / 4.184e15) ** (1 / 6)
        def phi(r):
            dd = r / RE; h = (1 - math.cos(dd)) * RE
            if h >= Rf: return 0.0
            de = math.acos(h / Rf)
            f = (2 / math.pi) * (de - (h / Rf) * math.sin(de))
            return 3e-3 * E / (2 * math.pi * r**2) * f
        d["cloth"] = reach(phi, 1.0e6 * s) / 1000
        d["fireball"] = Rf / 1000
    return d

def fmt_len(L):
    return f"{L*100:.0f} cm" if L < 1 else (f"{L:,.1f} m" if L < 1000 else f"{L/1000:,.1f} km")

def main():
    rows = ["# pilot_047 日ごとの結果（impact.py が作る）", "",
            "条件：毎日正午、都庁の真上。1 日目 直径 10 cm、毎日 2 倍。岩石 3,000 kg/m³・秒速 20 km・45 度。式は Collins ほか（2005）。",
            "距離は爆心（都庁）から。空中爆発は「上空 ○ km で爆発」。", "",
            "| 日 | 直径 | エネルギー（広島型の何発分） | 何が起きるか | 一部の窓が割れる | ガラスが割れる | 木造が倒れる | ビルが崩れる | 服が燃える | クレーター | 揺れ（M） |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for n in range(1, 29):
        d = day(n)
        if d.get("note"):
            what = d["note"]
        elif d["zb"]:
            what = f"上空 {d['zb']/1000:.1f} km で爆発"
        else:
            what = f"地面に衝突（秒速 {d['v']/1000:.1f} km）"
        km = lambda x: f"{x:,.1f} km" if x else "—"
        rows.append(f"| {n} | {fmt_len(d['L'])} | {d['hiro']:.3g} | {what} | {km(d['crack'])} | {km(d['glass'])} | {km(d['wood'])} | {km(d['bldg'])} | "
                    f"{km(d.get('cloth', 0))} | {km(d.get('crater', 0))} | {d['M']:.1f} |" if "M" in d else
                    f"| {n} | {fmt_len(d['L'])} | {d['hiro']:.3g} | {what} | {km(d['crack'])} | {km(d['glass'])} | {km(d['wood'])} | {km(d['bldg'])} | — | — | — |")
    out = Path(__file__).with_name("results_days.md")
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("\n".join(rows))

if __name__ == "__main__":
    main()

