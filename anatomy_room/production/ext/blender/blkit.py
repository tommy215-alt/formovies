"""Blender で 3D の場面を描く土台（2026-11-02〜、ユーザーの承認：3D の場面は Blender、図・文字・字幕はブラウザ）。テンプレートの外の部品。

流れ：
  1. 各回の blender/scene.py が、この blkit で場面（空・地球・人・道具）を組み、ショットごとのカメラと動きを u（0〜1）の関数で書く。
  2. `blender -b -P pilot_NNN/blender/scene.py -- [ショット名 ...] [--still] [--samples N]` で、
     work/timeline.json の時刻からショットの長さを決め、work/blender/<ショット>/f_0001.png … を描く（30 fps）。
  3. `python ext/blender/bl_pack.py NNN` で PNG を JPEG の data URI の JS（f_0001.js）にする（file:// の画像は canvas を汚すため）。
  4. renderer.html では SHOTS の 3D のショットを `{ at: "l01", kind: "3d", draw: blShot("l01") }` にし、
     `<script src="../ext/blender/blframes.js">` を kit.js のあとに、`BL.install()` を kitStart のあとに書く。

速さ（RTX 3070、2026-11-02 の実測）：Cycles 32 サンプル＋OptiX のノイズ除去＋persistent data で 1 コマ約 3 秒（128 サンプルとの差 44.5 dB）。
素材：MakeHuman / MPFB の人体（CC0、pilot_021/assets/human）、地表と雲は手続き的（ノイズ）、空は Blender の多重散乱の空。顔は描かない（ヘルメットで覆うか後ろ姿）。
"""
import bpy, math, os, sys, json
from mathutils import Vector

FPS = 30
R = 6371000.0
HUMAN_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "pilot_021", "assets", "human")


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = {"shots": [x for x in a if not x.startswith("--") and not x[0].isdigit()], "still": "--still" in a, "samples": 32}
    if "--samples" in a:
        o["samples"] = int(a[a.index("--samples") + 1])
    return o


# ---------------------------------------------------------------- 描画の設定
def setup(samples=32, exposure=-3.2):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for t in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = t; prefs.get_devices(); break
        except Exception:
            pass
    for d in prefs.devices:
        d.use = d.type != "CPU"
    sc.cycles.device = "GPU"; sc.cycles.samples = samples; sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPTIX"
    except Exception:
        pass
    sc.cycles.adaptive_threshold = .03; sc.render.use_persistent_data = True
    sc.cycles.volume_step_rate = 4.0; sc.cycles.volume_max_steps = 256   # 薄い霧・雲は粗い刻みで十分（2026-11-02、1 コマ 6 秒 → 短縮）
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
    sc.render.fps = FPS
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = exposure
    sc.render.image_settings.file_format = "PNG"
    sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .5
    return sc


def mat(name, col, rough=.5, metal=0.):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    return m


# ---------------------------------------------------------------- 空と太陽
class Sky:
    def __init__(self):
        sc = bpy.context.scene
        w = bpy.data.worlds.new("sky"); sc.world = w; w.use_nodes = True; nt = w.node_tree
        self.node = nt.nodes.new("ShaderNodeTexSky"); self.node.sky_type = "MULTIPLE_SCATTERING"
        nt.links.new(self.node.outputs[0], nt.nodes["Background"].inputs[0])
        self.sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(self.sun)
        self.sun.data.angle = math.radians(.545)

    def set(self, altitude, sun_el=14, sun_rot=205, sun_energy=9.0):
        """altitude（m）：空の見え方（31 km で黒い空）。太陽の向きは空のテクスチャと同じ（+Y が北）"""
        n = self.node; n.altitude = altitude; n.sun_elevation = math.radians(sun_el); n.sun_rotation = math.radians(sun_rot); n.sun_size = math.radians(.545)
        az, el = math.radians(sun_rot), math.radians(sun_el)
        d = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
        self.sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler(); self.sun.data.energy = sun_energy


# ---------------------------------------------------------------- 地球（地表は手続き的：乾いた盆地・山並み・白い砂、斜めほど青くかすむ）と雲の層
def _sphere(name, r, seg=256):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=(0, 0, -R))
    o = bpy.context.object; o.name = name; bpy.ops.object.shade_smooth(); return o


class Earth:
    def __init__(self, cloud_alt=4000):
        self.earth = _sphere("earth", R)
        em = bpy.data.materials.new("earth"); em.use_nodes = True; n = em.node_tree.nodes; L = em.node_tree.links; b = n["Principled BSDF"]
        tc = n.new("ShaderNodeTexCoord")

        def noise(scale, detail=8, rough=.55):
            x = n.new("ShaderNodeTexNoise"); x.inputs["Scale"].default_value = scale; x.inputs["Detail"].default_value = detail
            x.inputs["Roughness"].default_value = rough; L.new(tc.outputs["Object"], x.inputs["Vector"]); return x
        big, mid, fine, close = noise(1 / 60000, 4), noise(1 / 6000, 10), noise(1 / 600, 6), noise(1 / 8, 6, .7)
        mx = n.new("ShaderNodeMath"); mx.operation = "MULTIPLY_ADD"; L.new(mid.outputs["Fac"], mx.inputs[0]); mx.inputs[1].default_value = .6; L.new(big.outputs["Fac"], mx.inputs[2])
        cr = n.new("ShaderNodeValToRGB"); L.new(mx.outputs[0], cr.inputs[0]); e = cr.color_ramp.elements
        e[0].position, e[0].color = .38, (.62, .52, .38, 1); e[1].position, e[1].color = .9, (.10, .09, .08, 1)
        for pos, col in [(.5, (.48, .38, .27, 1)), (.62, (.36, .30, .22, 1)), (.72, (.24, .22, .16, 1)), (.8, (.17, .17, .13, 1))]:
            el = e.new(pos); el.color = col
        wh = noise(1 / 25000, 3); wr = n.new("ShaderNodeMapRange"); wr.inputs[1].default_value = .66; wr.inputs[2].default_value = .7; L.new(wh.outputs["Fac"], wr.inputs[0])
        ws = n.new("ShaderNodeMix"); ws.data_type = "RGBA"; L.new(wr.outputs[0], ws.inputs[0]); L.new(cr.outputs[0], ws.inputs[6]); ws.inputs[7].default_value = (.85, .84, .8, 1)
        ov = n.new("ShaderNodeMix"); ov.data_type = "RGBA"; ov.blend_type = "OVERLAY"; ov.inputs[0].default_value = .3
        L.new(ws.outputs[2], ov.inputs[6]); L.new(fine.outputs["Color"], ov.inputs[7])
        ov2 = n.new("ShaderNodeMix"); ov2.data_type = "RGBA"; ov2.blend_type = "OVERLAY"; ov2.inputs[0].default_value = .35   # 近くで見たときの砂と草のむら
        L.new(ov.outputs[2], ov2.inputs[6]); L.new(close.outputs["Color"], ov2.inputs[7])
        bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = .4; bump.inputs["Distance"].default_value = 300
        L.new(mx.outputs[0], bump.inputs["Height"]); L.new(bump.outputs[0], b.inputs["Normal"])
        lw = n.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = .5
        self.haze_pow = n.new("ShaderNodeMath"); self.haze_pow.operation = "POWER"; self.haze_pow.inputs[1].default_value = 4; L.new(lw.outputs["Facing"], self.haze_pow.inputs[0])
        hz = n.new("ShaderNodeMix"); hz.data_type = "RGBA"; L.new(self.haze_pow.outputs[0], hz.inputs[0]); L.new(ov2.outputs[2], hz.inputs[6]); hz.inputs[7].default_value = (.5, .64, .88, 1)
        L.new(hz.outputs[2], b.inputs["Base Color"])
        self.haze_k = n.new("ShaderNodeMath"); self.haze_k.operation = "MULTIPLY"; self.haze_k.inputs[1].default_value = .35; L.new(self.haze_pow.outputs[0], self.haze_k.inputs[0])
        L.new(self.haze_k.outputs[0], b.inputs["Emission Strength"]); b.inputs["Emission Color"].default_value = (.4, .55, .9, 1)
        b.inputs["Roughness"].default_value = .95; self.earth.data.materials.append(em)
        self.clouds = _sphere("clouds", R + cloud_alt)
        cm = bpy.data.materials.new("clouds"); cm.use_nodes = True; n = cm.node_tree.nodes; L = cm.node_tree.links; b = n["Principled BSDF"]
        tc = n.new("ShaderNodeTexCoord")
        c1 = n.new("ShaderNodeTexNoise"); c1.inputs["Scale"].default_value = 1 / 9000; c1.inputs["Detail"].default_value = 12; c1.inputs["Roughness"].default_value = .62
        L.new(tc.outputs["Object"], c1.inputs["Vector"])
        rg = n.new("ShaderNodeMapRange"); rg.inputs[1].default_value = .54; rg.inputs[2].default_value = .66; L.new(c1.outputs["Fac"], rg.inputs[0])
        b.inputs["Base Color"].default_value = (1, 1, 1, 1); b.inputs["Roughness"].default_value = 1; L.new(rg.outputs[0], b.inputs["Alpha"])
        self.clouds.data.materials.append(cm); self.clouds.visible_shadow = False

    def altitude(self, h, haze=.35, haze_pow=4):
        """カメラの高さ（m）。場面の原点（ゴンドラの床など）が高度 h になるよう、地球を下げる"""
        for o in (self.earth, self.clouds):
            o.location = (0, 0, -(R + h))
        self.haze_k.inputs[1].default_value = haze; self.haze_pow.inputs[1].default_value = haze_pow   # 地上の場面は haze_pow を大きく（地平線のすぐ近くだけかすむ）


# ---------------------------------------------------------------- 形の部品
def box(name, s, loc, m, rot=(0, 0, 0), bevel=.012, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name; o.scale = s
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bv = o.modifiers.new("b", "BEVEL"); bv.width = bevel; bv.segments = 3
    o.data.materials.append(m); o.parent = parent; return o


def tube(a, b_, r, m, parent=None, verts=24):
    a, b_ = Vector(a), Vector(b_); v = b_ - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=v.length, location=(a + b_) / 2, vertices=verts)
    o = bpy.context.object; o.rotation_euler = v.to_track_quat("Z", "Y").to_euler(); o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = parent; return o


def lathe(name, prof, m, segs=96, loc=(0, 0, 0)):
    """prof：[(半径, 高さ), ...] を Z 軸まわりに回した面"""
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new(); rings = []
    for r, z in prof:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), z)) for i in range(segs)])
    for a, b_ in zip(rings, rings[1:]):
        for i in range(segs):
            bm.faces.new((a[i], a[(i + 1) % segs], b_[(i + 1) % segs], b_[i]))
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.location = loc
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(m); return o


def human(kind="man_stand", suit=(.82, .8, .74), helmet=True, pack=True):
    """MakeHuman / MPFB の人体（CC0）。顔はヘルメットで覆う（helmet=False のときは後ろ姿だけで使う）。戻り値は親の空のオブジェクト（足もとが原点、-Y が前）"""
    sc = bpy.context.scene
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(os.path.join(HUMAN_DIR, kind + ".glb")))
    objs = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new("man_" + kind, None); sc.collection.objects.link(root)
    sm = mat("suit_" + kind, suit, .75)
    for o in objs:
        if o.parent is None:
            o.parent = root
        if o.type == "MESH":
            o.data.materials.clear(); o.data.materials.append(sm)
    bpy.context.view_layer.update()
    top = max((o.matrix_world @ Vector(c)).z for o in objs if o.type == "MESH" for c in o.bound_box)
    if helmet:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=.2, location=(0, -.02, top - .12)); h = bpy.context.object
        h.data.materials.append(mat("helm", (.85, .85, .82), .3)); bpy.ops.object.shade_smooth(); h.parent = root
    if pack:
        box("pack", (.4, .2, .5), (0, .16, top - .55), mat("olive", (.3, .32, .2), .8), parent=root)
    root["top"] = top
    return root


# ---------------------------------------------------------------- カメラ・ショット
class Cam:
    def __init__(self):
        sc = bpy.context.scene
        self.o = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(self.o); sc.camera = self.o
        self.o.data.sensor_width = 36; self.o.data.clip_start = .05; self.o.data.clip_end = 1e8

    def look(self, pos, at, lens=35, roll=0.0):
        p, a = Vector(pos), Vector(at)
        q = (a - p).to_track_quat("-Z", "Y")
        if roll:
            from mathutils import Quaternion
            q = q @ Quaternion((0, 0, 1), roll)
        self.o.location = p; self.o.rotation_mode = "QUATERNION"; self.o.rotation_quaternion = q; self.o.data.lens = lens


def ease(u):
    return .5 - .5 * math.cos(math.pi * max(0., min(1., u)))


def shot_lengths(here):
    """work/timeline.json から、ショット（cue 名）ごとの [開始, 終了] 秒。終了は次の cue（SHOTS の順は scene.py が渡す）"""
    tl = json.load(open(os.path.join(here, "..", "work", "timeline.json"), encoding="utf-8"))
    return tl["cues"], tl["ending_start"]


def render_shots(here, shots, order, opts, objs_anim):
    """shots：{名前: (setup(), anim(u, t, f))}、order：SHOTS の at の並び（3D 以外も含む。ショットの終わりを決める）。
    objs_anim：動かすオブジェクト（毎コマ keyframe を打って動きのぶれを出す）"""
    sc = bpy.context.scene
    cues, end = shot_lengths(here)
    todo = opts["shots"] or list(shots)
    for name in todo:
        i = order.index(name); a = cues[name]; b = cues[order[i + 1]] if i + 1 < len(order) else end
        n = int(math.ceil((b - a) * FPS)) + 2                 # 切れ目の前後に 1 コマずつ余分に
        setup_fn, anim = shots[name]
        for o in objs_anim:
            o.animation_data_clear()
        setup_fn()
        frames = [n // 2] if opts["still"] else range(n)
        for f in range(n):
            u = f / max(1, n - 3); anim(u, f / FPS, f)
            for o in objs_anim:
                for path in ("location", "rotation_quaternion" if o.rotation_mode == "QUATERNION" else "rotation_euler"):
                    o.keyframe_insert(path, frame=f + 1)
                if o.type == "CAMERA":
                    o.data.keyframe_insert("lens", frame=f + 1)
        out = os.path.join(here, "..", "work", "blender", name)
        os.makedirs(out, exist_ok=True)
        for f in frames:
            sc.frame_set(f + 1)
            sc.render.filepath = os.path.join(out, "still.png" if opts["still"] else "f_%04d.png" % (f + 1))
            bpy.ops.render.render(write_still=True)
        json.dump({"start": a, "end": b, "frames": n, "fps": FPS}, open(os.path.join(out, "meta.json"), "w"))
        print(f"BLSHOT {name} {n} frames", flush=True)
