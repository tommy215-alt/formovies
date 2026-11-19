"""pilot_063「あなたの一生を、24時間にしたら？」の 3D（Blender Cycles）。新ドパ設計 v2（061 型）。
ショット＝セリフの行（s00〜s10）。暗い展示室の金の 24 時間時計（壁）→ 床の大きな時計盤に、睡眠・仕事・テレビ・食事・通勤の扇が積み上がる
→ 夜の家 → 食卓 → カレンダー → 砂時計 → 最後は 1 分 50 秒ぶんの細い金の扇と、冒頭の時計。
人は顔のない陶器の人形（CHARACTER_GUIDE の方針）。動き・カメラの着地は表拍（lbeat の整数）。閃光なし。
blender -b -P blender/scene63.py -- [s00 s01 …] [--samples N]     試し描き：AT="1.5,3" PCT=40 で work/test/ に"""
import sys, os, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib63 import *  # noqa: F401,F403

O = K.args()
NAMES = [l["scene"] for l in PLAN["lines"]]
TL = json.load(open(os.path.join(HERE, "..", "work", "timeline.json"), encoding="utf-8")); CUE = TL["cues"]
sc = setup(samples=O["samples"] if "--samples" in sys.argv else 48)
KEY = area_light("key", (-4, -6, 8), (0, 0, 1), 5, 1500); RIM = area_light("rim", (5, 4, 6), (0, 0, 1.5), 4, 700, (1, .8, .6))
cam = K.Cam(); ANIM = [cam.o]; S = {}; CUR = ["s00"]
for _l in (KEY, RIM):
    _l.visible_camera = False; _l.visible_glossy = False   # 照明の板が床に写り込まないように


def lbeat(name, k):
    c = CUE[name]; return (round(c / BP) + k) * BP - c


def look(P, A, lens=40, fstop=2.8, roll=0.0):
    P, A = Vector(P), Vector(A); cam.look(P, A, lens, roll); cam_dof(cam, (P - A).length, fstop)


def vlerp(a, b, u):
    return [lerp(x, y, u) for x, y in zip(a, b)]


def eio(u):
    u = clamp(u); return 16 * u ** 5 if u < .5 else 1 - (-2 * u + 2) ** 5 / 2


def snap(keys, t, mv=.42, kick=.09):
    if t <= keys[0][0]:
        return keys[0][1], keys[0][2], keys[0][3], 0.0
    for n, ((t0, p0, a0, l0), (t1, p1, a1, l1)) in enumerate(zip(keys, keys[1:])):
        if t <= t1:
            d = min(mv, (t1 - t0) * .8); ts = t1 - d; p0d = vlerp(p0, a0, .07)
            if t < ts:
                return vlerp(p0, a0, .07 * ease((t - t0) / max(1e-3, ts - t0))), a0, l0, 0.0
            u = eio((t - ts) / d); sg = 1 if n % 2 else -1
            return vlerp(p0d, p1, u), vlerp(a0, a1, u), lerp(l0, l1, u), sg * kick * math.sin(math.pi * u)
    t1, p1, a1, l1 = keys[-1]; h = clamp((t - t1) / 3.0)
    return vlerp(p1, a1, .05 * ease(h)), a1, l1, 0.0


def go(name, keys, t, fstop=3.0, mv=.42, kick=.09):
    ks = [(0 if i == 0 else lbeat(name, k), p, a, l) for i, (k, p, a, l) in enumerate(keys)]
    P, A, L, r = snap(ks, t, mv, kick); look(P, A, L, fstop, r)


def drop(o, base, t, t0, h=2.0, dur=.3, rz=None):
    """拍の頭 t0 に着地する（落ち始めは t0 − dur）"""
    t0 -= dur; u = (t - t0) / dur
    if u < 0:
        o.location = (base[0], base[1], -50); return
    z = base[2] + h * (1 - u * u) if u < 1 else base[2] + .05 * h * math.exp(-9 * (t - t0 - dur)) * abs(math.sin(16 * (t - t0 - dur)))
    o.location = (base[0], base[1], z)
    if rz is not None:
        o.rotation_euler = (o.rotation_euler[0], o.rotation_euler[1], rz)


def rise(o, base, t, t0, dur=.35, depth=None):
    """床の下からせり上がる（拍の頭 t0 に着く）。depth：最初に沈んでいる深さ"""
    d = depth if depth is not None else o.get("h", 3.0)
    u = clamp((t - (t0 - dur)) / dur); o.location = (base[0], base[1], base[2] - d * (1 - eio(u)))


# ---------------------------------------------------------------- 質感・部品
def ceramic():
    return plain("ceramic", (.86, .84, .8), .35, coat=.5)


def goldfig():
    return gold_mat("goldfig", .16)


def fig(name, loc, s=.6, m=None, rz=0.0):
    f = figure(name, loc, s, m); f.rotation_euler = (0, 0, rz); f["z0"] = loc[2]; ANIM.append(f); return f


def lamp(name, loc, energy, col, r=.4):
    d = bpy.data.lights.new(name, "POINT"); d.energy = energy; d.color = col; d.shadow_soft_size = r
    o = bpy.data.objects.new(name, d); o.location = loc; return link(o)


def spot(name, loc, at, energy, col=(1, .95, .85), size=.4, blend=.3, ang=.5):
    d = bpy.data.lights.new(name, "SPOT"); d.energy = energy; d.color = col; d.shadow_soft_size = size; d.spot_blend = blend; d.spot_size = ang
    o = bpy.data.objects.new(name, d); o.location = loc; o.rotation_mode = "QUATERNION"; o.rotation_quaternion = (Vector(at) - Vector(loc)).to_track_quat("-Z", "Y"); return link(o)


def lights(key, rim, hdri="studio_small_08_2k.hdr", strength=.8, rot=0.0, bg=0):
    w = world(hdri, strength, rot, bg)
    if bg:
        for lk in list(w.node_tree.links):
            if lk.to_node.bl_idname == "ShaderNodeMixShader" and lk.to_socket == lk.to_node.inputs[0]:
                w.node_tree.links.remove(lk)
    KEY.data.energy, KEY.data.color = key; RIM.data.energy, RIM.data.color = rim


def glow_mat(name, col, k):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = k
    return m


def stage(kind):
    """舞台：arena（暗い展示室）・room（夜の食卓の部屋）・night（夜の住宅街の家の前）"""
    clear_scene(); ANIM[:] = [cam.o]
    if kind == "arena":
        plane("floor", 80, 80, (0, 0, 0), plain("blackfloor", (.025, .024, .027), .22, coat=.8))
        plane("backw", 80, 20, (0, 9, 10), pbr_mat("bw", "brushed_concrete", 1 / 3.0, (.16, .15, .15), 1.0, box_proj=True), rot=(math.pi / 2, 0, 0)); lights((900, (1, .92, .8)), (600, (1, .8, .6)), "studio_small_08_2k.hdr", .35)
    elif kind == "room":
        plane("floor", 40, 40, (0, 0, 0), pbr_mat("court", "wood_floor", 1 / 1.6, (1, .9, .78), 1.0, box_proj=True))
        wl = plain("wall", (.55, .48, .4), .8)
        plane("backw", 40, 10, (0, 3.2, 5), wl, rot=(math.pi / 2, 0, 0)); plane("sidew", 40, 10, (-3.6, 0, 5), wl, rot=(math.pi / 2, 0, math.pi / 2))
        lights((500, (1, .85, .65)), (300, (1, .8, .6)), "brown_photostudio_02_2k.hdr", .25)
    elif kind == "night":
        plane("floor", 300, 300, (0, 0, 0), pbr_mat("grs", "grass_ground", 1 / 2.5, (.55, .65, .5), 1.0, box_proj=True))
        plane("path", 1.2, 8, (0, -3.0, .004), pbr_mat("pv", "brushed_concrete", 1 / 1.5, (.6, .58, .55), 1.0, box_proj=True))
        lights((250, (.7, .78, 1)), (500, (1, .8, .55)), "modern_evening_street_2k.hdr", .5, 0.0, 1)


def pillar(name, loc, h, w=.7, m=None, label=None, lab_size=.42):
    """金の柱（床から h の高さ）。label は柱の上の正面に立つ金の数字"""
    root = empty(name, loc); m = m or gold_mat("goldpil", .14)
    parent(box(name + "_b", (w, w, h), (0, 0, h / 2), m, bevel=.03), root)
    if label:
        parent(text_obj(name + "_t", label, (0, -w / 2 - .02, h + lab_size * .75), lab_size, gold_mat("goldtext", .2), extrude=.04), root)
    root["h"] = h + (lab_size * 1.4 if label else 0) + .2; ANIM.append(root); return root


def stumps(name, loc):
    """クリケットの柱（ウィケット）：3 本の柱と、上の 2 本の横木（ベイル）"""
    wd = plain("stumpwood", (.86, .78, .6), .45, coat=.3); root = empty(name, loc); bails = []
    for x in (-.11, 0, .11):
        parent(cyl(name + "_s%g" % x, .022, .72, (x, 0, .36), wd, 24), root)
    for i, x in enumerate((-.055, .055)):
        b = cyl(name + "_bail%d" % i, .012, .11, (loc[0] + x, loc[1], loc[2] + .735), wd, 12); b.rotation_euler = (0, math.pi / 2, 0); b["base"] = (loc[0] + x, loc[1], loc[2] + .735); bails.append(b); ANIM.append(b)
    return root, bails


def bails_fly(bails, t, t0, dirs=((-1.2, -1.6), (1.0, -1.9))):
    for b, (vx, vy) in zip(bails, dirs):
        x, y, z = b["base"]
        if t < t0:
            b.location = (x, y, z); b.rotation_euler = (0, math.pi / 2, 0); continue
        v = t - t0; zz = z + 2.6 * v - 4.9 * v * v
        if zz < .012:
            v2 = (2.6 + math.sqrt(2.6 ** 2 + 4 * 4.9 * (z - .012))) / 9.8; v = v2; zz = .012
        b.location = (x + vx * .5 * v, y + vy * .5 * v, zz); b.rotation_euler = (7 * v * (1 if vx > 0 else -1), math.pi / 2 + 5 * v, 0)


def bat(name, s=1.0):
    wd = plain("batwood", (.88, .78, .55), .45, coat=.3); grip = plain("grip", (.08, .08, .1), .7); root = empty(name)
    parent(box(name + "_blade", (.11 * s, .04 * s, .55 * s), (0, 0, -.42 * s), wd, bevel=.012), root)
    parent(cyl(name + "_h", .018 * s, .3 * s, (0, 0, -.02 * s), grip, 16), root); return root


def batter(name, loc, s=1.0, facing=0.0):
    """打者：人形＋バット（手元を軸に回る）"""
    f = fig(name, loc, s, rz=facing); b = bat(name + "_bat", s); b.location = (loc[0] + .25 * s, loc[1] - .05 * s, loc[2] + .62 * s); b.rotation_euler = (0, -.5, 0); ANIM.append(b)
    return f, b


def ball(name, r=.05, col=(.55, .05, .04)):
    o = sphere(name, r, (0, 0, -50), plain("cball_%g" % col[0], col, .35, coat=.6), 32); ANIM.append(o); return o


def path_bowl(t, t0, t1, a, bounce, b):
    """t0 に a を出て、bounce で弾み、t1 に b へ（2 区間の放物線）"""
    tm = t0 + (t1 - t0) * .62
    if t < tm:
        u = clamp((t - t0) / (tm - t0)); p = vlerp(a, bounce, u); p[2] += 4 * .25 * u * (1 - u) - 0; return p
    u = clamp((t - tm) / (t1 - tm)); p = vlerp(bounce, b, u); p[2] += 4 * .18 * u * (1 - u); return p


def photo_frame(name, key, loc, rz=-.3, w=1.4):
    p = os.path.join(HERE, "..", "assets", "photo", key + ".jpg"); im = bpy.data.images.load(p, check_existing=True); h = w * im.size[1] / im.size[0]
    root = empty(name, loc); root.rotation_euler = (math.radians(-10), 0, rz)
    parent(box(name + "_f", (w + .18, .06, h + .18), (0, 0, h / 2 + .09), plain("frame", (.12, .08, .05), .5, coat=.4), bevel=.02), root)
    parent(box(name + "_m", (w + .08, .062, h + .08), (0, -.002, h / 2 + .09), plain("mat", (.93, .9, .84), .7), bevel=0), root)
    parent(plane(name + "_p", w, h, (0, -.035, h / 2 + .09), image_mat("ph_" + key, p, .5), rot=(math.pi / 2, 0, 0)), root)
    ANIM.append(root); return root



def torus(name, R, r, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=64, minor_segments=12, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o


def reflector(name, loc, at, size, energy):
    """カメラの後ろの大きな光の板：カメラには写らず、金の面にだけ映り込む（暗く沈まないように）"""
    o = area_light(name, loc, at, size, energy, (1, .95, .88)); o.visible_camera = False; o.visible_diffuse = False; return o


def label(name, txt, loc, size=.15, rot=(math.pi / 2, 0, 0)):
    return text_obj(name, txt, loc, size, gold_mat("goldtext", .2), rot=rot, extrude=.012, font="BIZUDPGothic-Bold.ttf")


ICO = [(0, a, b) for a in (-1, 1) for b in (-1.618, 1.618)] + [(a, b, 0) for a in (-1, 1) for b in (-1.618, 1.618)] + [(b, 0, a) for a in (-1, 1) for b in (-1.618, 1.618)]


def soccer_ball(name, r=.2):
    from mathutils import Vector
    root = empty(name); parent(sphere(name + "_w", r, (0, 0, 0), plain("sbw", (.93, .93, .9), .4, coat=.3), 64), root); bk = plain("sbk", (.03, .03, .035), .4, coat=.3)
    for i, v in enumerate(ICO):
        d = Vector(v).normalized(); o = cyl(name + "_p%d" % i, r * .36, r * .06, tuple(d * r * .985), bk, 5); o.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); parent(o, root)
    return root


def baseball(name, r=.12):
    root = empty(name); parent(sphere(name + "_w", r, (0, 0, 0), plain("bbw", (.94, .92, .86), .5, coat=.2), 48), root); rd = plain("bbred", (.75, .06, .05), .5)
    a, b = .72, .28
    for i in range(72):
        t = i / 72 * 2 * math.pi; x, y, z = a * math.cos(t) + b * math.cos(3 * t), a * math.sin(t) - b * math.sin(3 * t), 2 * math.sqrt(a * b) * math.sin(2 * t)
        parent(sphere(name + "_s%d" % i, r * .07, (x * r * 1.0, y * r * 1.0, z * r * 1.0), rd, 8), root)
    return root


def basketball(name, r=.2):
    root = empty(name); parent(sphere(name + "_o", r, (0, 0, 0), plain("bkor", (.8, .3, .07), .65, coat=.1), 64), root); bk = plain("bkln", (.04, .03, .03), .6)
    for i, rot in enumerate(((0, 0, 0), (math.pi / 2, 0, 0), (0, math.pi / 2, 0))):
        parent(torus(name + "_r%d" % i, r * 1.002, r * .025, (0, 0, 0), bk, rot), root)
    return root


def stopwatch(name, s=1.0):
    root = empty(name); sil = plain("silver", (.8, .8, .82), .2, metal=1.0); wh = plain("swface", (.95, .94, .9), .4, coat=.3); bk = plain("swhand", (.05, .05, .05), .4)
    o = cyl(name + "_c", .17 * s, .06 * s, (0, 0, 0), sil, 64, bevel=.008); o.rotation_euler = (math.pi / 2, 0, 0); parent(o, root)
    o = cyl(name + "_f", .145 * s, .062 * s, (0, -.002, 0), wh, 64); o.rotation_euler = (math.pi / 2, 0, 0); parent(o, root)
    for k in range(12):
        a = k / 12 * 2 * math.pi; o = box(name + "_tk%d" % k, (.006 * s, .004, .025 * s), (math.sin(a) * .12 * s, -.034 * s, math.cos(a) * .12 * s), bk, bevel=0); o.rotation_euler = (0, a, 0); parent(o, root)
    o = box(name + "_h", (.008 * s, .004, .11 * s), (.03 * s, -.036 * s, .045 * s), plain("swred", (.8, .08, .06), .4), bevel=0); o.rotation_euler = (0, .55, 0); parent(o, root)
    parent(cyl(name + "_k", .025 * s, .05 * s, (0, 0, .2 * s), sil, 24), root); parent(torus(name + "_ring", .035 * s, .008 * s, (0, 0, .255 * s), sil, (math.pi / 2, 0, 0)), root)
    return root


def golf_set(name):
    root = empty(name); wh = plain("gbw", (.95, .95, .93), .35, coat=.3)
    parent(cyl(name + "_tee", .008, .05, (0, 0, .025), plain("tee", (.85, .7, .4), .5), 16), root); parent(sphere(name + "_b", .045, (0, 0, .095), wh, 32), root)
    sh = cyl(name + "_sh", .007, .8, (.18, .05, .39), plain("shaft", (.75, .75, .78), .2, metal=1.0), 16); sh.rotation_euler = (0, -.22, 0); parent(sh, root)
    parent(box(name + "_hd", (.12, .05, .035), (.12, .05, .02), plain("ironh", (.7, .7, .72), .25, metal=1.0), bevel=.008), root)
    parent(cyl(name + "_gr", .011, .2, (.26, .05, .74), plain("grip", (.08, .08, .1), .7), 16), root)
    return root


def cricket_props(name):
    root = empty(name); b = bat(name + "_bat", 1.0); b.location = (-.05, 0, .03); b.rotation_euler = (0, math.pi / 2, .3); parent(b, root)
    parent(sphere(name + "_rb", .1, (.32, -.1, .1), plain("cball_.55", (.55, .05, .04), .35, coat=.6), 32), root); return root


def hop(t, t0, h=.2, dur=.4):
    """t0 で頂点（拍の頭に一番高い）"""
    u = (t - (t0 - dur / 2)) / dur; return h * math.sin(math.pi * u) if 0 < u < 1 else 0.0




def glass_mat():
    m = bpy.data.materials.get("glass63")
    if m is None:
        m = plain("glass63", (.95, .97, 1.0), .03); b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["IOR"].default_value = 1.45
    return m


def cone(name, r1, r2, h, loc, m, seg=64):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=h)
    o = bpy.data.objects.new(name, mesh_from_bm(name, bm, [m])); o.location = loc; return link(o)


# ---------------------------------------------------------------- 24 時間の時計
LIFE = PLAN["life"]
ANG = lambda hr: hr / 24 * 2 * math.pi                       # 0 時が上（床では奥 +y）、時計回り
HM = lambda h, m: h + m / 60
COL = {"sleep": (.10, .16, .42), "work": (.55, .17, .10), "tv": (.08, .38, .40), "meal": (.72, .46, .10), "commute": (.42, .42, .46)}
SEG = []                                                      # (名前, 始まりの時, 終わりの時)：0 時から順に積む（社会生活基本調査の分）
_h = 0.0
for k in ("sleep", "work", "tv", "meal", "commute"):
    SEG.append((k, _h, _h + PLAN["min"][k] / 60)); _h += PLAN["min"][k] / 60


def wall_clock(name, loc=(0, 0, 2.3), R=1.8):
    """壁の 24 時間時計（正面は −y）。針は root["hand"]（y 軸まわりに回す）"""
    root = empty(name, loc); face = plain("clockface", (.03, .03, .035), .35, coat=.6); g = gold_mat("gold", .13)
    o = cyl(name + "_f", R, .1, (0, 0, 0), face, 128); o.rotation_euler = (math.pi / 2, 0, 0); parent(o, root)
    parent(torus(name + "_rim", R + .04, .06, (0, -.04, 0), g, (math.pi / 2, 0, 0)), root)
    for i in range(24):
        a = ANG(i); big = i % 6 == 0; L = .26 if big else .12
        o = box(name + "_t%d" % i, (.05 if big else .03, .02, L), (math.sin(a) * (R - .15 - L / 2), -.06, math.cos(a) * (R - .15 - L / 2)), g, bevel=0); o.rotation_euler = (0, a, 0); parent(o, root)
    for hr in (0, 6, 12, 18):
        a = ANG(hr); parent(text_obj(name + "_n%d" % hr, str(hr), (math.sin(a) * (R - .62), -.07, math.cos(a) * (R - .62)), .32, gold_mat("goldtext", .2), extrude=.03), root)
    hd = empty(name + "_hand", (0, -.1, 0)); parent(hd, root)
    parent(box(name + "_hb", (.08, .03, R - .3), (0, 0, (R - .3) / 2 - .1), gold_mat("goldhand", .1), bevel=.01), hd)
    parent(cyl(name + "_cap", .12, .06, (0, -.03, 0), g, 48), hd).rotation_euler = (math.pi / 2, 0, 0)
    root["hand"] = hd.name; ANIM.append(hd); return root, hd


def wedge(name, h0, h1, r, th, m, r0=0.0, z=0.0):
    """床の時計盤の扇（h0 時〜h1 時、半径 r、厚さ th）"""
    bm = bmesh.new(); n = max(2, int((h1 - h0) / 24 * 160)); pts = []
    for i in range(n + 1):
        a = ANG(h0 + (h1 - h0) * i / n); pts.append((r * math.sin(a), r * math.cos(a)))
    inner = [(0, 0)] if r0 == 0 else [(r0 * math.sin(ANG(h1 - (h1 - h0) * i / n)), r0 * math.cos(ANG(h1 - (h1 - h0) * i / n))) for i in range(n + 1)]
    vs = [bm.verts.new((x, y, 0)) for x, y in pts + inner]; f = bm.faces.new(vs)
    ex = bmesh.ops.extrude_face_region(bm, geom=[f]); bmesh.ops.translate(bm, vec=(0, 0, th), verts=[v for v in ex["geom"] if isinstance(v, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = bpy.data.objects.new(name, mesh_from_bm(name, bm, [m], smooth=False)); o.location = (0, 0, z); return link(o)


def floor_dial(name, R=3.0):
    """床の大きな 24 時間の時計盤（中心が原点）"""
    g = gold_mat("gold", .13); cyl(name + "_d", R, .05, (0, 0, .025), plain("dialm", (.035, .033, .04), .3, coat=.6), 160)
    torus(name + "_rim", R + .03, .05, (0, 0, .05), g)
    for i in range(24):
        a = ANG(i); big = i % 6 == 0; L = .3 if big else .14
        o = box(name + "_t%d" % i, (.05 if big else .03, L, .02), (math.sin(a) * (R + .25 + L / 2), math.cos(a) * (R + .25 + L / 2), .01), g, bevel=0); o.rotation_euler = (0, 0, -a)
    for hr in (0, 6, 12, 18):
        a = ANG(hr); text_obj(name + "_n%d" % hr, str(hr), (math.sin(a) * (R + .95), math.cos(a) * (R + .95), .01), .4, gold_mat("goldtext", .2), rot=(0, 0, 0), extrude=.02)


def seg_mid(k, r=1.9):
    _, h0, h1 = next(x for x in SEG if x[0] == k); a = ANG((h0 + h1) / 2); return (r * math.sin(a), r * math.cos(a)), a


def all_wedges(upto=None, th=.14):
    out = {}
    for k, h0, h1 in SEG:
        out[k] = wedge("w_" + k, h0, h1, 2.9, th, plain("wm_" + k, COL[k], .35, coat=.4), z=.05); ANIM.append(out[k])
        if k == upto:
            break
    return out


def bed(name):
    root = empty(name); wd = plain("bedwood", (.35, .24, .16), .5)
    parent(box(name + "_fr", (.9, 1.5, .18), (0, 0, .12), wd, bevel=.02), root)
    parent(box(name + "_mt", (.84, 1.44, .14), (0, 0, .27), plain("sheet", (.9, .9, .92), .7), bevel=.04), root)
    parent(box(name + "_bl", (.86, .9, .06), (0, -.24, .36), plain("blanket", (.2, .27, .55), .8), bevel=.03), root)
    parent(box(name + "_pl", (.5, .25, .1), (0, .52, .38), plain("pillow", (.95, .95, .95), .8), bevel=.04), root)
    parent(box(name + "_hb", (.9, .06, .5), (0, .75, .3), wd, bevel=.02), root); return root


def desk(name):
    root = empty(name); wd = plain("deskw", (.5, .36, .22), .45); bk = plain("mon", (.03, .03, .04), .3, coat=.5)
    parent(box(name + "_t", (1.0, .55, .04), (0, 0, .58), wd, bevel=.01), root)
    for x in (-.45, .45):
        for y in (-.22, .22):
            parent(box(name + "_l%g%g" % (x, y), (.04, .04, .58), (x, y, .29), wd, bevel=0), root)
    parent(box(name + "_m", (.55, .03, .34), (0, .12, .85), bk, bevel=.01), root)
    parent(box(name + "_sc", (.5, .005, .29), (0, .103, .86), glow_mat("scr", (.5, .7, 1.0), 1.5), bevel=0), root)
    parent(box(name + "_s", (.04, .04, .12), (0, .14, .64), bk, bevel=0), root); return root


def tv(name):
    root = empty(name); bk = plain("mon", (.03, .03, .04), .3, coat=.5)
    parent(box(name + "_st", (.8, .35, .35), (0, 0, .175), plain("tvst", (.3, .22, .15), .5), bevel=.01), root)
    parent(box(name + "_m", (.95, .04, .56), (0, .05, .66), bk, bevel=.01), root)
    parent(box(name + "_sc", (.88, .005, .5), (0, .028, .66), glow_mat("tvscr", (.6, .8, 1.0), 1.2), bevel=0), root); return root


def table(name, w=1.1, d=.7, h=.5):
    root = empty(name); wd = plain("tablew", (.55, .38, .22), .45); wh = plain("plate", (.95, .95, .93), .3, coat=.4)
    parent(box(name + "_t", (w, d, .04), (0, 0, h), wd, bevel=.01), root)
    for x in (-w / 2 + .05, w / 2 - .05):
        for y in (-d / 2 + .05, d / 2 - .05):
            parent(box(name + "_l%g%g" % (x, y), (.04, .04, h), (x, y, h / 2), wd, bevel=0), root)
    for x in (-w / 4, w / 4):
        parent(cyl(name + "_p%g" % x, .11, .015, (x, -d / 5, h + .028), wh, 32), root)
    parent(cyl(name + "_bowl", .14, .06, (0, d / 6, h + .05), plain("bowl", (.75, .3, .15), .35, coat=.4), 32), root); return root


def train(name):
    root = empty(name); body = plain("trainb", (.85, .86, .88), .3, metal=.3); ln = plain("trainl", (.1, .45, .25), .4); win = glow_mat("trwin", (1, .9, .7), 1.0)
    for i in range(3):
        x = i * .95
        parent(box(name + "_c%d" % i, (.9, .38, .4), (x, 0, .24), body, bevel=.04), root)
        parent(box(name + "_s%d" % i, (.9, .385, .05), (x, 0, .14), ln, bevel=0), root)
        for j in range(4):
            parent(box(name + "_w%d%d" % (i, j), (.14, .39, .1), (x - .3 + j * .2, 0, .32), win, bevel=0), root)
    return root


def house(name):
    """夜の家：明かりのついた窓と玄関の灯り"""
    root = empty(name); wl = plain("hwall", (.78, .74, .66), .8); rf = plain("hroof", (.15, .13, .13), .6); wn = glow_mat("hwin", (1, .78, .45), 3.0)
    parent(box(name + "_b", (2.4, 1.8, 1.5), (0, 0, .75), wl, bevel=.02), root)
    bm = bmesh.new(); v = [bm.verts.new(p) for p in ((-1.35, -1.05, 1.5), (1.35, -1.05, 1.5), (0, -1.05, 2.4), (-1.35, 1.05, 1.5), (1.35, 1.05, 1.5), (0, 1.05, 2.4))]
    for f in ((0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)):
        bm.faces.new([v[i] for i in f])
    o = bpy.data.objects.new(name + "_r", mesh_from_bm(name + "_r", bm, [rf], smooth=False)); link(o); parent(o, root)
    parent(box(name + "_door", (.45, .03, .85), (.55, -.91, .43), plain("door", (.3, .2, .12), .5), bevel=.01), root)
    for x in (-.6,):
        parent(box(name + "_w%g" % x, (.6, .03, .45), (x, -.91, .95), wn, bevel=0), root)
    parent(box(name + "_w2", (.5, .03, .3), (.0, -.91, 1.95), wn, bevel=0), root)
    lp = bpy.data.lights.new(name + "_pl", "POINT"); lp.energy = 60; lp.color = (1, .8, .5); lp.shadow_soft_size = .1
    lo = bpy.data.objects.new(name + "_pl", lp); lo.location = (.55, -1.1, 1.05); link(lo); parent(lo, root)
    lw = bpy.data.lights.new(name + "_in", "POINT"); lw.energy = 120; lw.color = (1, .78, .45); lw.shadow_soft_size = .4
    lo = bpy.data.objects.new(name + "_in", lw); lo.location = (-.6, -.6, .95); link(lo); parent(lo, root)
    return root


def hourglass(name, s=1.0):
    root = empty(name); g = gold_mat("gold", .13); gl = glass_mat(); sd = plain("sand", (.86, .7, .45), .8)
    for z in (0, 1.0):
        parent(cyl(name + "_p%g" % z, .36 * s, .06 * s, (0, 0, (z + .03) * s if z == 0 else (z + .03) * s), g, 64, bevel=.01), root)
    for a in range(3):
        aa = a / 3 * 2 * math.pi; parent(cyl(name + "_r%d" % a, .025 * s, 1.0 * s, (.3 * s * math.cos(aa), .3 * s * math.sin(aa), .53 * s), g, 16), root)
    parent(cone(name + "_g1", .24 * s, .03 * s, .44 * s, (0, 0, .29 * s), gl), root); parent(cone(name + "_g2", .03 * s, .24 * s, .44 * s, (0, 0, .77 * s), gl), root)
    parent(cone(name + "_s1", .21 * s, .03 * s, .14 * s, (0, 0, .14 * s), sd), root)                       # 下にたまった砂（ほとんど）
    parent(cone(name + "_s2", .045 * s, .01 * s, .04 * s, (0, 0, .57 * s), sd), root)                      # 上に残った砂（わずか）
    parent(cyl(name + "_st", .006 * s, .2 * s, (0, 0, .38 * s), sd, 8), root); return root


# ================================================================ ショット
def s_s00():                                   # 冒頭：暗い展示室の壁に、金の 24 時間時計。針が勢いよく回り出す
    stage("arena"); spot("sp", (0, -5, 7), (0, 0, 2.3), 3000, size=.8, ang=.9, blend=.5); reflector("rf", (0, -14, 3.5), (0, 0, 2.3), 8, 700)
    S["clk"], S["hd"] = wall_clock("clk")


def a_s00(u, t, f):
    t1 = lbeat("s00", 1); w = 2 * math.pi * 1.6                                     # 拍 1 から 1.6 回転/秒、拍 7 で 8 時 32 分（30 歳）に止まる
    t7 = lbeat("s00", 7); a7 = ANG(HM(8, 32)) + 2 * math.pi * 4
    if t < t1:
        a = 0.0
    elif t < t7:
        k = (t - t1) / (t7 - t1); a = a7 * (1 - (1 - k) ** 2)
    else:
        a = a7
    S["hd"].rotation_euler = (0, a, 0)
    go("s00", [(0, (0, -3.0, 2.3), (0, 0, 2.3), 34), (3, (2.4, -4.6, 1.4), (0, 0, 2.3), 30), (6, (-1.6, -5.4, 2.8), (0, 0, 2.2), 28), (8, (0, -6.6, 2.3), (0, 0, 2.3), 30)], t, 4.0)


def s_s01():                                   # 平均寿命 84 年：時計の上に「0歳」「84歳」の金の札。針が一周
    s_s00(); S["l0"] = label("lab0", "0歳", (0, 0, 0), .3); S["l84"] = label("lab84", "84歳", (0, 0, 0), .3); ANIM.extend([S["l0"], S["l84"]])


def a_s01(u, t, f):
    t1, t5 = lbeat("s01", 1), lbeat("s01", 5); k = eio(clamp((t - t1) / (t5 - t1))); S["hd"].rotation_euler = (0, 2 * math.pi * k, 0)
    drop(S["l0"], (-.55, -.1, 4.55), t, lbeat("s01", 1), h=1.5); drop(S["l84"], (.6, -.1, 4.55), t, lbeat("s01", 5), h=1.5)
    go("s01", [(0, (0, -7.2, 3.0), (0, 0, 3.0), 30), (3, (2.2, -5.4, 2.0), (0, 0, 2.8), 30), (5, (0, -5.0, 4.2), (0, 0, 4.0), 34), (7, (0, -7.6, 2.8), (0, 0, 2.9), 30)], t, 4.0)


AGES = [(20, HM(5, 41), 1), (30, HM(8, 32), 3), (40, HM(11, 23), 6)]


def s_s02():                                   # 20 歳 5:41・30 歳 8:32・40 歳 11:23：針が拍ごとに進み、年齢の札が落ちる
    s_s00()
    S["ages"] = []
    for i, (ag, hr, b) in enumerate(AGES):
        o = label("age%d" % ag, "%d歳" % ag, (0, 0, 0), .26); ANIM.append(o); S["ages"].append(o)


def a_s02(u, t, f):
    a = 0.0
    for ag, hr, b in AGES:
        tb = lbeat("s02", b); k = eio(clamp((t - (tb - .3)) / .3)); a = a + (ANG(hr) - a) * k if t >= tb - .3 else a
    S["hd"].rotation_euler = (0, a, 0)
    for i, (ag, hr, b) in enumerate(AGES):
        r = 2.35; aa = ANG(hr); drop(S["ages"][i], (math.sin(aa) * r, -.15, 2.3 + math.cos(aa) * r), t, lbeat("s02", b), h=1.2)
    go("s02", [(0, (-.8, -7.4, 2.2), (0, 0, 2.3), 28), (3, (1.6, -6.6, 3.0), (.9, 0, 2.6), 28), (6, (3.0, -6.4, 2.2), (1.4, 0, 2.4), 28), (8, (0, -9.0, 2.6), (.6, 0, 2.4), 28)], t, 4.0)


def base_dial(upto):
    """床の時計盤の舞台（s03〜s05 共通）：扇は upto まで、ベッド、机・テレビ・食卓"""
    stage("arena"); spot("sp", (0, -4, 9), (0, 0, 0), 4000, size=1.0, ang=1.0, blend=.5); reflector("rf", (0, -14, 5), (0, 0, 0), 10, 600)
    floor_dial("fd"); S["w"] = all_wedges(upto); (x, y), a = seg_mid("sleep", 1.7)
    S["bed"] = bed("bed"); S["bed"].rotation_euler = (0, 0, -a); S["bedp"] = (x, y, .19); ANIM.append(S["bed"])
    sl = fig("sleeper", (0, 0, 0), .5, goldfig()); parent(sl, S["bed"]); sl.location = (0, .05, .62); sl.rotation_euler = (-math.pi / 2, 0, 0)
    S["objs"] = []
    if upto != "sleep":
        for k, fn in (("work", desk), ("tv", tv), ("meal", table)):
            (x, y), a = seg_mid(k, 1.85); o = fn("o_" + k); o.rotation_euler = (0, 0, -a + math.pi); ANIM.append(o); S["objs"].append((k, o, (x, y, .19)))


def s_s03():                                   # 睡眠：床の大きな時計盤に、紺の扇（0 時〜7 時 54 分）が落ちて、ベッドと眠る人形
    base_dial("sleep")


def a_s03(u, t, f):
    drop(S["w"]["sleep"], (0, 0, .05), t, lbeat("s03", 1), h=2.0); drop(S["bed"], S["bedp"], t, lbeat("s03", 3), h=1.6)
    (x, y), _ = seg_mid("sleep", 1.7)
    go("s03", [(0, (-1.0, -7.4, 5.8), (0, 0, 0), 30), (1, (-.4, -5.6, 4.2), (0, .3, 0), 30), (3, (x - 1.4, y - 2.4, 1.6), (x, y, .4), 34), (6, (x + 1.8, y - 2.8, 1.2), (x, y, .5), 32),
               (8, (0, -7.6, 6.4), (0, 0, 0), 28)], t, 4.0)


def s_s04():                                   # 仕事・テレビ・食事：扇が拍ごとに積み上がり、机・テレビ・食卓がのる
    base_dial("meal")


W4 = {"work": 1, "tv": 3, "meal": 5}


def a_s04(u, t, f):
    S["bed"].location = S["bedp"]; S["w"]["sleep"].location = (0, 0, .05)
    for k, o, p in S["objs"]:
        drop(S["w"][k], (0, 0, .05), t, lbeat("s04", W4[k]), h=1.6); drop(o, p, t, lbeat("s04", W4[k]), h=2.0)
    P_ = {k: seg_mid(k, 1.85)[0] for k in W4}
    go("s04", [(0, (-2.0, -6.6, 4.6), (0, 0, 0), 30), (1, (P_["work"][0] - 2.2, P_["work"][1] - 1.2, 1.4), (P_["work"][0], P_["work"][1], .5), 32),
               (3, (P_["tv"][0] - 1.0, P_["tv"][1] - 2.4, 1.4), (P_["tv"][0], P_["tv"][1], .5), 32), (5, (P_["meal"][0] + 2.0, P_["meal"][1] - 1.6, 1.4), (P_["meal"][0], P_["meal"][1], .4), 32),
               (7, (0, -7.8, 6.6), (0, 0, 0), 28)], t, 4.0)


def s_s05():                                   # 通勤・通学：灰色の細い扇と、扇の上を走り抜ける小さな電車
    base_dial("commute"); S["tr"] = train("tr"); ANIM.append(S["tr"])


def a_s05(u, t, f):
    S["bed"].location = S["bedp"]
    for k, o, p in S["objs"]:
        o.location = p
    for k in ("sleep", "work", "tv", "meal"):
        S["w"][k].location = (0, 0, .05)
    drop(S["w"]["commute"], (0, 0, .05), t, lbeat("s05", 1), h=1.4)
    (x, y), a = seg_mid("commute", 3.6); d = (math.cos(a), -math.sin(a))          # 扇の外側を、円に沿う向きに走る
    v = (t - lbeat("s05", 0)) * 2.4 - 2.6; S["tr"].location = (x + d[0] * v, y + d[1] * v, .0); S["tr"].rotation_euler = (0, 0, -a)
    go("s05", [(0, (x - 2.6, y - 2.2, 1.0), (x, y, .3), 30), (2, (x - 1.0, y - 3.4, 2.4), (x * .7, y * .7, .2), 30)], t, 4.0)


def s_s06():                                   # じゃあ、親と過ごす時間は？：夜の家。窓と玄関に明かり
    stage("night"); S["h"] = house("home"); S["h"].location = (0, 1.0, 0)
    reflector("rf", (0, -14, 3), (0, 0, 1), 8, 300)


def a_s06(u, t, f):
    go("s06", [(0, (2.6, -7.5, 1.0), (0, 0, 1.2), 30), (2, (.9, -4.2, .9), (.5, .1, .9), 34)], t, 4.0, mv=.5)


def s_s07():                                   # 家を出るまでは、毎日のように一緒：明かりの下の食卓、大人 2 人と子ども（金）
    stage("room"); S["tb"] = table("tb", 1.2, .8, .5); S["tb"].location = (0, .8, 0)
    spot("lamp", (0, .8, 2.6), (0, .8, .5), 900, (1, .82, .55), size=.3, ang=1.0, blend=.6)
    cyl("lampshade", .25, .18, (0, .8, 1.7), plain("shade", (.9, .8, .6), .6), 48); cyl("lampcord", .006, 1.0, (0, .8, 2.3), plain("cord", (.05, .05, .05), .5), 8)
    fig("dad", (-.85, .8, 0), .62, ceramic(), rz=-math.pi / 2); fig("mom", (.85, .8, 0), .62, ceramic(), rz=math.pi / 2); S["kid"] = fig("kid", (0, .05, 0), .42, goldfig())


def a_s07(u, t, f):
    S["kid"].location = (0, .05, hop(t, lbeat("s07", 1), .08, .4))
    go("s07", [(0, (0, -2.6, 1.9), (0, .7, .6), 32), (2, (1.8, -1.4, 1.0), (0, .6, .6), 30)], t, 3.0)


MONTHS = [(i + 1, (i % 4 - 1.5) * .95, 2.6 - (i // 4) * .95) for i in range(12)]


def s_s08():                                   # 18 歳で家を出て、お盆と正月に 3 日ずつ：12 か月の札が並び、8 月と 1 月だけ金に
    stage("arena"); spot("sp", (0, -5, 6), (0, 0, 1.6), 3000, size=.8, ang=1.0, blend=.5); reflector("rf", (0, -14, 3), (0, 0, 1.6), 8, 500)
    S["tiles"] = []; c = ceramic(); g = gold_mat("gold", .13)
    for m, x, z in MONTHS:
        o = empty("mt%d" % m); parent(box("mtb%d" % m, (.8, .08, .8), (0, 0, 0), c, bevel=.03), o)
        parent(text_obj("mtt%d" % m, "%d月" % m, (0, -.05, 0), .22, plain("ink", (.12, .1, .1), .5), extrude=.01, font="BIZUDPGothic-Bold.ttf"), o); ANIM.append(o); S["tiles"].append((m, o, (x, 0, z)))
    S["gold"] = []
    for m in (1, 8):
        _, x, z = MONTHS[m - 1]; o = empty("gt%d" % m); parent(box("gtb%d" % m, (.84, .1, .84), (0, 0, 0), g, bevel=.03), o)
        parent(text_obj("gtt%d" % m, "%d月" % m, (0, -.06, .1), .22, plain("ink", (.12, .1, .1), .5), extrude=.01, font="BIZUDPGothic-Bold.ttf"), o)
        parent(text_obj("gtd%d" % m, "3日", (0, -.06, -.18), .16, plain("ink", (.12, .1, .1), .5), extrude=.01, font="BIZUDPGothic-Bold.ttf"), o); ANIM.append(o); S["gold"].append((o, (x, -.25, z)))


def a_s08(u, t, f):
    for i, (m, o, p) in enumerate(S["tiles"]):
        rise(o, p, t, lbeat("s08", -1), .35, depth=4.0)          # 場面の入りから並んでいる（暗いコマを出さない）
    for o, p in S["gold"]:
        k = eio(clamp((t - (lbeat("s08", 2) - .3)) / .3)); o.location = (p[0], lerp(.0, p[1], k) if k > 0 else 0.05, p[2] if k > 0 else -50)
    go("s08", [(0, (0, -6.4, 1.4), (0, 0, 1.2), 30), (2, (-1.2, -4.6, 2.2), (-.3, 0, 1.9), 32), (5, (1.6, -5.6, .9), (0, 0, 1.4), 30)], t, 3.0)


def s_s09():                                   # 親が 87 歳まで生きても、残りは約 940 時間：砂がほとんど落ちた砂時計
    stage("arena"); spot("sp", (1, -3, 5), (0, 0, .6), 2500, size=.5, ang=.8, blend=.5); reflector("rf", (0, -12, 2), (0, 0, .6), 6, 400)
    S["hg"] = hourglass("hg", 1.0); ANIM.append(S["hg"])


def a_s09(u, t, f):
    drop(S["hg"], (0, 0, 0), t, lbeat("s09", 1), h=2.0)
    go("s09", [(0, (0, -4.2, 1.6), (0, 0, .6), 34), (2, (1.4, -2.4, .8), (0, 0, .5), 36), (4, (-.6, -2.0, 1.2), (0, 0, .35), 42)], t, 4.0)


def s_s10():                                   # 1 分 50 秒：時計盤の上に細い金の線（親と過ごす時間）。引くと 24 時間、最後に壁の時計
    stage("arena"); spot("sp", (0, -1, 9), (0, 0, 0), 4000, size=1.0, ang=.8, blend=.5); reflector("rf", (0, -14, 5), (0, 0, 1), 10, 600)
    floor_dial("fd"); S["w"] = all_wedges(None)
    for k, o in S["w"].items():
        o.location = (0, 0, .05)
    for k, fn in (("work", desk), ("tv", tv), ("meal", table)):
        (x, y), a = seg_mid(k, 1.85); o = fn("o_" + k); o.rotation_euler = (0, 0, -a + math.pi); o.location = (x, y, .19)
    (x, y), a = seg_mid("sleep", 1.7); b = bed("bed"); b.rotation_euler = (0, 0, -a); b.location = (x, y, .19)
    h0 = 19.0; S["pa"] = HM(19, 0); hs = PLAN["parent_s"] / 3600                     # 空いている夜 7 時の場所に、1 分 50 秒ぶん
    S["sl"] = wedge("sliver", h0, h0 + hs, 2.9, .2, glow_mat("slm", (1, .75, .3), 5.0), z=.05)
    S["clk"], S["hd"] = wall_clock("clk", (0, 7.5, 3.6), 2.6)


def a_s10(u, t, f):
    S["hd"].rotation_euler = (0, ANG(HM(8, 32)) + .01 * math.sin(t * 6) * 0, 0)
    a = ANG(19.0); dx, dy = math.sin(a), math.cos(a)                    # 外側から中心に向かって見る：扇は細い光の線に見える
    go("s10", [(0, (4.2 * dx, 4.2 * dy, .5), (1.6 * dx, 1.6 * dy, .2), 40), (3, (7.0 * dx, 7.0 * dy, 3.4), (0, 0, 0), 30), (6, (0, -8.4, 7.0), (0, 1.0, 0), 28),
               (9, (0, -6.0, 3.0), (0, 7.5, 3.6), 30)], t, 4.0, mv=.5)


# ---------------------------------------------------------------- 書き出し
def _setup(k):
    def f():
        CUR[0] = k; S.clear(); globals()["s_" + k]()
    return f


SHOTS = {k: (_setup(k), (lambda a: (lambda u, t, f: a(u, t, f)))(globals()["a_" + k])) for k in NAMES}

if os.environ.get("AT"):
    ats = [float(x) for x in os.environ["AT"].split(",")]; out = os.path.join(HERE, "..", "work", "test"); os.makedirs(out, exist_ok=True)
    sc.render.resolution_percentage = int(os.environ.get("PCT", "40"))
    for name in O["shots"]:
        setup_fn, anim = SHOTS[name]; setup_fn()
        for at in ats:
            anim(0, at, int(at * K.FPS)); sc.render.filepath = os.path.join(out, f"{name}_{at:g}.png")
            t0 = time.time(); bpy.ops.render.render(write_still=True); print("TEST", name, at, round(time.time() - t0, 1), "s", flush=True)
else:
    K.render_shots(HERE, SHOTS, NAMES, O, ANIM)
