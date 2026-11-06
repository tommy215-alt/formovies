"""3 日目以降：8 km 四方のブロック・1 時間きざみのざっくりした計算（macro.py の 2 日目の状態から続ける）。

ルールは macro.py と同じ（突破 5%／日、籠城の限界 7 日・21 日、家を出た人がかまれる・逃げる、自衛隊、海峡の道）。
使い方：python coarse.py base close ...（close は base の 2 日目の状態から、橋とトンネルを封鎖して続ける）
出力：data/coarse_<名>.npz
"""
import math, os, sys
import numpy as np
import params as P
from build_grid import latlon_rc, NR, NC
from macro import SCEN, LINKS, STRAIT_CUTS, CITIES, DAY

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
K = 8                      # 1 ブロック＝8×8 メッシュ（約 7.4×9.0 km）
BR, BC = NR // K, NC // K
AREA = 1.045 * K * K
DX = 8.2                   # km（ブロックの間の距離の目安）
SNAP_D = [3, 5, 7, 8, 10, 14, 21, 22, 30, 45, 60, 90]
STATE_OF = {"close": "base"}


def blk(a, f=np.sum):
    a = a[:BR * K, :BC * K].reshape(BR, K, BC, K)
    return f(f(a, axis=3), axis=1)


def run(name):
    sc = SCEN[name]
    s = np.load(os.path.join(D, f"state_{STATE_OF.get(name, name)}.npz"), allow_pickle=True)
    g = np.load(os.path.join(D, "grid.npz"))
    land = g["land"]
    H = blk(s["H"]); C = blk(s["C"]); F = blk(s["F"] + s["O"]); Z = blk(s["Z"])
    tf = blk(s["t_first"], np.min)
    pl = blk(s["police_left"])
    bland = blk(land.astype(np.int32)) > 0
    # ブロックの間を動けるか（細かい格子の陸のつながりから）
    canN = np.zeros(land.shape, bool); canE = np.zeros(land.shape, bool)
    canN[:-1] = land[:-1] & land[1:]; canE[:, :-1] = land[:, :-1] & land[:, 1:]
    for (la0, la1), (lo0, lo1) in STRAIT_CUTS:
        r0, c0 = latlon_rc(la0, lo0); _, c1 = latlon_rc(la0, lo1)
        canN[r0, c0:c1 + 1] = False
    bN = np.zeros((BR, BC), bool); bE = np.zeros((BR, BC), bool)
    for i in range(BR - 1):
        bN[i] = canN[i * K + K - 1, :BC * K].reshape(BC, K).any(1)
    for j in range(BC - 1):
        bE[:, j] = canE[:BR * K, j * K + K - 1].reshape(BR, K).any(1)
    # ブロックが細い海峡をまたぐので、島（海峡を切った陸のつながり）ごとに分け、別の島のブロックの間は動けない
    bisl = block_islands(land, canN, canE)
    bN[:-1] &= bisl[:-1] == bisl[1:]; bE[:, :-1] &= bisl[:, :-1] == bisl[:, 1:]
    links = []
    for (nm, a, b, L), q in zip(LINKS, s["linkq"]):
        ra, ca = latlon_rc(*a); rb, cb = latlon_rc(*b)
        links.append(dict(name=nm, a=(ra // K, ca // K), b=(rb // K, cb // K), q=np.array(q, float), crossed=0.0, t_cross=None))
    sdf = dict(zip(("M", "killed", "lost", "ammo"), s["sdf"].tolist()))
    conv = dict(zip(("out", "home", "comm", "forced"), s["conv"].tolist()))
    police_kill, police_bit = s["police"].tolist()
    arrive = {k: float(v) for k, v in s["arrive"]}
    cities = {k: (latlon_rc(*v)[0] // K, latlon_rc(*v)[1] // K) for k, v in CITIES.items()}
    p_kill = sum(math.comb(P.POLICE_ROUNDS, k) * P.POLICE_HIT ** k * (1 - P.POLICE_HIT) ** (P.POLICE_ROUNDS - k)
                 for k in range(P.HITS_TO_STOP, P.POLICE_ROUNDS + 1))
    D_w = (P.Z_WANDER ** 2) * sc["wander_tau"] / 2 / 1e6 * 3600   # km²/時
    t = float(s["t"]); dt = 60.0
    rows, snaps = [], {}
    while t < 90 * DAY:
        inf = Z >= 1
        newly = inf & np.isinf(tf); tf[newly] = t
        hr = np.where(H + C > 0, H / np.maximum(H + C, 1e-9), 1)
        # 籠城：突破 5%／日（取り囲むゾンビの数で）
        sh = np.minimum(1, Z / np.maximum(2 * H / 2.1, 1e-9)); scm = np.minimum(1, Z / np.maximum(20 * C / 200, 1e-9))
        p = P.BREACH_PER_DAY * dt / DAY
        bh = np.where(Z >= 1, H * p * sh, 0); bc = np.where(Z >= 1, C * p * scm, 0)
        H -= bh; C -= bc; conv["home"] += bh.sum(); conv["comm"] += bc.sum()
        # 籠城の限界
        age = np.where(np.isfinite(tf), t - tf, -1.0)
        oh = np.where((age >= P.HOME_HOLD_DAYS * DAY) & (Z >= 0.5), H * dt / DAY, 0)
        oc = np.where((age >= P.COMM_HOLD_DAYS * DAY) & (Z >= 0.5), C * dt / DAY, 0)
        H -= oh; C -= oc; F += oh + oc
        # 外にいる人がかまれる
        rho = F / AREA
        rate = 0.06 * rho / (1 + 0.06 * (5 / 60) * rho)
        bites = np.where(Z >= 1, np.minimum(F * 0.9, Z * rate * dt), 0)
        F -= bites; conv["forced"] += bites.sum()
        # 逃げ切った人は受け入れられる
        safe = np.isinf(tf) & (Z < 0.01)
        F_in = np.where(safe, F, 0); F -= F_in; H += F_in
        # 警察官
        eng = np.where(inf & (pl > 0), pl * min(1, dt / 30.0), 0)
        kp = np.minimum(Z, eng * p_kill); pl -= eng
        Z += bites + bh + bc - kp + eng * 0.9
        police_kill += kp.sum(); police_bit += eng.sum() * 0.9
        # 自衛隊
        if t >= sc["sdf_armed_h"] * 60 and sdf["ammo"] > 0:
            hrs = (t - sc["sdf_armed_h"] * 60) / 60
            plan = min(100000.0, 5000 + 25000 * min(1, hrs / 36) + 70000 * max(0, min(1, (hrs - 36) / 132)))
            sdf["M"] = max(0.0, plan - sdf["lost"])
            front = inf & ~(np.roll(inf, 1, 0) & np.roll(inf, -1, 0) & np.roll(inf, 1, 1) & np.roll(inf, -1, 1))
            zf = float((Z * front).sum())
            if zf > 0 and sdf["M"] > 0:
                cap = sdf["M"] * (P.SDF_ROUNDS_PER_MIN * P.SDF_HIT / P.HITS_TO_STOP) * 0.1 * dt
                kill = min(cap, 0.5 * zf, sdf["ammo"] * P.SDF_HIT / P.HITS_TO_STOP)
                lost = min(sdf["M"], sdf["M"] * 0.0005 * dt * zf / (zf + sdf["M"] * 20))
                Z += Z * front * ((lost - kill) / zf)
                sdf["killed"] += kill; sdf["ammo"] -= kill * P.HITS_TO_STOP / P.SDF_HIT; sdf["lost"] += lost
        # 動く
        Z = move(Z, F, H + C, bN, bE, dt, D_w, age)
        F = flee(F, Z, bN, bE, dt)
        # 海峡の道（1 km の鎖）
        if not (sc["link_close_day"] is not None and t >= sc["link_close_day"] * DAY):
            fr = min(0.45, D_w * dt / 60 / 1.0)
            for lk in links:
                q = lk["q"]
                inA = Z[lk["a"]] / (K * K) * fr; inB = Z[lk["b"]] / (K * K) * fr
                new = q.copy()
                new[1:] += fr * q[:-1]; new[:-1] += fr * q[1:]; new[1:] -= fr * q[1:]; new[:-1] -= fr * q[:-1]
                oa, ob = fr * q[0], fr * q[-1]
                new[0] += inA - oa; new[-1] += inB - ob
                Z[lk["a"]] += oa - inA; Z[lk["b"]] += ob - inB
                lk["q"] = np.maximum(new, 0); lk["crossed"] += ob
                if lk["t_cross"] is None and lk["crossed"] >= 1:
                    lk["t_cross"] = t
        Z[~bland] = 0
        t += dt
        for k, rc in cities.items():
            if k not in arrive and Z[rc] >= AREA:   # 1 km² あたり 1 体（1 km の計算と同じ目安）
                arrive[k] = t
        if abs(t % 360) < 1:
            rows.append((t, Z.sum(), (Z >= AREA).sum() * AREA, (H + C + F).sum(), F.sum(), H.sum(), C.sum(),
                         conv["out"], conv["home"], conv["comm"], conv["forced"], sdf["M"], sdf["killed"], sdf["lost"],
                         police_kill, police_bit))
        for d_ in SNAP_D:
            if abs(t - d_ * DAY) < 1:
                snaps[f"Z_{d_}d"] = Z.astype(np.float32); snaps[f"S_{d_}d"] = (H + C).astype(np.float32)
    np.savez_compressed(os.path.join(D, f"coarse_{name}.npz"), rows=np.array(rows),
                        arrive=np.array(list(arrive.items()), dtype=object),
                        links=np.array([(lk["name"], lk["t_cross"] or -1, lk["crossed"]) for lk in links], dtype=object), **snaps)
    return rows, arrive, links


def block_islands(land, canN, canE):
    """海峡を切った陸のつながりで島に番号を付け、ブロックごとに一番多い島の番号を返す。"""
    from collections import deque
    lab = np.zeros(land.shape, np.int32); n = 0
    for r0, c0 in zip(*np.nonzero(land)):
        if lab[r0, c0]:
            continue
        n += 1; lab[r0, c0] = n; q = deque([(r0, c0)])
        while q:
            r, c = q.popleft()
            for rr, cc, ok in ((r + 1, c, canN[r, c]), (r - 1, c, r > 0 and canN[r - 1, c]),
                               (r, c + 1, canE[r, c]), (r, c - 1, c > 0 and canE[r, c - 1])):
                if ok and not lab[rr, cc]:
                    lab[rr, cc] = n; q.append((rr, cc))
    size = np.bincount(lab.ravel())
    b = lab[:BR * K, :BC * K].reshape(BR, K, BC, K).transpose(0, 2, 1, 3).reshape(BR, BC, K * K)
    out = np.zeros((BR, BC), np.int32)
    for i, j in zip(*np.nonzero((b > 0).any(2))):
        v = b[i, j][b[i, j] > 0]
        ids, cnt = np.unique(v, return_counts=True)
        out[i, j] = ids[np.argmax(cnt * np.log1p(size[ids]))]   # 一番多い島（同じくらいなら大きな島）
    return out


def _dirs(bN, bE):
    for ax in (0, 1):
        for shift in (1, -1):
            can = bN if ax == 0 else bE
            okm = can.copy() if shift == 1 else np.roll(can, 1, ax)
            if ax == 0:
                okm[-1 if shift == 1 else 0] = False
            else:
                okm[:, -1 if shift == 1 else 0] = False
            yield ax, shift, okm


def move(z, exposed, shelter, bN, bE, dt, D_w, age):
    busy = np.minimum(1, exposed / np.maximum(z, 1e-9) * 0.2)
    free = z * (1 - busy)
    g = np.log1p((exposed + 0.02 * shelter) / (z + 1))
    rho_n = np.maximum.reduce([np.roll(exposed, s, a) for a in (0, 1) for s in (1, -1)]) / AREA
    v = (P.Z_WANDER + (P.Z_SPRINT - P.Z_WANDER) * np.minimum(1, rho_n / 2000.0)) * 3.6   # km/時
    fr_d = D_w * dt / 60 / DX ** 2
    fr = []
    for ax, shift, okm in _dirs(bN, bE):
        d = np.clip(np.roll(g, -shift, ax) - g, 0, None)
        ready = age >= DX / v * 60   # ブロックを横切る時間が経ってから
        fr.append((ax, shift, np.where(okm, v * dt / 60 / DX * np.minimum(1, d) * ready + fr_d, 0)))
    tot = sum(f for _, _, f in fr)
    s = np.where(tot > 0.9, 0.9 / np.maximum(tot, 1e-9), 1.0)
    out = z.copy()
    for ax, shift, f in fr:
        mv = free * f * s; out -= mv; out += np.roll(mv, shift, ax)
    return np.maximum(out, 0)


def flee(f, z, bN, bE, dt):
    gz = np.log1p(z); out = f.copy()
    for ax, shift, okm in _dirs(bN, bE):
        d = np.clip(gz - np.roll(gz, -shift, ax), 0, None)
        frac = np.where(okm, np.minimum(0.22, 4.0 * dt / 60 / DX * np.minimum(1, d)), 0)
        mv = f * frac; out -= mv; out += np.roll(mv, shift, ax)
    return np.maximum(out, 0)


if __name__ == "__main__":
    for nm in sys.argv[1:] or ["base"]:
        rows, arrive, links = run(nm)
        print(nm, "ゾンビ（90 日）", f"{rows[-1][1]:,.0f}", "生き残り", f"{rows[-1][3]:,.0f}")
