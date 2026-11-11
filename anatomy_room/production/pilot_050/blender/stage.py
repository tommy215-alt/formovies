"""pilot_050 のショットで共通に使う部品（時計・光・歩き・沿道の応援・湯気・看板・机・バケツ）。"""
from common import *
import trex, people, city
from city import RW, SW
from gait import PERIOD

V = PLAN["v"]; WRV = 42195. / PLAN["wr"]          # ティラノ 秒速 5.4 m、先頭 秒速 5.885 m
MOUTH = (0, 5.25, 4.13)                           # 口の先（置いた姿勢）
Z = Vector((0, 0, 1))


def shot_clock(k):
    """ショットの中の秒 → 号砲からの秒（plan.py の c）"""
    s = SPLAN[k]; c = s["c"]; d = s["dur"]
    def f(t):
        u = clamp(t / d)
        for (u0, c0), (u1, c1) in zip(c, c[1:]):
            if u <= u1 or (u1, c1) == tuple(c[-1]):
                return c0 + (c1 - c0) * clamp((u - u0) / max(1e-9, u1 - u0))
        return c[-1][1]
    return f


def base(sun_el=55., sun_rot=150., energy=6.0, exposure=-4.5, haze=(.8, .86, .93), haze_k=.9, d0=150., d1=4000.):
    """ショットの最初に呼ぶ：前のショットの物を消し、昼の光にする"""
    env_clear(); sky.set(0, sun_el, sun_rot, energy); sc.view_settings.exposure = exposure; set_haze(haze, haze_k, d0, d1)
    sc.render.use_motion_blur = False; trex.medal(False)
    for s_ in (trex.T["xray"], esock(trex.T["bone"])):
        s_.id_data.animation_data_clear()
    trex.xray(0, 0)


def walker(amp_fn, y0=0., ph0=0., T=14.):
    """歩幅 amp(t) で歩いたときの、腰の y・周期の位置・歩幅（速さは 5.4·amp、足がすべらないよう数値で積分）"""
    dt = 1 / 240; ts = np.arange(int(T / dt) + 2) * dt; a = np.array([amp_fn(x) for x in ts])
    ys = y0 + np.concatenate([[0.], np.cumsum(V * (a[:-1] + a[1:]) / 2 * dt)])
    def f(t):
        t = max(0., t); return float(np.interp(t, ts, ys)), ph0 + t / PERIOD, float(amp_fn(t))
    return f


def crowd(name, ya, yb, sides=(-1, 1), lod=0, seed=1, cheer=.7, fill=.8, rows=(1.0, 2.3, 3.1, 3.9), wave=1.0, gaps=()):
    """沿道の応援（歩道に立って道を向く）。rows：車道の端からの距離"""
    rnd = np.random.default_rng(seed); P = []; H = []
    for s in sides:
        for xr in rows:
            for y in np.arange(ya, yb, .62):
                if rnd.random() > fill or any(g[0] == s and g[1] <= y <= g[2] for g in gaps):
                    continue
                P.append((s * (RW + xr + rnd.uniform(-.12, .12)), y + rnd.uniform(-.2, .2))); H.append(s * math.pi / 2 + rnd.normal(0, .3))
    if not P:
        return None
    md = np.where(rnd.random(len(P)) < cheer, 1, 2)
    return people.split(name, P, heading=np.array(H), mode=md, seed=seed + 5, lod=lod, bib=False, wave=wave)


def runners(name, P, speed, seed=1, lod=0, **kw):
    return people.People(name, P, heading=0.0, speed=speed, mode=kw.pop("mode", 0), seed=seed, lod=lod, **kw)


class Steam:
    """湯気：puff を n 個、src(t)（世界座標）から順に出して上へ流す。a_ の中で key(t, f) を呼ぶ"""
    def __init__(self, name, n, src, life=2.2, r=.8, dens=.03, rise=.9, t0=0., t1=1e9, col=(.93, .93, .96), drift=(0, 0, 0), seed=7):
        self.p = [puff(f"{name}{i}", (0, 0, -60), r, col, dens) for i in range(n)]; self.n = n; self.src = src; self.life = life; self.r = r; self.k = dens * 2.2
        self.rise = rise; self.t0 = t0; self.t1 = t1; self.drift = Vector(drift); self.rnd = np.random.default_rng(seed).uniform(-1, 1, (n, 4))

    def key(self, t, f):
        for i, (o, sock) in enumerate(self.p):
            ph = (t - self.t0) / self.life - i / self.n; k = math.floor(ph); born = self.t0 + (k + i / self.n) * self.life; age = t - born
            if ph < 0 or born > self.t1:
                keyp(o, f, loc=(0, 0, -60), scale=.01); key_v(sock, 0., f); continue
            u = age / self.life; rr = self.rnd[i]
            p = Vector(self.src(born)) + Vector((rr[0] * .35, rr[1] * .35, 0)) + (Z * self.rise + self.drift) * age + Vector((rr[2], rr[3], 0)) * .25 * age
            keyp(o, f, loc=p, scale=self.r * (.45 + .85 * u) * (1 + .15 * rr[2])); key_v(sock, self.k * max(0., math.sin(math.pi * min(1, u * 1.15))) ** .8 * (1 - .5 * u), f)


def board(name, tex, c, w, h, n=(1, 0, 0), poles=True, z0=0.):
    """絵の板（tex/<tex>.png）。c：中心、n：読む人のいる向き（水平）。poles：両端に柱"""
    n = Vector(n).normalized(); r = (-n).cross(Z); c = Vector(c); im = img_mat(tex, .6)
    P = [c - r * w / 2 - Z * h / 2, c + r * w / 2 - Z * h / 2, c + r * w / 2 + Z * h / 2, c - r * w / 2 + Z * h / 2]
    o = mesh_obj(name, quad("q", [p + n * .03 for p in P], im), [im])
    bk = mat("board_back", (.85, .85, .86), .6); mesh_obj(name + "_b", quad("q", [p - n * .005 for p in P], bk), [bk])
    if poles:
        dk = mat("pole", (.12, .13, .14), .45, .6); tv, tf = city._cyl(8, 1.0)
        instances(name + "_p", tv, tf, [(*(c + r * s * (w / 2 + .04))[:2], z0, .04, .04, c.z + h / 2 - z0, 0, 0, 0) for s in (-1, 1)], [dk])
    return o


def tables(name, x, ya, yb, cups=True, side=-1):
    """給水の机（道の端、長さ 1.8 m ずつ）と紙コップ"""
    top = []; leg = []; cup = []; rnd = np.random.default_rng(4)
    for y in np.arange(ya, yb, 2.0):
        top.append((x, y + .9, .74, .7, 1.8, .04, 0, 0, 0))
        for dx in (-.3, .3):
            for dy in (.08, 1.72):
                leg.append((x + dx, y + dy, .36, .035, .035, .72, 0, 0, 0))
        if cups:
            for i in range(4):
                for j in range(13):
                    if rnd.random() < .85:
                        cup.append((x - .24 + i * .16, y + .12 + j * .13, .76, .034, .034, .09, 0, 0, 0))
    instances(name, CUBE_V, CUBE_F, top, [mat("table", (.88, .88, .86), .5)]); instances(name + "_l", CUBE_V, CUBE_F, leg, [mat("pole", (.12, .13, .14), .45, .6)])
    if cup:
        tv, tf = city._cyl(8, 1.25); city._smooth(instances(name + "_c", tv, tf, cup, [mat("cup", (.93, .93, .9), .5)]))


def bucket(name, r=.3, h=.46, col=(.05, .25, .75)):
    """バケツ（原点は中心）。上の面は水"""
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r * .8, radius2=r, depth=h)
    wm = mat("water_top", (.35, .6, .8), .08); bm.faces.ensure_lookup_table()
    for fc in bm.faces:
        fc.material_index = 1 if (fc.normal.z > .9) else 0
        fc.smooth = fc.normal.z < .9 and fc.normal.z > -.9
    return mesh_obj(name, bm, [mat(name + "_m", col, .35), wm])


def platform(name, x, y, h, w=1.5, d=1.5, open_side=-1):
    """ティラノ用の高い給水台（足場）。open_side：手すりを付けない側（ティラノの側、-1 で -X）"""
    dk = mat("pole", (.12, .13, .14), .45, .6); P = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.append((x + sx * w / 2, y + sy * d / 2, h / 2, .07, .07, h, 0, 0, 0))
    for z in (h * .35, h * .7):
        for sx in (-1, 1):
            P.append((x + sx * w / 2, y, z, .04, d, .04, 0, 0, 0))
        for sy in (-1, 1):
            P.append((x, y + sy * d / 2, z, w, .04, .04, 0, 0, 0))
    P.append((x, y, h - .04, w + .1, d + .1, .08, 0, 0, 0))
    for sy in (-1, 1):                                   # 手すり（ティラノの側は空ける）
        P.append((x, y + sy * d / 2, h + 1.0, w, .04, .04, 0, 0, 0)); P.append((x, y + sy * d / 2, h + .5, w, .04, .04, 0, 0, 0))
        for sx in (-1, 1):
            P.append((x + sx * w / 2, y + sy * d / 2, h + .5, .04, .04, 1.0, 0, 0, 0))
    P.append((x - open_side * w / 2, y, h + 1.0, .04, d, .04, 0, 0, 0))
    instances(name, CUBE_V, CUBE_F, P, [dk])


def hands(p, i=0):
    """People の i 番目の人の両手の先（メッシュの座標、p.o.location を足す前）"""
    return [Vector(p.V[i, p.off[k] + 2 * 8 + 1]) for k in ("faL", "faR")]


def aim_above(pos, head, deg, zh=5.2):
    """大きな札のあるショット用：頭の上（zh）が画面の中心より deg 度だけ上に来るよう、カメラの向く点を返す"""
    pos = Vector(pos); head = Vector(head); d = math.hypot(head.x - pos.x, head.y - pos.y); el = math.atan2(zh - pos.z, d) - math.radians(deg)
    return Vector((head.x, head.y, pos.z + d * math.tan(el)))
