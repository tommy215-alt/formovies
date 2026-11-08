# pilot_047：毎日正午、都庁の真上に隕石。1 日目 直径 10 cm、毎日 2 倍。28 日目に地球が砕ける。
# 式は Collins, Melosh, Marcus (2005) "Earth Impact Effects Program"（MAPS 40, 817-840）。
# 実装は、その Web 版の計算プログラム crater.cgi（PyPI の ImpactEffect 1.0.0 の test/cgi-bin に同梱）を
# そのまま Python に移した（大気中の壊れ方・空中爆発・爆風・被害の基準・クレーター・熱・揺れ）。
# python impact.py → results_days.md と days.json
import json, math
from pathlib import Path

RHO_I, V_IN, THETA = 3000.0, 20.0, 45.0      # 岩石 kg/m³・秒速 km・角度（度）
RHO_T = 2500.0                                # 地面：堆積岩
G, R_EARTH, PO = 9.8, 6370.0, 1e5             # crater.cgi の定数（R_EARTH は km）
RHO_SURF, H, CD, FP = 1.0, 8000.0, 2.0, 7.0
KT = 4.186e12                                 # crater.cgi の換算
HIROSHIMA_KT = 16.0                           # 広島の原爆 約 16 kt（放射線影響研究所）
SIN = math.sin(math.radians(THETA))

# 画面のエネルギーは身近なものに言い換える（日で切り替え。出典は fact_check.md）
CAR_J = 0.5 * 1500 * (100 / 3.6) ** 2         # 1.5 t の車が時速 100 km でぶつかる（約 58 万 J）
JP_ELEC_J = 8496.3e8 * 3.6e6                  # 日本で 1 年に使う電気（2023 年度の需要電力量 8,496.3 億 kWh）
WORLD_J = 620e18                              # 人類が 1 年に使うエネルギー（2023 年、620 EJ）
SUN_W = 3.828e26                              # 太陽が 1 秒に出す光（IAU の公称値）
LADDER = [(6, "car"), (12, "hiroshima"), (17, "jp_elec"), (21, "world"), (99, "sun")]


def familiar(n, E):
    """n 日目のエネルギー E (J) を身近なもので。(種類, 数, 画面の文)"""
    kind = next(k for last, k in LADDER if n <= last)
    num = lambda x: f"{x:,.0f}" if x < 1e4 else (f"{x/1e4:,.0f}万" if x < 1e8 else f"{x/1e8:,.0f}億")
    if kind == "car":
        x = E / CAR_J
        return kind, x, f"時速100kmの車 {num(x)}台の衝突"
    if kind == "hiroshima":
        x = E / (HIROSHIMA_KT * KT)
        return kind, x, f"広島の原爆 {x:,.1f}発" if x < 10 else f"広島の原爆 {num(x)}発"
    if kind == "jp_elec":
        x = E / JP_ELEC_J
        return kind, x, f"日本で使う電気 {num(x)}年分"
    if kind == "world":
        x = E / WORLD_J
        return kind, x, f"人類が使うエネルギー {num(x)}年分"
    s = E / SUN_W
    if s < 60:
        t = f"{s:,.0f}秒間"
    elif s < 3600:
        t = f"{s/60:,.0f}分間"
    elif s < 86400:
        t = f"{s/3600:,.0f}時間"
    else:
        t = f"{s/86400:,.0f}日間"
    return kind, s, f"太陽が{t}に出す光"

# 目安（fact_check.md で出典を確かめる）
OCEAN_BOIL_J = 5e27      # 海 1.4e21 kg を 15℃ から蒸発させる熱（約 2.6 MJ/kg × 1.4e21 kg ≒ 3.6e27 J、切り上げ）
EARTH_BIND_J = 2.49e32   # 地球の重力による結合エネルギー（密度の分布を考えた値。一様なら 2.24×10^32 J）
EARTH_D_KM = 12742.0


def entry(L):
    """crater.cgi の atmospheric_entry。(速度 km/s, 空中爆発の高さ m, 壊れ始めの高さ m, 地面での破片の広がり m)"""
    Y = 10 ** (2.107 + 0.0624 * RHO_I ** 0.5)
    rS = Y / (RHO_SURF * (V_IN * 1000) ** 2)
    av = 3 * RHO_SURF * CD * H / (4 * RHO_I * L * SIN)
    iF = 2.7185 * av * rS
    if iF >= 1:                                   # 壊れずに地面へ
        vT = min(V_IN * 1000, (4 * RHO_I * L * G / (3 * RHO_SURF * CD)) ** 0.5)
        return max(vT, V_IN * 1000 * math.exp(-av)) / 1000, 0.0, None, 0.0
    omega = 1.308 - 0.314 * iF - 1.303 * (1 - iF) ** 0.5
    zBU = -H * math.log(rS) - omega * H
    vBU = V_IN * 1000 * math.exp(-av * math.exp(-zBU / H))
    vFac = 0.75 * (CD * RHO_SURF / RHO_I) ** 0.5 * math.exp(-zBU / (2 * H))
    lD = L * SIN * (RHO_I / (CD * RHO_SURF)) ** 0.5 * math.exp(zBU / (2 * H))
    a2 = (FP ** 2 - 1) ** 0.5
    zB = zBU - 2 * H * math.log(1 + a2 * lD / (2 * H))
    if zB > 0:                                    # 空中爆発
        ex = 1 / 24 * a2 * (24 + 8 * a2 ** 2 + 6 * a2 * lD / H + 3 * a2 ** 3 * lD / H)
        return vBU * math.exp(-ex * vFac) / 1000, zB, zBU, 0.0
    s = H / lD                                    # 広がりながら地面へ
    integ = s ** 3 / 3 * (3 * (4 + 1 / s ** 2) * math.exp(zBU / H) + 6 * math.exp(2 * zBU / H)
                          - 16 * math.exp(1.5 * zBU / H) - 3 / s ** 2 - 2)
    disp = L * (1 + 4 * s ** 2 * (math.exp(zBU / (2 * H)) - 1) ** 2) ** 0.5
    return vBU * math.exp(-vFac * integ) / 1000, 0.0, zBU, disp


def overpressure(dist_km, E_kt, zB):
    """crater.cgi の air_blast。地面の最大の過圧 Pa"""
    sf = E_kt ** (1 / 3)
    d = dist_km * 1000 / sf
    z = zB / sf
    rc = 290 + 0.65 * z
    rm = 1e30 if z >= 550 else 550 * z / (1.2 * (550 - z))
    mach = lambda x: rc * 75000 / 4 / x * (1 + 3 * (rc / x) ** 1.3)
    reg = lambda x: 3.14e11 * (x ** 2 + z ** 2) ** -1.3 + 1.8e7 * (x ** 2 + z ** 2) ** -0.565
    if zB > 0:
        ds = z ** 2 * 0.00328
        pM, pR = mach(rm + ds), reg(rm - ds)
    else:
        ds = 0.0
    if d >= rm + ds:
        return mach(d)
    if d <= rm - ds:
        return reg(d)
    return pR - (d - rm + ds) * 0.5 * (pR - pM) / ds


def thermal(dist_km, E_surf):
    """crater.cgi の find_thermal。熱の量 J/m²（火の玉が地平線の下なら 0）"""
    Rf = 2e-6 * E_surf ** (1 / 3)                 # km
    h = (1 - math.cos(dist_km / R_EARTH)) * R_EARTH
    if h > Rf:
        return 0.0
    de = math.acos(h / Rf)
    f = (2 / math.pi) * (de - (h / Rf) * math.sin(de))
    return 3e-3 * E_surf / (2 * math.pi * (dist_km * 1000) ** 2) * f


def reach(fn, lim, lo=0.01, hi=20000.0):
    """fn(km) >= lim となる一番遠い距離（km、地球の半周 20,000 km まで）。届かなければ 0"""
    if fn(lo) < lim:
        return 0.0
    if fn(hi) >= lim:
        return hi
    for _ in range(80):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if fn(mid) >= lim else (lo, mid)
    return lo


def day(n):
    L = 0.1 * 2 ** (n - 1)
    m = RHO_I * math.pi * L ** 3 / 6
    E0 = 0.5 * m * (V_IN * 1000) ** 2
    v, zB, zBU, disp = entry(L)
    E_atm = 0.5 * m * ((V_IN * 1000) ** 2 - (v * 1000) ** 2)
    if zB > 0:
        E_blast, E_surf = E_atm / KT, E_atm
    else:
        E_surf = 0.5 * m * (v * 1000) ** 2
        E_blast = max(E_atm, E_surf) / KT
    d = dict(day=n, L_m=L, E0_J=E0, hiroshima=E0 / KT / HIROSHIMA_KT, v_kms=v, burst_m=zB, breakup_m=zBU)
    d['energy_kind'], d['energy_x'], d['energy_text'] = familiar(n, E0)
    # 爆風：crater.cgi の基準（Pa）
    for key, pa in (("glass_may", 690), ("glass", 6900), ("wood", 26800), ("bldg", 42600),
                    ("steel", 273000)):
        d[key + "_km"] = reach(lambda r: overpressure(r, E_blast, zB), pa)
    if zB == 0:
        mt = E_surf / (KT * 1000)
        mf = mt ** (1 / 6)
        d["cloth_km"] = reach(lambda r: thermal(r, E_surf), 1e6 * mf)
        d["burn3_km"] = reach(lambda r: thermal(r, E_surf), 4.2e5 * mf)
        d["fireball_km"] = 2e-6 * E_surf ** (1 / 3)
        Dtr = 1.6 * (m / RHO_T) ** (1 / 3) * (1.61 * G * L / (v * 1000) ** 2) ** -0.22 * SIN ** (1 / 3)
        if disp >= Dtr:                           # 破片の雨：一番大きな破片（直径の半分）のクレーター
            Dtr /= 2
        Dfr = 1.17 * Dtr ** 1.13 / 3200 ** 0.13 if Dtr * 1.25 >= 3200 else 1.25 * Dtr
        d["crater_km"] = Dfr / 1000
        d["M"] = 0.67 * math.log10(E_surf) - 5.87
    if E0 > EARTH_BIND_J:
        d["global"] = "earth_breaks"
    elif E0 > OCEAN_BOIL_J:
        d["global"] = "oceans_boil"
    # 式の範囲：被害の距離が地球の半周を超えたら、距離は意味を持たない
    d["beyond_model"] = d["glass_km"] >= 20000 or d.get("crater_km", 0) > EARTH_D_KM / 4
    return d


def fmt_len(L):
    return f"{L*100:.0f} cm" if L < 1 else (f"{L:,.1f} m" if L < 1000 else f"{L/1000:,.1f} km")


def main():
    days = [day(n) for n in range(1, 29)]
    here = Path(__file__).parent
    (here / "days.json").write_text(json.dumps(days, ensure_ascii=False, indent=1), encoding="utf-8")
    km = lambda x: "—" if not x else ("地球全体" if x >= 20000 else f"{x:,.1f}")
    rows = ["# pilot_047 日ごとの結果（impact.py が作る）", "",
            "条件：毎日正午、都庁の真上。1 日目 直径 10 cm、毎日 2 倍。岩石 3,000 kg/m³・秒速 20 km・45 度・地面は堆積岩 2,500 kg/m³。",
            "式は Collins ほか（2005）、実装は Earth Impact Effects Program の crater.cgi を移したもの。距離は都庁から km。", "",
            "| 日 | 直径 | エネルギー（画面の言い換え） | 何が起きるか | 窓が割れるかも（690 Pa） | 窓が割れる（6.9 kPa） | 木造が倒れる | ビルが崩れる | 服が燃える | クレーター | 揺れ（M） |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for d in days:
        if d.get("global") == "earth_breaks":
            what = "地球の結合エネルギーを超える（地球が砕ける）"
        elif d.get("global") == "oceans_boil":
            what = "海をすべて蒸発させるエネルギーを超える"
        elif d["burst_m"] > 0:
            what = f"上空 {d['burst_m']/1000:.1f} km で爆発"
        else:
            what = f"地面に衝突（秒速 {d['v_kms']:.1f} km）"
        rows.append(f"| {d['day']} | {fmt_len(d['L_m'])} | {d['energy_text']} | {what} | {km(d['glass_may_km'])} | "
                    f"{km(d['glass_km'])} | {km(d['wood_km'])} | {km(d['bldg_km'])} | {km(d.get('cloth_km'))} | "
                    f"{km(d.get('crater_km'))} | {d['M']:.1f} |" if "M" in d else
                    f"| {d['day']} | {fmt_len(d['L_m'])} | {d['energy_text']} | {what} | {km(d['glass_may_km'])} | "
                    f"{km(d['glass_km'])} | {km(d['wood_km'])} | {km(d['bldg_km'])} | — | — | — |")
    rows += ["", "- 「地球全体」は地球の半周（20,000 km）を超えるもの。17 日目ごろから先は式をあてはめる範囲を超えるので、画面では文献の目安で見せる。"]
    (here / "results_days.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("\n".join(rows[5:]))


if __name__ == "__main__":
    main()
