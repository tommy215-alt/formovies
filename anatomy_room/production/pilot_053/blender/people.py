"""pilot_050 の人（顔のないピクトグラム：頭・胴・腕 2 節・脚 2 節）。N 人分を 1 つのメッシュにして、コマごとに numpy で形を作り直す。
mode：0＝走る、1＝立って応援（両手を上げて振る）、2＝立つ、3＝走りながら両手を上げる（t3 秒から）。lod=1 は遠く用（胴と頭だけ）。色は頂点の色 "Col"。
実在の人・大会のゼッケンは写さない（白い札だけ）。"""
from common import *

L_TH, L_SH, L_UA, L_FA, L_TO = .44, .44, .27, .25, .5
SHIRTS = [(.85, .1, .08), (.95, .5, .05), (.95, .8, .1), (.15, .55, .2), (.1, .45, .8), (.08, .15, .5), (.55, .15, .6), (.9, .9, .88), (.9, .3, .5), (.1, .65, .65)]
SKIN = (.62, .4, .27)


def _capsule(seg=8):
    """軸 z の 0→1、半径 1 の筒。両端はとがった丸み（cap＝軸の向きに半径の何倍のびるか）。返り値：(tx, ty, tz, cap) と面"""
    v = []; f = []
    for tz in (0., 1.):
        for i in range(seg):
            a = 2 * math.pi * i / seg; v.append((math.cos(a), math.sin(a), tz, 0.))
    v.append((0, 0, 0., -1.)); v.append((0, 0, 1., 1.))
    for i in range(seg):
        j = (i + 1) % seg; f.append((i, j, seg + j, seg + i)); f.append((2 * seg, j, i)); f.append((2 * seg + 1, seg + i, seg + j))
    return np.array(v, float), f


def _ico(sub):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    v = np.array([tuple(x.co) for x in bm.verts], float); f = [tuple(x.index for x in fc.verts) for fc in bm.faces]; bm.free(); return v, f


def _pmat():
    if "people" in MATS:
        return MATS["people"]
    m = bpy.data.materials.new("people"); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]
    at = t.nodes.new("ShaderNodeAttribute"); at.attribute_name = "Col"; t.links.new(at.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = .62; add_haze(m, 150., 4000., .8); MATS["people"] = m; return m


class People:
    def __init__(self, name, P0, heading=0.0, speed=0.0, mode=0, seed=1, delay=None, lod=0, accel=1.6, shirts=None, bib=True, wave=1.0, sub=None):
        """sub：N 人のうち、この物に入れる人（split() で動く人と動かない人を分ける。一人ひとりの色・大きさ・動きは分けないときと同じ）"""
        P0 = np.asarray(P0, float).reshape(-1, 2); N = len(P0); rnd = np.random.default_rng(seed); self.lod = lod
        self.P0 = P0; self.h = np.broadcast_to(np.asarray(heading, float), (N,)).copy(); self.sp = np.broadcast_to(np.asarray(speed, float), (N,)).copy()
        self.mode = np.broadcast_to(np.asarray(mode), (N,)).copy(); self.free = delay is None; self.delay = np.zeros(N) if delay is None else np.broadcast_to(np.asarray(delay, float), (N,)).copy()
        self.T = accel; self.t3 = 0.0; self.ph = rnd.uniform(0, 6.28, N); self.s = rnd.uniform(.9, 1.08, N); self.wf = rnd.uniform(4.5, 7.5, N) * wave; self.one = rnd.random(N) < .35
        pal = np.array(shirts if shirts is not None else SHIRTS); sh = pal[rnd.integers(0, len(pal), N)]; pants = np.array([(.03, .03, .04), (.05, .06, .12), (.12, .03, .03)])[rnd.integers(0, 3, N)]
        skin = np.array(SKIN) * rnd.uniform(.7, 1.15, (N, 1))
        if sub is not None:
            for k in ("P0", "h", "sp", "mode", "delay", "ph", "s", "wf", "one"):
                setattr(self, k, getattr(self, k)[sub])
            sh, pants, skin = sh[sub], pants[sub], skin[sub]; N = int(np.sum(sub))
        self.N = N; self.SL = np.maximum(.9, self.sp / 1.45) * 1.0
        cv, cf = _capsule(8 if lod == 0 else 6); hv, hf = _ico(1 if lod else 2)
        self.cv = cv; self.hv = hv; nc = len(cv); nh = len(hv)
        parts = ["torso"] + ([] if lod else ["thL", "shL", "thR", "shR", "uaL", "faL", "uaR", "faR"])
        self.off = {}; o = 0; faces = []
        for p in parts:
            self.off[p] = o; faces += [tuple(k + o for k in fc) for fc in cf]; o += nc
        self.off["head"] = o; faces += [tuple(k + o for k in fc) for fc in hf]; o += nh
        self.bib = bib and not lod
        if self.bib:
            self.off["bib"] = o; faces.append((o, o + 1, o + 2, o + 3)); o += 4
        nv = o; self.nv = nv
        allf = [tuple(i * nv + k for k in fc) for i in range(N) for fc in faces]
        me = bpy.data.meshes.new(name); me.from_pydata(np.zeros((N * nv, 3)).tolist(), [], allf); me.update()
        me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool)); me.materials.append(_pmat())
        col = np.zeros((N, nv, 3))
        for p, o_ in self.off.items():
            n_ = nh if p == "head" else 4 if p == "bib" else nc
            c_ = sh if p in ("torso", "uaL", "uaR") else pants if p in ("thL", "thR") else np.ones((N, 3)) * .9 if p == "bib" else skin
            col[:, o_:o_ + n_] = c_[:, None]
        ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT"); ca.data.foreach_set("color", np.concatenate([col.reshape(-1, 3), np.ones((N * nv, 1))], 1).ravel())
        self.me = me; self.o = link(bpy.data.objects.new(name, me)); self.V = np.zeros((N, nv, 3)); DYN.append(self.update); self.update(0.0)
        # 動かない人（立っているだけ、遠くの人は応援の上下 5 cm も見えない）は毎コマ作り直さない：
        # 形が変わらなければ Blender はシーンを GPU に送り直さないので速い（絵は同じ）
        if not self.sp.any() and (lod or not ((self.mode == 1) | (self.mode == 3)).any()):
            DYN.remove(self.update)

    def _seg(self, part, A, B, r0, r1, Rt, xs=1.0):
        d = B - A; L = np.linalg.norm(d, axis=1)[:, None]; d = d / np.maximum(L, 1e-6)
        X = Rt - d * (Rt * d).sum(1)[:, None]; X /= np.maximum(np.linalg.norm(X, axis=1)[:, None], 1e-6); Pp = np.cross(d, X)
        cv = self.cv; tx, ty, tz, cap = cv[:, 0][None, :, None], cv[:, 1][None, :, None], cv[:, 2][None, :, None], cv[:, 3][None, :, None]
        r = (r0 + (r1 - r0) * tz) * self.s[:, None, None]
        o = self.off[part]
        self.V[:, o:o + len(cv)] = A[:, None] + d[:, None] * (L[:, None] * tz + r * cap * .75) + r * (tx * xs * X[:, None] + ty * Pp[:, None])
        return d, X, Pp

    def update(self, t):
        N = self.N; s = self.s[:, None]
        dist, frac = self._dist(t)
        run = (self.mode == 0) | (self.mode == 3); amp = np.where(run, frac * np.clip(self.sp / 3.6, .45, 1.0), 0.0)
        F = np.stack([-np.sin(self.h), np.cos(self.h), np.zeros(N)], 1); Rt = np.stack([np.cos(self.h), np.sin(self.h), np.zeros(N)], 1); Z = np.array([0, 0, 1.0])[None]
        pos = np.concatenate([self.P0, np.zeros((N, 1))], 1) + F * dist[:, None]
        ph = self.ph + 2 * math.pi * dist / self.SL
        legs = []
        for sx, p in ((-1, ph), (1, ph + math.pi)):
            a = .1 * amp + .62 * amp * np.sin(p); b = .1 + 1.25 * amp * np.maximum(0, np.cos(p))
            legs.append((sx, a, b, L_TH * np.cos(a) + L_SH * np.cos(a - b)))
        cheer = (self.mode == 1) | ((self.mode == 3) & (t >= self.t3)); wv = np.sin(t * self.wf + self.ph)
        hz = (np.maximum(legs[0][3], legs[1][3]) + .07 + .03 * amp * np.abs(np.sin(ph)) + np.where(cheer, .05 * np.abs(wv), 0))[:, None] * s
        hipc = pos + Z * hz; lean = (.14 * amp)[:, None]
        up = F * np.sin(lean) + Z * np.cos(lean); shc = hipc + up * L_TO * s
        if self.lod:
            self._seg("torso", pos + Z * .25 * s, shc, .2, .17, Rt, 1.15)
        else:
            self._seg("torso", hipc, shc, .15, .17, Rt, 1.3)
        o = self.off["head"]; hc = shc + up * .25 * s; self.V[:, o:o + len(self.hv)] = hc[:, None] + self.hv[None] * (.125 * s)[:, None]
        if self.lod:
            self.me.vertices.foreach_set("co", self.V.reshape(-1).astype(np.float32)); self.me.update(); return
        if self.bib:
            o = self.off["bib"]; c = hipc + up * .3 * s + F * .185 * s * np.cos(lean)
            for k, (u, w) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
                self.V[:, o + k] = c + Rt * (u * .1 * s) + up * (w * .075 * s)
        for (sx, a, b, _), th, sh in zip(legs, ("thL", "thR"), ("shL", "shR")):
            a = a[:, None]; b = b[:, None]; hp = hipc + Rt * (sx * .085 * s)
            kn = hp + (F * np.sin(a) - Z * np.cos(a)) * L_TH * s; ft = kn + (F * np.sin(a - b) - Z * np.cos(a - b)) * L_SH * s
            self._seg(th, hp, kn, .085, .07, Rt); self._seg(sh, kn, ft, .065, .05, Rt)
        for sx, p, ua, fa, k in ((-1, ph + math.pi, "uaL", "faL", 0), (1, ph, "uaR", "faR", 1)):
            c = (.75 * amp * np.sin(p))[:, None]; e = c + (.25 + 1.2 * np.clip(amp * 2, 0, 1))[:, None]
            d1 = F * np.sin(c) - Z * np.cos(c) + Rt * (sx * .12); d2 = F * np.sin(e) - Z * np.cos(e) - Rt * (sx * .1)
            w = (wv if k == 0 else np.sin(t * self.wf + self.ph + 1.3))[:, None]; upk = (cheer & ~(self.one & (k == 1)))[:, None]
            c1 = Rt * (sx * (.5 + .25 * w)) + F * .12 + Z * .85; c2 = Rt * (sx * (.15 + .45 * w)) + F * .08 + Z * .95
            d1 = np.where(upk, c1, d1); d2 = np.where(upk, c2, d2)
            d1 /= np.linalg.norm(d1, axis=1)[:, None]; d2 /= np.linalg.norm(d2, axis=1)[:, None]
            sp_ = shc + Rt * (sx * .2 * s) - up * .04 * s; el = sp_ + d1 * L_UA * s; hd = el + d2 * L_FA * s
            self._seg(ua, sp_, el, .058, .05, Rt * 1.0 + F * .01); self._seg(fa, el, hd, .048, .042, Rt * 1.0 + F * .01)
        self.me.vertices.foreach_set("co", self.V.reshape(-1).astype(np.float32)); self.me.update()

    def _dist(self, t):
        if self.free:                      # 最初から走っている
            return self.sp * t, np.ones(self.N)
        tau = t - self.delay; T = self.T
        return self.sp * np.where(tau < 0, 0, np.where(tau < T, tau * tau / (2 * T), tau - T / 2)), np.clip(tau / T, 0, 1)

    def pos(self, t):
        dist, _ = self._dist(t)
        return self.P0 + np.stack([-np.sin(self.h), np.cos(self.h)], 1) * dist[:, None]


def split(name, P0, heading=0.0, speed=0.0, mode=0, lod=0, **kw):
    """動く人（走る・手を振る）と動かない人を別の物にする：動かない方は毎コマ作り直さず、GPU にも送り直さない（速い。絵は同じ）。
    返すのは動く方（全員が同じなら 1 つだけ）"""
    N = len(P0); sp = np.broadcast_to(np.asarray(speed, float), (N,)); md = np.broadcast_to(np.asarray(mode), (N,))
    mov = (sp > 0) | ((((md == 1) | (md == 3))) & (lod == 0))
    if mov.all() or not mov.any():
        return People(name, P0, heading, speed, mode, lod=lod, **kw)
    People(name + "_still", P0, heading, speed, mode, lod=lod, sub=~mov, **kw)
    return People(name, P0, heading, speed, mode, lod=lod, sub=mov, **kw)


def grid(n, x0, x1, y0, y1, seed=1, jitter=.35, avoid=None):
    """道の上に n 人をばらつかせて並べる（x0〜x1、y0〜y1）。avoid：(x, y, r) の円の中には置かない"""
    rnd = np.random.default_rng(seed); area = (x1 - x0) * (y1 - y0); d = math.sqrt(area / max(1, n)); out = []
    ny = max(1, int(round((y1 - y0) / d))); nx = max(1, int(math.ceil(n / ny)))
    for j in range(ny):
        for i in range(nx):
            x = x0 + (i + .5 + rnd.uniform(-jitter, jitter)) * (x1 - x0) / nx; y = y0 + (j + .5 + rnd.uniform(-jitter, jitter)) * (y1 - y0) / ny
            if avoid and any((x - ax) ** 2 + (y - ay) ** 2 < r * r for ax, ay, r in avoid):
                continue
            out.append((x, y))
    if len(out) > n:                    # 余りは全体から均等に間引く（前の列だけが欠けないように）
        out = [out[i] for i in sorted(rnd.choice(len(out), n, replace=False))]
    return np.array(out)
