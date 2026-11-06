"""30 分以降：1 km メッシュで日本の主な島まで計算する。

使い方：python macro.py [シナリオ名]（シナリオは SCEN）
出力：data/macro_<名>.npz（1 時間ごとの集計、主な都市に着いた時刻、決まった時刻のマップ）
"""
import math, os, sys, time
import numpy as np
import params as P
from build_grid import latlon_rc, mesh_rc, NR, NC

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
DAY = 1440.0  # 分

SCEN = {
    # 基準：うろつき方は「1 分ごとに向きを変えて歩く」、自衛隊は 12 時間後に武器を使える、橋とトンネルは閉じない
    "base":     dict(wander_tau=60, sdf_armed_h=12, ammo=5e7, link_close_day=None, front_out=0.01),
    "roam":     dict(wander_tau=600, sdf_armed_h=12, ammo=5e7, link_close_day=None, front_out=0.01),   # 10 分まっすぐ歩く
    "slow_gov": dict(wander_tau=60, sdf_armed_h=72, ammo=5e7, link_close_day=None, front_out=0.01),   # 武器の使用が 3 日後
    "no_sdf":   dict(wander_tau=60, sdf_armed_h=1e9, ammo=0, link_close_day=None, front_out=0.01),
    "close":    dict(wander_tau=60, sdf_armed_h=12, ammo=5e7, link_close_day=2, front_out=0.01),     # 2 日目に橋・トンネルを封鎖
    "outdoor":  dict(wander_tau=60, sdf_armed_h=12, ammo=5e7, link_close_day=None, front_out=0.03, go_home=True),  # 外に出る人が多い
}

# 海峡を渡る道（橋・トンネル）。（名前, 端 A, 端 B, 長さ km）
LINKS = [
    ("関門（橋・トンネル・人道トンネル）", (33.960, 130.948), (33.945, 130.962), 1.0),
    ("明石海峡大橋", (34.628, 135.020), (34.598, 135.012), 3.9),
    ("大鳴門橋", (34.250, 134.665), (34.228, 134.635), 1.6),
    ("瀬戸大橋", (34.468, 133.805), (34.335, 133.830), 13.1),
    ("しまなみ海道", (34.405, 133.205), (34.095, 133.010), 60.0),
    ("青函トンネル", (41.150, 140.480), (41.550, 140.300), 53.9),
]
# 1 km の格子で関門海峡がつながってしまう所を切る（33.950° と 33.958° の行の間）
STRAIT_CUTS = [((33.950, 33.958), (130.88, 131.05))]

CITIES = {"新宿駅": (35.6905, 139.7003), "東京駅": (35.6812, 139.7671), "渋谷": (35.658, 139.7016),
          "池袋": (35.7295, 139.7109), "立川": (35.698, 139.414), "八王子": (35.656, 139.339),
          "横浜": (35.4658, 139.6223), "川崎": (35.531, 139.697), "さいたま": (35.8617, 139.6455),
          "千葉": (35.6074, 140.1065), "成田": (35.776, 140.318), "宇都宮": (36.5551, 139.8826),
          "前橋": (36.3895, 139.0634), "水戸": (36.3707, 140.4762), "甲府": (35.6662, 138.5683),
          "静岡": (34.9756, 138.3828), "名古屋": (35.1709, 136.8815), "大阪": (34.7025, 135.4959),
          "広島": (34.3976, 132.4754), "福岡": (33.5902, 130.4207), "仙台": (38.2601, 140.8822),
          "青森": (40.8286, 140.7340), "札幌": (43.0687, 141.3508), "高松": (34.3503, 134.0466),
          "新潟": (37.9122, 139.0613), "金沢": (36.578, 136.648)}
SNAP_H = [0.5, 1, 2, 3, 6, 12, 24, 48, 72, 120, 168, 192, 240, 336, 504, 528, 720, 1080, 1440, 2160]


def out_frac(t, sc):
    """まだゾンビが来ていない（が、知っている）地域で、屋外にいる人の割合。"""
    if t < P.T_MEDIA_MIN:
        return P.OUT_FRAC_NOON
    if t < 6 * 60:
        if sc.get("go_home"):   # 歩いて帰る人・子どもを迎えに行く人が多い（東日本大震災の帰宅困難者のように、電車は止まる）
            return 0.05
        return 0.02 + (P.OUT_FRAC_NOON - 0.02) * math.exp(-(t - P.T_MEDIA_MIN) / 30.0)   # 速報を見て屋内へ
    if t < DAY:
        return 0.02
    return sc["front_out"]  # 買い物などで最小限


def run(name):
    sc = SCEN[name]
    g = np.load(os.path.join(D, "grid.npz"))
    land = g["land"]; night = g["night"].astype(np.float64); day = g["day"].astype(np.float64)
    area = 1.045
    # 昼の居場所：家にいる人＝常住人口の 55%（昼間人口より多ければ昼間人口まで）、残りは大きな建物（オフィス・店・学校）
    H = np.minimum(night * 0.55, day); C = day - H
    O = day * P.OUT_FRAC_NOON; H *= 1 - P.OUT_FRAC_NOON; C *= 1 - P.OUT_FRAC_NOON
    F = np.zeros_like(O)    # 籠城の限界で外に出た人（建物に戻れない）
    Z = np.zeros_like(O)
    t_first = np.full(O.shape, np.inf)
    night_done = np.zeros(O.shape, bool)
    # 最初の 30 分（micro.py）の結果を重ねる
    m = np.load(os.path.join(D, "micro.npz"))
    from micro import cell_latlon, N as MN
    lat, lon = cell_latlon()
    from micro import HANDOFF_MIN
    hk = f"{HANDOFF_MIN}"
    mz = m["Z_" + hk] + m["E_" + hk]; mo = m["O_" + hk]; mi = m["I_" + hk]
    acc = {}
    for a, la in enumerate(lat):
        for b, lo in enumerate(lon):
            r, c = latlon_rc(la, lo)
            s = acc.setdefault((r, c), [0.0, 0.0, 0.0])
            s[0] += mz[a, b]; s[1] += mo[a, b]; s[2] += mi[a, b]
    for (r, c), (z, o, i) in acc.items():
        tot = H[r, c] + C[r, c]
        hr = H[r, c] / tot if tot > 0 else 0.5
        Z[r, c] = z; O[r, c] = o; H[r, c] = i * hr; C[r, c] = i * (1 - hr)
        if z >= 1:
            t_first[r, c] = float(HANDOFF_MIN)
    pop0 = night.sum()
    # 動ける向き（4 近傍、陸地どうし、海峡は切る）
    canN = np.zeros(O.shape, bool); canE = np.zeros(O.shape, bool)
    canN[:-1] = land[:-1] & land[1:]; canE[:, :-1] = land[:, :-1] & land[:, 1:]
    for (la0, la1), (lo0, lo1) in STRAIT_CUTS:
        r0, c0 = latlon_rc(la0, lo0); _, c1 = latlon_rc(la0, lo1)
        canN[r0, c0:c1 + 1] = False
    # 海峡の道（1 km の鎖。中に人はいない）
    links = []
    for nm, a, b, L in LINKS:
        ra, ca = latlon_rc(*a); rb, cb = latlon_rc(*b)
        links.append(dict(name=nm, a=(ra, ca), b=(rb, cb), q=np.zeros(max(2, int(round(L)))), crossed=0.0, t_cross=None))
    cities = {k: latlon_rc(*v) for k, v in CITIES.items()}
    arrive = {}
    # 自衛隊
    sdf = dict(M=0.0, killed=0.0, lost=0.0, ammo=sc["ammo"])
    police_bit = 0.0
    p_kill = sum(math.comb(P.POLICE_ROUNDS, k) * P.POLICE_HIT ** k * (1 - P.POLICE_HIT) ** (P.POLICE_ROUNDS - k)
                 for k in range(P.HITS_TO_STOP, P.POLICE_ROUNDS + 1))
    police_left = night * P.POLICE_PER_POP_JAPAN * P.POLICE_ON_DUTY
    tok = np.zeros(O.shape, bool)
    r0, c0 = latlon_rc(35.5, 138.9); r1, c1 = latlon_rc(35.9, 139.95); tok[r0:r1, c0:c1] = True
    police_left[tok] = night[tok] * P.POLICE_PER_POP_TOKYO * P.POLICE_ON_DUTY
    police_kill = 0.0
    conv = dict(out=0.0, home=0.0, comm=0.0, forced=0.0)
    rows, snaps = [], {}
    D_w = (P.Z_WANDER ** 2) * sc["wander_tau"] / 2 / 1e6 * 60  # km²/分
    t = float(HANDOFF_MIN)
    T_END = 2 * DAY   # 細かい計算は 2 日まで。その先は coarse.py（ざっくり）
    wall = time.time()
    while t < T_END:
        dt = 1.0 if t < 6 * 60 else (5.0 if t < 2 * DAY else 10.0)
        # 計算する範囲（ゾンビのいる所の周り）
        zz = Z > 0.01
        for lk in links:
            if lk["q"].sum() > 0.01:
                zz[lk["a"]] = zz[lk["b"]] = True
        rr, cc = np.nonzero(zz)
        if len(rr) == 0:
            break
        pad = 60
        a0, a1 = max(0, rr.min() - pad), min(NR, rr.max() + pad + 1)
        b0, b1 = max(0, cc.min() - pad), min(NC, cc.max() + pad + 1)
        sl = (slice(a0, a1), slice(b0, b1))
        o, h, c_, f, z = O[sl], H[sl], C[sl], F[sl], Z[sl]
        tf = t_first[sl]; ld = land[sl]
        infested = z >= 1.0
        newly = infested & np.isinf(tf)
        tf[newly] = t
        # 夜になったら、まだ来ていない地域は家に帰る（常住人口の配置に戻す）
        if t >= 12 * 60:
            nd = night_done[sl]
            todo = (~nd) & np.isinf(tf)
            if todo.any():
                ns = night[sl]
                h[todo] = ns[todo] * 0.97; c_[todo] = ns[todo] * 0.03; o[todo] = 0
                nd[todo] = True
            night_done[sl] = nd
        # まだ来ていない地域の屋外の人
        cold = np.isinf(tf)
        target = out_frac(t, sc)
        tot = o + h + c_
        want = tot * target
        hr = np.where(h + c_ > 0, h / np.maximum(h + c_, 1e-9), 1)
        delta = np.where(cold, (want - o) * min(1.0, dt / 30.0), 0)
        o += delta; h -= delta * hr; c_ -= delta * (1 - hr)
        # ゾンビのいる所：屋外の人はかまれるか、建物に逃げ込む
        rho = (o + f) / area
        a_s = 0.06; hnd = 5 / 60
        rate = a_s * rho / (1 + a_s * hnd * rho)          # 1 体あたり 1 分あたり
        # 端数のゾンビ（1 体に満たない）はかまない
        bites = np.where(z >= 1, np.minimum((o + f) * 0.9, z * rate * dt), 0)
        fo = np.where(o + f > 0, o / np.maximum(o + f, 1e-9), 0)
        o -= bites * fo; f -= bites * (1 - fo)
        conv["out"] += float((bites * fo).sum()); conv["forced"] += float((bites * (1 - fo)).sum())
        hot = z >= 0.5
        shel = np.where(hot, o * min(1.0, dt / 3.0), 0)
        o -= shel; h += shel * hr; c_ += shel * (1 - hr)
        # 籠城：1 日 5% の建物が突破される（取り囲むゾンビの数で）
        nh = h / 2.1; nc = c_ / 200
        sh = np.minimum(1, z / np.maximum(2 * nh, 1e-9)); scm = np.minimum(1, z / np.maximum(20 * nc, 1e-9))
        p = P.BREACH_PER_DAY * dt / DAY
        bh = np.where(z >= 1, h * p * sh, 0); bc = np.where(z >= 1, c_ * p * scm, 0)
        h -= bh; c_ -= bc
        conv["home"] += float(bh.sum()); conv["comm"] += float(bc.sum())
        # 籠城の限界：ゾンビが来てから 7 日（家）・21 日（大きな建物）で外へ
        age = np.where(np.isfinite(tf), t - tf, -1.0)
        out_h = np.where((age >= P.HOME_HOLD_DAYS * DAY) & (z >= 0.5), h * min(1, dt / DAY), 0)
        out_c = np.where((age >= P.COMM_HOLD_DAYS * DAY) & (z >= 0.5), c_ * min(1, dt / DAY), 0)
        # 逃げ切った人（ゾンビのいない地域）は、その地域の建物に受け入れられる（1 時間ほどで）
        safe = np.isinf(tf) & (z < 0.01)
        taken = np.where(safe, f * min(1, dt / 60.0), 0)
        f -= taken; h += taken
        h -= out_h; c_ -= out_c; f += out_h + out_c
        # 警察官（その地域の勤務中の警察官が最初に向かい、かまれる）
        pl = police_left[sl]
        eng = np.where(newly | (infested & (pl > 0)), pl * min(1, dt / 30.0), 0)
        kills_p = np.minimum(z, eng * p_kill)
        pl -= eng; police_left[sl] = pl
        z += -kills_p + eng * 0.9
        police_kill += float(kills_p.sum()); police_bit += float(eng.sum() * 0.9)
        # 自衛隊（武器の使用が許されたあと、前線で）
        z += bites + bh + bc
        if t >= sc["sdf_armed_h"] * 60 and sdf["ammo"] > 0:
            hrs = (t - sc["sdf_armed_h"] * 60) / 60
            # 投入される隊員（A）：12 時間で 5,000 人 → 2 日で 3 万人（東部方面隊の規模）→ 1 週間で 10 万人（全国から）
            plan = min(100000.0, 5000 + 25000 * min(1, hrs / 36) + 70000 * max(0, min(1, (hrs - 36) / 132)))
            sdf["M"] = max(0.0, plan - sdf["lost"])
            front = infested & ~(np.roll(infested, 1, 0) & np.roll(infested, -1, 0) & np.roll(infested, 1, 1) & np.roll(infested, -1, 1))
            zf = float((z * front).sum())
            if zf > 0 and sdf["M"] > 0:
                cap = sdf["M"] * (P.SDF_ROUNDS_PER_MIN * P.SDF_HIT / P.HITS_TO_STOP) * 0.1 * dt  # 実際に撃てるのは 1 割の時間
                kill = min(cap, min(0.5, 0.05 * dt) * zf, sdf["ammo"] * P.SDF_HIT / P.HITS_TO_STOP)
                # 前線のゾンビが隊員より多いほど、取りつかれてかまれる（A）
                lost = min(sdf["M"], sdf["M"] * 0.0005 * dt * zf / (zf + sdf["M"] * 20))
                z += z * front * ((lost - kill) / zf)
                sdf["killed"] += kill; sdf["ammo"] -= kill * P.HITS_TO_STOP / P.SDF_HIT
                sdf["lost"] += lost
        # 動く：ゾンビは見える人へ全力で、いなければうろつく。外に出た人はゾンビから離れる
        cn = canN[sl]; ce = canE[sl]
        z_new = move(z, o + f, h + c_, cn, ce, dt, D_w, t - tf)
        f_new = flee(f, z, cn, ce, dt)
        O[sl], H[sl], C[sl], F[sl], Z[sl], t_first[sl] = o, h, c_, f_new, z_new, tf
        # 海峡の道
        for lk in links:
            if sc["link_close_day"] is not None and t >= sc["link_close_day"] * DAY:
                continue
            # 道の中はうろつき（1 次元の拡散）だけ。端のマスから、隣のマスへ動くのと同じ割合で入る
            q = lk["q"]; fr = min(0.2, D_w * dt / 1.0)
            inA = Z[lk["a"]] * fr; inB = Z[lk["b"]] * fr
            new = q.copy()
            new[1:] += fr * q[:-1]; new[:-1] += fr * q[1:]; new[1:] -= fr * q[1:]; new[:-1] -= fr * q[:-1]
            outa, outb = fr * q[0], fr * q[-1]
            new[0] += inA - outa; new[-1] += inB - outb
            Z[lk["a"]] += outa - inA; Z[lk["b"]] += outb - inB
            lk["q"] = np.maximum(new, 0)
            lk["crossed"] += outb
            if lk["t_cross"] is None and lk["crossed"] >= 1:
                lk["t_cross"] = t
        t += dt
        for k, (r, c) in cities.items():
            if k not in arrive and Z[r, c] >= 1:
                arrive[k] = t
        if abs(t % 60) < dt / 2 or t < 60 and abs(t % 10) < dt / 2:
            inf = Z >= 1
            human_left = float((O + H + C + F).sum())
            rows.append((t, float(Z.sum()), float(inf.sum() * area), human_left, float(O.sum() + F.sum()),
                         float(H.sum()), float(C.sum()), conv["out"], conv["home"], conv["comm"], conv["forced"],
                         sdf["M"], sdf["killed"], sdf["lost"], police_kill, police_bit))
        for hh in SNAP_H:
            if abs(t - hh * 60) < dt / 2:
                snaps[f"Z_{hh}"] = Z.astype(np.float32)
                snaps[f"H_{hh}"] = (H + C).astype(np.float32)
        if abs(t % (2 * DAY)) < dt / 2:
            print(f"  {name}: {t/DAY:.0f} 日目 ゾンビ {Z.sum():,.0f}（{time.time()-wall:.0f} 秒）", flush=True)
    np.savez_compressed(os.path.join(D, f"macro_{name}.npz"), rows=np.array(rows),
                        arrive=np.array([(k, v) for k, v in arrive.items()], dtype=object),
                        links=np.array([(lk["name"], lk["t_cross"] if lk["t_cross"] else -1, lk["crossed"]) for lk in links], dtype=object),
                        pop0=pop0, **snaps)
    # 2 日目の状態（coarse.py が続きを計算する）
    np.savez_compressed(os.path.join(D, f"state_{name}.npz"), t=t, O=O, H=H, C=C, F=F, Z=Z, t_first=t_first,
                        police_left=police_left, sdf=np.array([sdf["M"], sdf["killed"], sdf["lost"], sdf["ammo"]]),
                        conv=np.array([conv["out"], conv["home"], conv["comm"], conv["forced"]]),
                        police=np.array([police_kill, police_bit]),
                        linkq=np.array([lk["q"] for lk in links], dtype=object),
                        arrive=np.array([(k, v) for k, v in arrive.items()], dtype=object))
    return rows, arrive, links


def okmask(cn, ce, ax, shift):
    if shift == 1:
        okm = (cn if ax == 0 else ce).copy()
    else:
        okm = np.roll(cn if ax == 0 else ce, 1, ax)
    # 計算範囲の端で反対側に回り込まない
    if ax == 0:
        okm[-1 if shift == 1 else 0] = False
    else:
        okm[:, -1 if shift == 1 else 0] = False
    return okm


def move(z, exposed, shelter, cn, ce, dt, D_w, age):
    """ゾンビの移動（マスをまたぐ動き）。

    全力で追うのは人が見えている 75 m の中だけ（それはマスの中のかみつきの速さに入っている）。
    マスをまたぐ動きは、うろつき（拡散）＋人の多い方へ寄っていく動き。寄る速さは、屋外の人が多いほど
    速くなる（人が途切れず見えていれば、追う・かむ・次を見つける、をくり返して前へ進む）。上限は全力。
    """
    area = 1.045
    busy = np.minimum(1, exposed / np.maximum(z, 1e-9) * 0.2)   # 近くでかむ相手がいれば動かない
    free = z * (1 - busy)
    g = np.log1p((exposed + 0.02 * shelter) / (z + 1))
    rho_n = np.maximum.reduce([np.roll(exposed, s, a) for a in (0, 1) for s in (1, -1)]) / area
    v_seek = P.Z_WANDER + (P.Z_SPRINT - P.Z_WANDER) * np.minimum(1, rho_n / 2000.0)   # m/s
    out = z.copy()
    fr_d = min(0.2, D_w * dt / 1.0)
    fracs = []
    for ax in (0, 1):
        for shift in (1, -1):
            okm = okmask(cn, ce, ax, shift)
            d = np.clip(np.roll(g, -shift, ax) - g, 0, None)
            # 人の方へ寄る動きは、ゾンビがそのマスを横切る時間（1 km ÷ 速さ）が経ってから（端数が先へ染み出さない）
            ready = np.nan_to_num(age, nan=-1, neginf=-1, posinf=-1) >= 1000.0 / v_seek / 60
            fracs.append((ax, shift, np.where(okm, v_seek * 60 / 1000 * dt * np.minimum(1, d) * ready + fr_d, 0)))
    tot = sum(f for _, _, f in fracs)
    s = np.where(tot > 0.9, 0.9 / np.maximum(tot, 1e-9), 1.0)   # 1 ステップで出ていくのは 9 割まで
    for ax, shift, f in fracs:
        mv = free * f * s
        out -= mv
        out += np.roll(mv, shift, ax)
    return np.maximum(out, 0)


def flee(f, z, cn, ce, dt):
    gz = np.log1p(z)
    out = f.copy()
    v = 4.0 / 60 * dt  # 歩いて 4 km/時
    for ax in (0, 1):
        for shift in (1, -1):
            okm = okmask(cn, ce, ax, shift)
            d = np.clip(gz - np.roll(gz, -shift, ax), 0, None)
            frac = np.where(okm, np.minimum(0.22, v * np.minimum(1, d)), 0)
            mv = f * frac
            out -= mv; out += np.roll(mv, shift, ax)
    return np.maximum(out, 0)


if __name__ == "__main__":
    names = sys.argv[1:] or ["base"]
    for nm in names:
        rows, arrive, links = run(nm)
        print(nm, "完了。都市に着いた時刻（時間）：", {k: round(v / 60, 1) for k, v in sorted(arrive.items(), key=lambda x: x[1])})
        print("海峡：", [(lk["name"], None if lk["t_cross"] is None else round(lk["t_cross"] / 1440, 1)) for lk in links])
