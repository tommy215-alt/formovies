"""Procedural 3DCG for every shot (Blender 4.0, EEVEE).

Usage:  xvfb-run -a blender -b --python scripts/blender_shots.py -- SHOT [--preview]
Builds the set for SHOT from scratch, animates camera / objects and renders
JPEG frames to assets/frames/shots/SHOT/.
"""
import bpy, json, math, os, random, sys
from mathutils import Vector, Euler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARDS = os.path.join(ROOT, "assets", "frames", "boards")
FPS = 30

# global timeline (seconds) — matched to assets/audio/timeline.json
SHOTS = {
    "A1": (0.0, 8.2), "B1": (8.2, 12.9), "B2": (12.9, 17.2), "B3": (17.2, 20.4),
    "C1": (20.4, 26.3), "C2": (26.3, 30.5), "C3": (30.5, 34.0), "C4": (34.0, 40.2),
    "D1": (40.2, 44.1), "D2": (44.1, 48.6), "D3": (48.6, 54.1), "D4": (54.1, 59.3),
    "D5a": (59.3, 65.9), "D5b": (65.9, 70.3), "E1": (70.3, 74.8), "E2": (74.8, 79.2),
    "E3": (79.2, 84.6), "F1": (84.6, 91.0), "F2": (91.0, 95.0),
}


def nframes(shot):
    a, b = SHOTS[shot]
    return int(round(b * FPS)) - int(round(a * FPS))


# ------------------------------------------------------------------ basics
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 720, 1280   # upscaled to 1080x1920 in compositing
    sc.render.fps = FPS
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 94
    ee = sc.eevee
    ee.taa_render_samples = 8
    ee.use_gtao = True; ee.gtao_distance = 0.6
    ee.use_bloom = True; ee.bloom_intensity = 0.03; ee.bloom_threshold = 1.2
    ee.use_soft_shadows = True
    ee.shadow_cube_size = "1024"; ee.shadow_cascade_size = "2048"
    ee.use_ssr = False
    ee.volumetric_tile_size = "8"; ee.volumetric_samples = 48; ee.use_volumetric_shadows = True
    ee.volumetric_end = 30
    vs = sc.view_settings
    vs.view_transform = "Filmic"
    for look in ("Filmic - Medium High Contrast", "Medium High Contrast"):
        try:
            vs.look = look; break
        except TypeError:
            pass
    w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
    return sc


def world(color=(0.01, 0.012, 0.016), strength=1.0, fog=0.0, fog_color=(1, 1, 1), aniso=0.4):
    w = bpy.context.scene.world; nt = w.node_tree
    bg = nt.nodes["Background"]; bg.inputs[0].default_value = (*color, 1); bg.inputs[1].default_value = strength
    if fog > 0:
        vol = nt.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Density"].default_value = fog
        vol.inputs["Color"].default_value = (*fog_color, 1)
        vol.inputs["Anisotropy"].default_value = aniso
        nt.links.new(vol.outputs[0], nt.nodes["World Output"].inputs["Volume"])


def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    return m, nt, p


def L(nt, a, b):
    nt.links.new(a, b)


def noise_mix(nt, p_input, c1, c2, scale=4.0, detail=8, lo=0.3, hi=0.7, coord="Generated", distortion=0.0):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
    n.inputs["Distortion"].default_value = distortion
    L(nt, tc.outputs[coord], n.inputs["Vector"])
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].position = lo; r.color_ramp.elements[1].position = hi
    r.color_ramp.elements[0].color = (*c1, 1); r.color_ramp.elements[1].color = (*c2, 1)
    L(nt, n.outputs["Fac"], r.inputs[0])
    if p_input is not None:
        L(nt, r.outputs[0], p_input)
    return r


def bump(nt, p, strength=0.15, scale=40.0, detail=10, coord="Generated"):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
    L(nt, tc.outputs[coord], n.inputs["Vector"])
    b = nt.nodes.new("ShaderNodeBump"); b.inputs["Strength"].default_value = strength
    L(nt, n.outputs["Fac"], b.inputs["Height"]); L(nt, b.outputs[0], p.inputs["Normal"])
    return b


def simple(name, color, rough=0.5, metal=0.0, spec=0.5, nvar=0.0, nscale=6.0, bump_s=0.0, bump_scale=60):
    m, nt, p = node_mat(name)
    p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metal
    p.inputs["Specular IOR Level"].default_value = spec
    if nvar > 0:
        c2 = tuple(min(1, c * (1 + nvar)) for c in color); c1 = tuple(c * (1 - nvar) for c in color)
        noise_mix(nt, p.inputs["Base Color"], c1, c2, scale=nscale)
    else:
        p.inputs["Base Color"].default_value = (*color, 1)
    if bump_s > 0: bump(nt, p, bump_s, bump_scale)
    return m


def wood(name, base=(0.16, 0.075, 0.03), dark=(0.06, 0.026, 0.01), rough=0.55, scale=3.0, plank_axis="X"):
    """Wood grain: stretched noise + wave rings."""
    m, nt, p = node_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1, 12, 1) if plank_axis == "X" else (12, 1, 1)
    L(nt, tc.outputs["Object"], mp.inputs["Vector"])
    wave = nt.nodes.new("ShaderNodeTexWave"); wave.inputs["Scale"].default_value = scale
    wave.inputs["Distortion"].default_value = 6; wave.inputs["Detail"].default_value = 4
    wave.bands_direction = "Y" if plank_axis == "X" else "X"
    L(nt, mp.outputs[0], wave.inputs["Vector"])
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].color = (*dark, 1); r.color_ramp.elements[1].color = (*base, 1)
    L(nt, wave.outputs["Fac"], r.inputs[0]); L(nt, r.outputs[0], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = rough
    b = nt.nodes.new("ShaderNodeBump"); b.inputs["Strength"].default_value = 0.08
    L(nt, wave.outputs["Fac"], b.inputs["Height"]); L(nt, b.outputs[0], p.inputs["Normal"])
    return m


def planks(name, base=(0.12, 0.06, 0.025), dark=(0.04, 0.02, 0.008), rough=0.6, width=0.18):
    """Floor boards: brick texture gives per-plank tint, wave gives grain."""
    m, nt, p = node_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = 2.2; br.inputs["Row Height"].default_value = width
    br.inputs["Mortar Size"].default_value = 0.004
    br.inputs["Color1"].default_value = (*base, 1)
    br.inputs["Color2"].default_value = tuple(c * 0.7 for c in base) + (1,)
    br.inputs["Mortar"].default_value = (*dark, 1)
    L(nt, tc.outputs["Object"], br.inputs["Vector"])
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.3, 6, 1)
    L(nt, tc.outputs["Object"], mp.inputs["Vector"])
    wave = nt.nodes.new("ShaderNodeTexWave"); wave.inputs["Scale"].default_value = 2
    wave.inputs["Distortion"].default_value = 8; wave.bands_direction = "Y"
    L(nt, mp.outputs[0], wave.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 0.45
    L(nt, br.outputs["Color"], mix.inputs[6]); L(nt, wave.outputs["Color"], mix.inputs[7])
    L(nt, mix.outputs[2], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = rough
    b = nt.nodes.new("ShaderNodeBump"); b.inputs["Strength"].default_value = 0.25
    L(nt, br.outputs["Fac"], b.inputs["Height"]); L(nt, b.outputs[0], p.inputs["Normal"])
    return m


def emit(name, color, strength):
    m, nt, p = node_mat(name)
    nt.nodes.remove(p)
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (*color, 1); e.inputs[1].default_value = strength
    L(nt, e.outputs[0], nt.nodes["Material Output"].inputs[0])
    return m


def board_mat(name, kind, tex=None, seq=0, sweep=None):
    """Writing-surface material. kind: green | black_slate | black_paint | white | eboard.
    tex: chalk RGBA image (or sequence dir) composited over the surface."""
    m, nt, p = node_mat(name)
    base = {"green": ((0.010, 0.040, 0.026), (0.020, 0.060, 0.040), 0.72),
            "black_slate": ((0.012, 0.013, 0.015), (0.03, 0.032, 0.036), 0.5),
            "black_paint": ((0.010, 0.010, 0.010), (0.022, 0.020, 0.018), 0.34),
            "white": ((0.80, 0.82, 0.82), (0.86, 0.87, 0.87), 0.12)}
    tc = nt.nodes.new("ShaderNodeTexCoord")
    if kind == "eboard":
        img = load_img(tex)
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img
        L(nt, tc.outputs["UV"], t.inputs["Vector"])
        L(nt, t.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = 2.2
        p.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)
        p.inputs["Roughness"].default_value = 0.08; p.inputs["Coat Weight"].default_value = 0.6
        return m
    if kind == "white":
        img = load_img(tex)
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img
        L(nt, tc.outputs["UV"], t.inputs["Vector"]); L(nt, t.outputs["Color"], p.inputs["Base Color"])
        p.inputs["Roughness"].default_value = 0.1; p.inputs["Coat Weight"].default_value = 0.5
        return m
    c1, c2, rough = base[kind]
    ramp = noise_mix(nt, None, c1, c2, scale=2.5, detail=10, lo=0.35, hi=0.75)
    # old erased-chalk smudges (low-frequency, horizontal streaks)
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "X"
    wv.inputs["Scale"].default_value = 1.4; wv.inputs["Distortion"].default_value = 9
    wv.inputs["Detail"].default_value = 3
    L(nt, tc.outputs["Generated"], wv.inputs["Vector"])
    sm = nt.nodes.new("ShaderNodeMath"); sm.operation = "MULTIPLY"; sm.inputs[1].default_value = 0.035 if kind != "black_paint" else 0.025
    L(nt, wv.outputs["Fac"], sm.inputs[0])
    mix0 = nt.nodes.new("ShaderNodeMix"); mix0.data_type = "RGBA"
    L(nt, sm.outputs[0], mix0.inputs[0]); L(nt, ramp.outputs[0], mix0.inputs[6])
    mix0.inputs[7].default_value = (0.35, 0.37, 0.36, 1)
    surf = mix0.outputs[2]
    if kind == "black_slate":
        bump(nt, p, 0.12, 25, 12)
    else:
        bump(nt, p, 0.03, 120, 6)
    if tex:
        img = load_img(tex, seq)
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.interpolation = "Cubic"
        if seq:
            t.image_user.frame_duration = seq; t.image_user.frame_start = 1
            t.image_user.frame_offset = 0; t.image_user.use_auto_refresh = True
        L(nt, tc.outputs["UV"], t.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
        a = nt.nodes.new("ShaderNodeMath"); a.operation = "MULTIPLY"; a.inputs[1].default_value = 0.93
        L(nt, t.outputs["Alpha"], a.inputs[0]); L(nt, a.outputs[0], mix.inputs[0])
        L(nt, surf, mix.inputs[6]); mix.inputs[7].default_value = (0.78, 0.79, 0.77, 1)
        L(nt, mix.outputs[2], p.inputs["Base Color"])
        rmix = nt.nodes.new("ShaderNodeMath"); rmix.operation = "MULTIPLY_ADD"
        L(nt, t.outputs["Alpha"], rmix.inputs[0]); rmix.inputs[1].default_value = 0.95 - rough; rmix.inputs[2].default_value = rough
        L(nt, rmix.outputs[0], p.inputs["Roughness"])
    else:
        L(nt, surf, p.inputs["Base Color"]); p.inputs["Roughness"].default_value = rough
    return m


_imgs = {}
def load_img(tex, seq=0):
    path = os.path.join(BOARDS, tex) if not tex.startswith("/") else tex
    if os.path.isdir(path): path = os.path.join(path, "0001.png")
    if path in _imgs: return _imgs[path]
    img = bpy.data.images.load(path)
    if seq: img.source = "SEQUENCE"
    _imgs[path] = img
    return img


# ------------------------------------------------------------------ geometry
def box(name, size, loc, mat=None, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        md = o.modifiers.new("bev", "BEVEL"); md.width = bevel; md.segments = 2
    if mat: o.data.materials.append(mat)
    return o


def plane(name, w, h, loc, rot, mat=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = (w, h, 1)
    bpy.ops.object.transform_apply(scale=True)
    if mat: o.data.materials.append(mat)
    return o


def cyl(name, r, depth, loc, rot=(0, 0, 0), mat=None, verts=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object; o.name = name
    if mat: o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


def wall_with_windows(name, x, y0, y1, h, windows, mat, thick=0.25):
    """Wall in the YZ plane at x; windows = list of (yc, z0, w, hgt). Built from boxes (no booleans)."""
    parts = []
    ys = sorted(windows)
    cur = y0
    for yc, z0, w, hh in ys:
        parts.append(box(name, (thick, yc - w / 2 - cur, h), (x, (cur + yc - w / 2) / 2, h / 2), mat))
        parts.append(box(name, (thick, w, z0), (x, yc, z0 / 2), mat))
        parts.append(box(name, (thick, w, h - z0 - hh), (x, yc, (z0 + hh + h) / 2), mat))
        cur = yc + w / 2
    parts.append(box(name, (thick, y1 - cur, h), (x, (cur + y1) / 2, h / 2), mat))
    return parts


def window_frames(x, windows, mat, panes=(2, 3), bar=0.04):
    for yc, z0, w, hh in windows:
        box("wf", (0.08, w, bar * 1.5), (x, yc, z0), mat); box("wf", (0.08, w, bar * 1.5), (x, yc, z0 + hh), mat)
        box("wf", (0.08, bar * 1.5, hh), (x, yc - w / 2, z0 + hh / 2), mat); box("wf", (0.08, bar * 1.5, hh), (x, yc + w / 2, z0 + hh / 2), mat)
        for i in range(1, panes[0]):
            box("wm", (0.05, bar, hh), (x, yc - w / 2 + w * i / panes[0], z0 + hh / 2), mat)
        for j in range(1, panes[1]):
            box("wm", (0.05, w, bar), (x, yc, z0 + hh * j / panes[1]), mat)


def sun(rot_dir, energy, color=(1, 0.95, 0.85), angle=0.02):
    bpy.ops.object.light_add(type="SUN")
    s = bpy.context.object; s.data.energy = energy; s.data.color = color; s.data.angle = angle
    d = Vector(rot_dir).normalized()
    s.rotation_euler = (-d).to_track_quat("Z", "Y").to_euler()
    s.data.shadow_cascade_max_distance = 25; s.data.use_contact_shadow = True
    return s


def area(loc, target, energy, size=1.0, color=(1, 1, 1), shape="SQUARE", size_y=None):
    bpy.ops.object.light_add(type="AREA", location=loc)
    a = bpy.context.object; a.data.energy = energy; a.data.size = size; a.data.color = color
    if size_y:
        a.data.shape = "RECTANGLE"; a.data.size_y = size_y
    a.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return a


def spot(loc, target, energy, angle=40, blend=0.6, color=(1, 1, 1), radius=0.1):
    bpy.ops.object.light_add(type="SPOT", location=loc)
    s = bpy.context.object; s.data.energy = energy; s.data.spot_size = math.radians(angle)
    s.data.spot_blend = blend; s.data.color = color; s.data.shadow_soft_size = radius
    s.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return s


def point(loc, energy, color=(1, 1, 1), radius=0.2):
    bpy.ops.object.light_add(type="POINT", location=loc)
    p = bpy.context.object; p.data.energy = energy; p.data.color = color; p.data.shadow_soft_size = radius
    return p


# ------------------------------------------------------------------ camera
def camera(keys, n, lens=28, fstop=2.8, focus_offset=None, ease=True):
    """keys: list of (frac, cam_loc, target_loc[, lens])."""
    sc = bpy.context.scene
    bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
    cam.data.lens = lens; cam.data.sensor_fit = "AUTO"; cam.data.sensor_width = 36
    cam.data.clip_start = 0.01; cam.data.clip_end = 100
    bpy.ops.object.empty_add(); tgt = bpy.context.object; tgt.name = "target"
    c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    cam.data.dof.use_dof = fstop is not None
    if fstop:
        cam.data.dof.aperture_fstop = fstop; cam.data.dof.focus_object = tgt
    for k in keys:
        f = 1 + k[0] * (n - 1)
        cam.location = k[1]; cam.keyframe_insert("location", frame=f)
        tgt.location = k[2]; tgt.keyframe_insert("location", frame=f)
        if len(k) > 3:
            cam.data.lens = k[3]; cam.data.keyframe_insert("lens", frame=f)
    for ob in (cam, tgt):
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"; kp.easing = "AUTO"
                if not ease: kp.interpolation = "LINEAR"
    # subtle handheld drift for documentary feel
    for i, fc in enumerate(cam.animation_data.action.fcurves):
        md = fc.modifiers.new("NOISE"); md.scale = 90; md.strength = 0.012; md.phase = i * 13.0
    return cam, tgt


# ------------------------------------------------------------------ props
def chalk_stick(mat=None, color=(0.85, 0.85, 0.82), r=0.0055, length=0.075):
    m = mat or simple("chalk", color, 0.95, spec=0.2, nvar=0.05, bump_s=0.3, bump_scale=200)
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=length, vertices=16, location=(0, 0, length / 2))
    o = bpy.context.object; o.name = "chalkstick"; o.data.materials.append(m)
    bpy.ops.object.transform_apply(location=True)   # origin at the writing tip
    bpy.ops.object.shade_smooth()
    return o


def animate_pen(obj, seq_dir, board_center, board_w, board_h, n, normal=(0, -1, 0), tilt=(0.30, -0.85, -0.40),
                start_frame=1, hide_after=True, frames_filter=None):
    """Move the stick tip along pen.json (uv) over a vertical board facing -Y."""
    pens = json.load(open(os.path.join(BOARDS, seq_dir, "pen.json")))
    d = Vector(tilt).normalized()
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    cx, cy, cz = board_center
    last = None
    for i in range(n):
        f = start_frame + i
        p = pens[i] if i < len(pens) else None
        if frames_filter and not frames_filter(i): p = None
        if p:
            u, v = p[0], p[1]
            loc = Vector((cx + (u - 0.5) * board_w, cy - 0.004, cz + (0.5 - v) * board_h))
            obj.location = loc; obj.scale = (1, 1, 1); last = loc
        else:
            obj.scale = (0, 0, 0)
            if last is not None: obj.location = last
        obj.keyframe_insert("location", frame=f); obj.keyframe_insert("scale", frame=f)
    for fc in obj.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT" if fc.data_path == "scale" else "LINEAR"
    return pens


def dust(origins, mat, per=3, fall=0.35, life=40, seed=3):
    """Tiny chalk specks spawned at given (frame, Vector) origins, drifting down."""
    r = random.Random(seed)
    for f0, o in origins:
        for k in range(per):
            bpy.ops.mesh.primitive_ico_sphere_add(radius=r.uniform(0.0007, 0.0018), subdivisions=1, location=o)
            s = bpy.context.object; s.data.materials.append(mat)
            s.scale = (0, 0, 0); s.keyframe_insert("scale", frame=max(1, f0 - 1))
            s.scale = (1, 1, 1); s.keyframe_insert("scale", frame=f0)
            s.location = o; s.keyframe_insert("location", frame=f0)
            s.location = o + Vector((r.uniform(-0.04, 0.04), r.uniform(-0.06, -0.01), -fall * r.uniform(0.6, 1.2)))
            s.keyframe_insert("location", frame=f0 + life)
            s.scale = (0, 0, 0); s.keyframe_insert("scale", frame=f0 + life)


# ------------------------------------------------------------------ sets
def modern_room(variant="day", board_kind="green", board_tex=None, seq=0, showa=False, sweep=None):
    """Japanese classroom. Front wall y=1.0, board centre (0, 0.98, 1.45) 4.0 x 1.2."""
    W, D0, D1, H = 4.6, -6.5, 1.0, 3.1
    wallc = (0.62, 0.58, 0.50) if showa else (0.70, 0.69, 0.64)
    wall = simple("wall", wallc, 0.85, nvar=0.06, nscale=3, bump_s=0.05)
    floor = planks("floor", (0.20, 0.11, 0.05) if showa else (0.30, 0.20, 0.11), rough=0.45 if showa else 0.35, width=0.12)
    box("floor", (2 * W, D1 - D0 + 1, 0.1), (0, (D0 + D1) / 2, -0.05), floor)
    ceil = box("ceiling", (2 * W, D1 - D0 + 1, 0.1), (0, (D0 + D1) / 2, H + 0.05), simple("ceil", (0.75, 0.75, 0.72), 0.9))
    box("front", (2 * W, 0.2, H), (0, D1 + 0.1, H / 2), wall)
    box("back", (2 * W, 0.2, H), (0, D0 - 0.1, H / 2), wall)
    box("right", (0.2, D1 - D0, H), (W + 0.1, (D0 + D1) / 2, H / 2), wall)
    wins = [(-5.2, 0.85, 1.5, 1.75), (-3.0, 0.85, 1.5, 1.75), (-0.8, 0.85, 1.5, 1.75)]
    wall_with_windows("left", -W - 0.1, D0, D1, H, wins, wall, 0.2)
    frame_m = wood("winframe", (0.25, 0.15, 0.08), (0.12, 0.06, 0.03)) if showa else simple("alu", (0.6, 0.6, 0.62), 0.35, metal=0.8)
    window_frames(-W - 0.05, wins, frame_m, panes=(2, 2) if not showa else (3, 3))
    # skirting + wainscot
    box("skirt", (2 * W, 0.03, 0.12), (0, D1 - 0.015, 0.06), wood("skirt", (0.15, 0.08, 0.04), (0.08, 0.04, 0.02)))
    # board
    bw, bh, bc = 4.0, 1.2, (0, 0.985, 1.45)
    if board_kind == "morph":
        morph_boards(bw, bh, bc, sweep); bd = None
    else:
        bd = plane("board", bw, bh, bc, (math.radians(90), 0, 0), board_mat("board", board_kind, board_tex, seq))
    fr = wood("bframe", (0.22, 0.12, 0.06), (0.10, 0.05, 0.02)) if showa else simple("bframe", (0.55, 0.56, 0.58), 0.3, metal=0.9)
    for (sx, sz, x, z) in [(bw + 0.1, 0.05, 0, bc[2] + bh / 2 + 0.025), (bw + 0.1, 0.05, 0, bc[2] - bh / 2 - 0.025),
                           (0.05, bh, -bw / 2 - 0.025, bc[2]), (0.05, bh, bw / 2 + 0.025, bc[2])]:
        box("bfr", (sx, 0.04, sz), (x, 0.975, z), fr)
    box("tray", (bw, 0.09, 0.025), (0, 0.94, bc[2] - bh / 2 - 0.06), fr)
    cm = simple("chalk2", (0.8, 0.8, 0.78), 0.95)
    for i, c in enumerate([(0.85, 0.85, 0.82), (0.9, 0.75, 0.2), (0.85, 0.3, 0.3), (0.85, 0.85, 0.82)]):
        o = cyl("trc", 0.0055, 0.07, (-1.2 + i * 0.18, 0.93, bc[2] - bh / 2 - 0.04), (0, math.radians(90), 0.2 * i), simple(f"tc{i}", c, 0.95))
    box("eraser", (0.14, 0.05, 0.035), (0.9, 0.93, bc[2] - bh / 2 - 0.03), simple("eras", (0.25, 0.2, 0.15), 0.9))
    # teacher's platform & podium
    box("platform", (5.0, 1.0, 0.15), (0, 0.45, 0.075), wood("plat", (0.18, 0.10, 0.05), (0.09, 0.05, 0.02)))
    box("podium", (0.9, 0.5, 1.0), (1.7, -0.1, 0.65), wood("pod", (0.24, 0.13, 0.06), (0.12, 0.06, 0.03)), bevel=0.01)
    # desks
    deskm = wood("desk", (0.33, 0.20, 0.10), (0.18, 0.10, 0.04)) if showa else simple("lam", (0.55, 0.44, 0.30), 0.4, nvar=0.05)
    leg = wood("leg", (0.2, 0.1, 0.05), (0.1, 0.05, 0.02)) if showa else simple("steel", (0.25, 0.27, 0.3), 0.4, metal=0.85)
    seat = wood("seat", (0.28, 0.16, 0.08), (0.14, 0.07, 0.03)) if showa else simple("ply", (0.45, 0.32, 0.18), 0.45)
    for cx in (-2.4, -0.8, 0.8, 2.4):
        for ry in (-1.4, -2.6, -3.8, -5.0):
            x = cx + (0.04 * math.sin(cx * 7 + ry * 3)); y = ry
            box("desk", (0.62, 0.45, 0.03), (x, y, 0.71), deskm, bevel=0.005)
            box("deskbox", (0.58, 0.40, 0.12), (x, y + 0.01, 0.63), leg if showa else deskm)
            for lx in (-0.28, 0.28):
                for ly in (-0.19, 0.19):
                    box("leg", (0.025, 0.025, 0.57), (x + lx, y + ly, 0.285), leg)
            box("seat", (0.40, 0.38, 0.025), (x, y - 0.42, 0.42), seat, bevel=0.004)
            box("back", (0.40, 0.025, 0.25), (x, y - 0.62, 0.66), seat, bevel=0.004)
            for lx in (-0.18, 0.18):
                for ly in (-0.58, -0.26):
                    box("cleg", (0.022, 0.022, 0.42), (x + lx, y + ly, 0.21), leg)
    # ceiling lights
    lights = []
    for x in (-1.8, 1.8):
        for y in (-0.5, -3.0, -5.5):
            lights.append(box("lamp", (0.25, 1.25, 0.04), (x, y, H - 0.03), emit("lampm", (1, 0.98, 0.94), 6 if variant == "day" else 0.0)))
    # outside: sky plane & ground
    skyc = {"day": ((0.75, 0.85, 1.0), 2.5), "dusk": ((1.0, 0.55, 0.28), 2.0), "dark": ((0.05, 0.08, 0.16), 0.6)}[variant if variant in ("day", "dusk", "dark") else "day"]
    plane("sky", 0.1, 1, (-W - 6, -2.5, 2), (0, math.radians(90), 0), emit("skym", *skyc)).scale = (60, 30, 1)
    box("ground", (10, 40, 0.1), (-W - 5.5, -2.5, -0.3), simple("grass", (0.08, 0.12, 0.05), 0.9))
    box("bulletin", (0.03, 2.4, 0.9), (W - 0.02, -3.0, 1.7), simple("cork", (0.35, 0.22, 0.12), 0.9, nvar=0.2, nscale=60))
    bpy.ops.object.select_all(action="DESELECT")
    return bd, (bw, bh, bc)


def add_wipe(m, f0, f1):
    """Make material m disappear left-to-right between frames f0..f1 (alpha clip on UV.x)."""
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(nt, tc.outputs["UV"], sep.inputs[0])
    val = nt.nodes.new("ShaderNodeValue")
    val.outputs[0].default_value = -0.02; val.outputs[0].keyframe_insert("default_value", frame=f0)
    val.outputs[0].default_value = 1.02; val.outputs[0].keyframe_insert("default_value", frame=f1)
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"
    L(nt, sep.outputs[0], gt.inputs[0]); L(nt, val.outputs[0], gt.inputs[1]); L(nt, gt.outputs[0], p.inputs["Alpha"])
    m.blend_method = "CLIP"; m.shadow_method = "CLIP"


def morph_boards(bw, bh, bc, sweep):
    """green chalk -> whiteboard -> e-board, stacked surfaces wiped away with a glowing seam."""
    layers = [("green", "GAL_CHALK"), ("white", "WHITE.png"), ("eboard", "EBOARD.png")]
    glow = emit("seam", (1.0, 0.85, 0.55), 30)
    for i, (kind, tex) in enumerate(layers):
        m = board_mat("mb_" + kind, kind, tex)
        if i < len(sweep):
            add_wipe(m, *sweep[i])
            sb = box("seam", (0.012, 0.01, bh), (0, bc[1] - 0.006, bc[2]), glow)
            sb.location.x = -bw / 2; sb.keyframe_insert("location", frame=sweep[i][0])
            sb.location.x = bw / 2; sb.keyframe_insert("location", frame=sweep[i][1])
            sb.scale = (0, 0, 0); sb.keyframe_insert("scale", frame=sweep[i][0] - 1); sb.keyframe_insert("scale", frame=sweep[i][1] + 1)
            sb.scale = (1, 1, 1); sb.keyframe_insert("scale", frame=sweep[i][0]); sb.keyframe_insert("scale", frame=sweep[i][1])
            for fc in sb.animation_data.action.fcurves:
                for kp in fc.keyframe_points: kp.interpolation = "CONSTANT" if fc.data_path == "scale" else "LINEAR"
        plane("mboard", bw, bh, (bc[0], bc[1] - 0.003 + 0.0012 * i, bc[2]), (math.radians(90), 0, 0), m)


def hist_room(board=None, slates=True, fog=0.012):
    """Early-19th-century schoolroom: lime-washed walls, plank floor, long desks with benches, slates."""
    W, D0, D1, H = 4.0, -7.5, 0.6, 3.3
    wall = simple("lime", (0.55, 0.50, 0.42), 0.95, nvar=0.18, nscale=1.5, bump_s=0.2, bump_scale=8)
    floor = planks("hfloor", (0.10, 0.06, 0.03), (0.02, 0.012, 0.006), 0.7, width=0.24)
    box("floor", (2 * W, D1 - D0 + 1, 0.1), (0, (D0 + D1) / 2, -0.05), floor)
    c = box("ceiling", (2 * W, D1 - D0 + 1, 0.1), (0, (D0 + D1) / 2, H + 0.05), simple("hceil", (0.4, 0.36, 0.3), 0.95))
    beam = wood("beam", (0.10, 0.06, 0.03), (0.04, 0.02, 0.01), 0.8)
    for y in (-6.0, -4.0, -2.0, 0.0):
        box("beam", (2 * W, 0.22, 0.25), (0, y, H - 0.12), beam)
    box("front", (2 * W, 0.2, H), (0, D1 + 0.1, H / 2), wall)
    box("back", (2 * W, 0.2, H), (0, D0 - 0.1, H / 2), wall)
    box("right", (0.2, D1 - D0, H), (W + 0.1, (D0 + D1) / 2, H / 2), wall)
    wins = [(-5.8, 1.0, 1.1, 1.6), (-3.4, 1.0, 1.1, 1.6), (-1.0, 1.0, 1.1, 1.6)]
    wall_with_windows("left", -W - 0.1, D0, D1, H, wins, wall, 0.35)
    wf = wood("hwin", (0.30, 0.26, 0.20), (0.18, 0.15, 0.1), 0.8)
    window_frames(-W - 0.05, wins, wf, panes=(3, 4), bar=0.03)
    plane("sky", 1, 1, (-W - 6, -3, 2), (0, math.radians(90), 0), emit("skym", (0.9, 0.92, 1.0), 3.0)).scale = (60, 30, 1)
    # teacher's desk on platform, globe
    box("platform", (3.0, 1.4, 0.2), (0, -0.2, 0.1), planks("plat", (0.12, 0.07, 0.035)))
    tdm = wood("tdesk", (0.16, 0.08, 0.035), (0.06, 0.03, 0.01), 0.5)
    box("tdesk", (1.4, 0.7, 0.05), (1.3, -0.5, 0.98), tdm, bevel=0.01)
    box("tdesk_b", (1.3, 0.6, 0.6), (1.3, -0.5, 0.6), tdm)
    cyl("gstand", 0.015, 0.25, (1.75, -0.5, 1.13), mat=simple("brass", (0.6, 0.45, 0.2), 0.35, metal=1))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(1.75, -0.5, 1.38), segments=32, ring_count=16)
    g = bpy.context.object; bpy.ops.object.shade_smooth()
    g.data.materials.append(simple("globe", (0.45, 0.38, 0.22), 0.5, nvar=0.5, nscale=3))
    # books on teacher desk
    for i, col in enumerate([(0.2, 0.05, 0.03), (0.08, 0.1, 0.05), (0.15, 0.1, 0.05)]):
        box("book", (0.22, 0.16, 0.04), (0.9, -0.5 + 0.02 * i, 1.03 + 0.04 * i), simple(f"bk{i}", col, 0.7), rot=(0, 0, 0.1 * i), bevel=0.004)
    # long desks + benches: 4 rows x 2 columns, 3 seats each
    dm = wood("hdesk", (0.18, 0.10, 0.05), (0.07, 0.035, 0.015), 0.6)
    slate_spots = []
    for ci, cx in enumerate((-1.7, 1.5)):
        for ri, ry in enumerate((-2.2, -3.5, -4.8, -6.1)):
            box("hdesk", (2.4, 0.5, 0.05), (cx, ry, 0.76), dm, rot=(math.radians(-8), 0, 0), bevel=0.008)
            box("hdesk_f", (2.4, 0.04, 0.45), (cx, ry + 0.24, 0.5), dm)
            for lx in (-1.1, 1.1):
                box("hleg", (0.06, 0.45, 0.74), (cx + lx, ry, 0.37), dm)
            box("bench", (2.4, 0.28, 0.05), (cx, ry - 0.55, 0.44), dm, bevel=0.008)
            for lx in (-1.05, 0, 1.05):
                box("bleg", (0.05, 0.24, 0.42), (cx + lx, ry - 0.55, 0.21), dm)
            for si, sx in enumerate((-0.75, 0.0, 0.75)):
                slate_spots.append((cx + sx + 0.05 * math.sin(ri * 3 + si), ry - 0.02, 0.795, (ri * 3 + si + ci * 5) % 12))
    sun((0.75, 0.32, -0.5), 6.0, (1.0, 0.88, 0.7), angle=0.015)
    world((0.02, 0.02, 0.025), 1.0, fog=fog, fog_color=(1, 0.95, 0.88))
    area((0, -3.5, 3.1), (0, -3.5, 0), 120, size=4, color=(1, 0.9, 0.8))   # bounce fill
    if board:
        pass
    return slate_spots


def desk_slate(spot, frame_m, idx, scale=1.0, tex=None, seq=0, name="slate"):
    """A school slate (0.30 x 0.22) in a wooden frame lying on a sloped desk. Returns parent empty."""
    x, y, z, k = spot
    bpy.ops.object.empty_add(location=(x, y, z)); e = bpy.context.object; e.name = name
    e.rotation_euler = (math.radians(-8), 0, math.radians((k % 5 - 2) * 3))
    sm = board_mat(f"slm{idx}", "black_slate", tex or f"SLATE{k}", seq)
    s = plane("slatesurf", 0.28, 0.20, (0, 0, 0.006), (0, 0, 0), sm); s.parent = e
    for (sx, sy, px, py) in [(0.30, 0.012, 0, 0.105), (0.30, 0.012, 0, -0.105), (0.012, 0.22, -0.145, 0), (0.012, 0.22, 0.145, 0)]:
        b = box("sfr", (sx, sy, 0.012), (px, py, 0.006), frame_m, bevel=0.002); b.parent = e
    e.scale = (scale, scale, scale)
    return e


# ------------------------------------------------------------------ studio
def studio(color=(0.006, 0.006, 0.008), fog=0.0):
    world(color, 1.0, fog=fog)
    box("cyc", (30, 0.2, 12), (0, 3, 6), simple("dark", (0.02, 0.02, 0.022), 0.8))
    box("table", (30, 30, 0.1), (0, 0, -0.05), simple("tbl", (0.03, 0.03, 0.032), 0.6, nvar=0.1))


# ================================================================== shots
def shot_A1(n):
    sc = reset()
    world((0.004, 0.006, 0.012), 1.0, fog=0.02, fog_color=(0.7, 0.8, 1.0))
    bd, (bw, bh, bc) = modern_room("dark", "green", "A1", seq=n)
    sp = spot((0, -1.2, 3.0), (0, 1, 1.4), 0, angle=70, blend=0.8, color=(1, 0.93, 0.82))
    sp.data.energy = 0; sp.data.keyframe_insert("energy", frame=1)
    sp.data.energy = 420; sp.data.keyframe_insert("energy", frame=40)
    area((-6, -3, 2.0), (0, -3, 0.5), 300, size=3, color=(0.5, 0.6, 1.0))
    cs = chalk_stick(); animate_pen(cs, "A1", bc, bw, bh, n)
    camera([(0, (0.35, -6.2, 1.5), (0.1, 1, 1.5)), (1, (-0.30, -2.35, 1.42), (-0.30, 1, 1.47))], n, lens=28, fstop=2.2)


def shot_B1(n):
    reset(); spots = hist_room()
    fm = wood("sframe", (0.30, 0.18, 0.08), (0.15, 0.08, 0.03))
    for i, s in enumerate(spots): desk_slate(s, fm, i)
    pen_m = simple("spencil", (0.25, 0.25, 0.27), 0.5)
    camera([(0, (-2.9, -7.0, 1.55), (-0.6, -2.5, 0.9)), (1, (-0.6, -7.1, 1.75), (0.8, -2.0, 0.95))], n, lens=26, fstop=4.0)


def shot_B2(n):
    reset(); spots = hist_room(fog=0.006)
    fm = wood("sframe", (0.30, 0.18, 0.08), (0.15, 0.08, 0.03))
    hero = spots[1]
    for i, s in enumerate(spots):
        desk_slate(s, fm, i, tex="B2" if s is hero else None, seq=n if s is hero else 0)
    # slate pencil (writing) and a cloth (erasing) follow pen.json, mapped onto the hero slate
    x, y, z, k = hero
    pens = json.load(open(os.path.join(BOARDS, "B2", "pen.json")))
    pencil = cyl("spencil", 0.0035, 0.12, (0, 0, 0.06), mat=simple("sp", (0.35, 0.35, 0.37), 0.6))
    bpy.context.view_layer.objects.active = pencil
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    rag = box("rag", (0.08, 0.06, 0.025), (0, 0, 0), simple("cloth", (0.45, 0.40, 0.32), 1.0, nvar=0.2, nscale=80, bump_s=0.5, bump_scale=150), bevel=0.01)
    d = Vector((0.35, -0.45, 0.82)).normalized(); pencil.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    tilt = math.radians(-8); rotk = math.radians((k % 5 - 2) * 3)
    for i in range(n):
        p = pens[i] if i < len(pens) else None
        erasing = 72 <= i <= 92
        for o in (pencil, rag):
            o.scale = (0, 0, 0)
        if p:
            lx, ly = (p[0] - 0.5) * 0.28, (0.5 - p[1]) * 0.20
            v = Vector((lx, ly, 0.008)); v.rotate(Euler((tilt, 0, rotk)))
            loc = Vector((x, y, z)) + v
            o = rag if erasing else pencil
            o.location = loc + (Vector((0, 0, 0.012)) if erasing else Vector()); o.scale = (1, 1, 1)
        for o in (pencil, rag):
            o.keyframe_insert("location", frame=i + 1); o.keyframe_insert("scale", frame=i + 1)
    for o in (pencil, rag):
        for fc in o.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT" if fc.data_path == "scale" else "LINEAR"
    camera([(0, (x + 0.20, y - 0.55, z + 0.48), (x + 0.01, y, z)), (1, (x + 0.08, y - 0.50, z + 0.44), (x, y + 0.01, z))], n, lens=50, fstop=2.2)


def shot_B3(n):
    reset(); spots = hist_room()
    fm = wood("sframe", (0.30, 0.18, 0.08), (0.15, 0.08, 0.03))
    for i, s in enumerate(spots): desk_slate(s, fm, i)
    for o in bpy.data.objects:
        if o.name.startswith(("ceiling", "beam")): o.visible_camera = False
    camera([(0, (-1.2, -6.6, 3.1), (-0.9, -5.0, 0.7)), (1, (0.4, -3.4, 3.2), (0.2, -2.6, 0.7))], n, lens=24, fstop=5.6)


def hist_board_frame(bw=4.4, bh=1.6, bc=(0, 0.57, 1.65), alpha_keys=None, tex=None, seq=0):
    bm = board_mat("bigslate", "black_slate", tex, seq)
    bd = plane("bigboard", bw, bh, bc, (math.radians(90), 0, 0), bm)
    fr = wood("bbfr", (0.16, 0.09, 0.04), (0.07, 0.035, 0.015), 0.6)
    parts = [bd]
    for (sx, sz, x, z) in [(bw + 0.16, 0.08, 0, bc[2] + bh / 2 + 0.04), (bw + 0.16, 0.08, 0, bc[2] - bh / 2 - 0.04),
                           (0.08, bh, -bw / 2 - 0.04, bc[2]), (0.08, bh, bw / 2 + 0.04, bc[2])]:
        parts.append(box("bbf", (sx, 0.05, sz), (x, bc[1] - 0.01, z), fr))
    parts.append(box("btray", (bw, 0.1, 0.03), (0, bc[1] - 0.06, bc[2] - bh / 2 - 0.09), fr))
    return parts, (bw, bh, bc)


def shot_C1(n):
    reset(); spots = hist_room()
    fm = wood("sframe", (0.30, 0.18, 0.08), (0.15, 0.08, 0.03))
    parts, (bw, bh, bc) = hist_board_frame()
    # the big board fades in over the assembled slates at the end
    for p in parts:
        p.scale = (0.0, 0.0, 0.0) if p.name != "bigboard" else (0.0, 1, 0.0)
    rnd = random.Random(4)
    cols, rows = 6, 4
    cw, ch = bw / cols, bh / rows
    order = list(range(len(spots))); rnd.shuffle(order)
    for i, s in enumerate(spots):
        e = desk_slate(s, fm, i)
        gi = order[i]; gx, gz = gi % cols, gi // cols
        dest = Vector((bc[0] - bw / 2 + cw * (gx + 0.5), bc[1] - 0.03, bc[2] + bh / 2 - ch * (gz + 0.5)))
        f0 = 12 + int(i * 3.2) + rnd.randint(0, 6); f1 = f0 + 42
        e.keyframe_insert("location", frame=f0); e.keyframe_insert("rotation_euler", frame=f0); e.keyframe_insert("scale", frame=f0)
        mid = (Vector(e.location) + dest) / 2 + Vector((rnd.uniform(-0.5, 0.5), -0.6, 0.9))
        e.location = mid; e.rotation_euler = (math.radians(40), rnd.uniform(-1, 1), rnd.uniform(-0.6, 0.6))
        e.keyframe_insert("location", frame=(f0 + f1) // 2); e.keyframe_insert("rotation_euler", frame=(f0 + f1) // 2)
        e.location = dest; e.rotation_euler = (math.radians(90), 0, 0)
        e.scale = (cw / 0.30, ch / 0.22, cw / 0.30)
        e.keyframe_insert("location", frame=f1); e.keyframe_insert("rotation_euler", frame=f1); e.keyframe_insert("scale", frame=f1)
        # sink into the wall once the solid board appears
        e.keyframe_insert("location", frame=n - 30)
        e.location = dest + Vector((0, 0.06, 0)); e.keyframe_insert("location", frame=n - 18)
    for p in parts:
        tgt = p.scale.copy(); p.keyframe_insert("scale", frame=n - 32)
        p.scale = (1, 1, 1); p.keyframe_insert("scale", frame=n - 18)
    # flash of light at the moment of union
    pl = point((0, -0.6, 1.7), 0, (1, 0.85, 0.6), 0.5)
    pl.data.keyframe_insert("energy", frame=n - 34); pl.data.energy = 600; pl.data.keyframe_insert("energy", frame=n - 22)
    pl.data.energy = 0; pl.data.keyframe_insert("energy", frame=n - 4)
    camera([(0, (0.3, -7.0, 1.7), (0, -2.0, 1.2)), (0.45, (0.1, -6.6, 1.75), (0, -0.5, 1.4)), (1, (0, -5.6, 1.7), (0, 0.6, 1.6))], n, lens=26, fstop=4.0)


def shot_C2(n):
    reset(); spots = hist_room()
    fm = wood("sframe", (0.30, 0.18, 0.08), (0.15, 0.08, 0.03))
    for i, s in enumerate(spots): desk_slate(s, fm, i)
    parts, (bw, bh, bc) = hist_board_frame(tex="C2", seq=n)
    cs = chalk_stick(); animate_pen(cs, "C2", bc, bw, bh, n)
    spot((0, -1.5, 3.1), (0, 0.57, 1.6), 500, angle=80, blend=0.9, color=(1, 0.92, 0.8))
    camera([(0, (-1.3, -2.1, 1.55), (-1.1, 0.57, 1.6)), (1, (0.55, -2.0, 1.6), (0.5, 0.57, 1.6))], n, lens=28, fstop=4.0)


def shot_C3(n):
    reset(); spots = hist_room()
    parts, (bw, bh, bc) = hist_board_frame(tex="C3", seq=n)
    cs = chalk_stick(); pens = animate_pen(cs, "C3", bc, bw, bh, n)
    dm = emit("dust", (0.9, 0.9, 0.85), 0.6)
    org = []
    for i, p in enumerate(pens[:n]):
        if p and i % 2 == 0:
            org.append((i + 1, Vector((bc[0] + (p[0] - 0.5) * bw, bc[1] - 0.01, bc[2] + (0.5 - p[1]) * bh))))
    dust(org, dm, per=2)
    qx = bc[0] + (0.86 - 0.5) * bw; qz = bc[2] + (0.5 - 0.70) * bh
    spot((qx - 0.8, -1.2, 2.6), (qx, bc[1], qz), 260, angle=60, blend=0.9, color=(1, 0.92, 0.8))
    camera([(0, (qx - 0.75, bc[1] - 1.55, qz + 0.1), (qx - 0.25, bc[1], qz + 0.05)), (1, (qx - 0.35, bc[1] - 1.25, qz + 0.02), (qx, bc[1], qz))], n, lens=40, fstop=2.8)


def shot_C4(n):
    reset(); spots = hist_room()
    fm = wood("sframe", (0.30, 0.18, 0.08), (0.15, 0.08, 0.03))
    for i, s in enumerate(spots): desk_slate(s, fm, i)
    parts, (bw, bh, bc) = hist_board_frame(tex="C4")
    for o in bpy.data.objects:
        if o.name.startswith(("ceiling",)): o.visible_camera = False
    camera([(0, (0.0, -1.9, 1.25), (0, 0.57, 1.6)), (1, (0.2, -7.2, 2.6), (0, 0.0, 1.3))], n, lens=26, fstop=5.6)


def shot_D1(n):
    reset(); world((0.02, 0.025, 0.03))
    bd, (bw, bh, bc) = modern_room("day", "green", "D1", seq=n)
    sun((0.8, 0.45, -0.45), 3.5, (1, 0.95, 0.85))
    area((0, -3, 3.0), (0, -3, 0), 250, size=5)
    cs = chalk_stick(); animate_pen(cs, "D1", bc, bw, bh, n)
    camera([(0, (0.25, -3.6, 1.4), (-0.05, 1, 1.45)), (1, (0.0, -2.1, 1.45), (-0.08, 1, 1.45))], n, lens=30, fstop=2.8)


def shot_D2(n):
    reset(); studio(fog=0.0)
    slate = board_mat("natslate", "black_slate")
    s = box("slab_slate", (1.0, 0.7, 0.03), (-0.52, 0, 0.015), slate, bevel=0.004)
    # painted wood: grain shows through black paint
    m, nt, p = node_mat("paintwood")
    wd = wood("tmpw")
    ramp = noise_mix(nt, None, (0.008, 0.008, 0.008), (0.03, 0.025, 0.02), scale=6)
    p.inputs["Base Color"].default_value = (0.012, 0.011, 0.01, 1); p.inputs["Roughness"].default_value = 0.38
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 14, 1)
    L(nt, tc.outputs["Object"], mp.inputs["Vector"])
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 3; wv.inputs["Distortion"].default_value = 7; wv.bands_direction = "Y"
    L(nt, mp.outputs[0], wv.inputs["Vector"])
    L(nt, ramp.outputs[0], p.inputs["Base Color"])
    b = nt.nodes.new("ShaderNodeBump"); b.inputs["Strength"].default_value = 0.15
    L(nt, wv.outputs["Fac"], b.inputs["Height"]); L(nt, b.outputs[0], p.inputs["Normal"])
    w = box("slab_wood", (1.0, 0.7, 0.03), (0.52, 0, 0.015), m, bevel=0.004)
    area((-1.8, -0.2, 0.45), (0, 0, 0), 35, size=1.2, color=(1, 0.92, 0.8))
    area((1.2, 1.0, 0.8), (0, 0, 0), 25, size=1.5, color=(0.7, 0.8, 1.0))
    area((0, -1.0, 1.4), (0, 0, 0), 12, size=2)
    chalkm = simple("chalkp", (0.85, 0.85, 0.82), 0.95)
    for i in range(4):
        cyl("chalkpiece", 0.0055, 0.04 + 0.01 * i, (-0.7 + 0.12 * i, -0.18 + 0.05 * i, 0.036), (0, math.radians(90), 0.4 * i), chalkm)
    camera([(0, (-0.75, -0.55, 0.42), (-0.50, 0.0, 0.03)), (1, (0.62, -0.55, 0.40), (0.50, 0.0, 0.03))], n, lens=45, fstop=3.2, ease=True)


def shot_D3(n):
    reset(); studio()
    ply = wood("plywood", (0.45, 0.32, 0.18), (0.30, 0.20, 0.10), 0.7)
    steel = simple("steel", (0.55, 0.56, 0.58), 0.32, metal=1.0, bump_s=0.02)
    m, nt, p = node_mat("enamel")
    p.inputs["Roughness"].default_value = 0.6
    col = p.inputs["Base Color"]; emc = p.inputs["Emission Color"]; ems = p.inputs["Emission Strength"]
    emc.default_value = (1.0, 0.35, 0.05, 1)
    keys = [(1, (0.02, 0.02, 0.02), 0.0), (70, (0.02, 0.02, 0.02), 0.0), (95, (0.25, 0.08, 0.02), 6.0),
            (120, (0.03, 0.10, 0.06), 1.5), (150, (0.012, 0.045, 0.03), 0.0)]
    for f, c, e in keys:
        col.default_value = (*c, 1); col.keyframe_insert("default_value", frame=f)
        ems.default_value = e; ems.keyframe_insert("default_value", frame=f)
    bump(nt, p, 0.02, 150)
    bpy.ops.object.empty_add(location=(0, 0, 0.55)); root = bpy.context.object
    a = box("ply", (0.9, 0.6, 0.05), (0, 0, 0), ply, bevel=0.003); a.parent = root
    b = box("steelsheet", (0.9, 0.6, 0.006), (0, 0, 0.17), steel); b.parent = root
    c = box("enamel", (0.9, 0.6, 0.004), (0, 0, 0.34), m); c.parent = root
    for o, z0, z1, f0, f1 in ((c, 0.34, 0.0285 + 0.005, 50, 90), (b, 0.17, 0.028, 105, 140)):
        o.location.z = z0; o.keyframe_insert("location", frame=f0)
        o.location.z = z1; o.keyframe_insert("location", frame=f1)
    c.keyframe_insert("location", frame=105); c.location.z = 0.028 + 0.005; c.keyframe_insert("location", frame=140)
    root.rotation_euler = (math.radians(18), 0, math.radians(-30)); root.keyframe_insert("rotation_euler", frame=1)
    root.rotation_euler = (math.radians(12), 0, math.radians(20)); root.keyframe_insert("rotation_euler", frame=n)
    area((-1.2, -1.0, 1.6), (0, 0, 0.55), 120, size=1.2, color=(1, 0.95, 0.9))
    area((1.4, 0.6, 1.0), (0, 0, 0.55), 70, size=1.0, color=(0.7, 0.8, 1))
    spot((0, 1.5, 1.8), (0, 0, 0.55), 150, angle=40, color=(0.9, 0.9, 1))
    camera([(0, (0.0, -2.0, 1.15), (0, 0, 0.62)), (1, (0.35, -1.55, 0.95), (0, 0, 0.6))], n, lens=40, fstop=4.0)


def shot_D4(n):
    reset(); studio(fog=0.004)
    box("wall", (6, 0.1, 3), (0, 0.06, 1.5), simple("wallg", (0.12, 0.115, 0.105), 0.9, nvar=0.1, bump_s=0.05))
    for x, kind in ((-0.56, "black_paint"), (0.56, "green")):
        bm = board_mat("cmp_" + kind, kind, "CMP")
        plane("cmp", 1.0, 0.75, (x, 0.0, 1.4), (math.radians(90), 0, 0), bm)
        for (sx, sz, dx, z) in [(1.06, 0.03, 0, 1.4 + 0.39), (1.06, 0.03, 0, 1.4 - 0.39), (0.03, 0.78, -0.515, 1.4), (0.03, 0.78, 0.515, 1.4)]:
            box("cf", (sx, 0.03, sz), (x + dx, -0.01, z), simple("cfm", (0.5, 0.5, 0.52), 0.3, metal=0.9))
    # one shared window light high-left: identical conditions for both surfaces
    area((-1.4, -2.6, 2.6), (0, 0, 1.4), 220, size=0.9, size_y=1.3, color=(1, 0.96, 0.9))
    area((1.5, -2.0, 1.0), (0, 0, 1.4), 20, size=2.0)
    camera([(0, (0.45, -4.1, 1.35), (0, 0, 1.4)), (1, (-0.2, -3.8, 1.42), (0, 0, 1.4))], n, lens=34, fstop=5.6)


def shot_D5a(n):
    reset(); world((0.02, 0.02, 0.025), fog=0.012, fog_color=(1, 0.95, 0.85))
    bd, (bw, bh, bc) = modern_room("day", "green", "SHOWA", showa=True)
    for o in bpy.data.objects:
        if o.name.startswith("lamp"): o.hide_render = True
    sun((0.8, 0.5, -0.4), 4.5, (1, 0.9, 0.75))
    area((0, -3, 3.0), (0, -3, 0), 200, size=5, color=(1, 0.92, 0.85))
    camera([(0, (3.2, -6.0, 1.55), (0.2, 1, 1.2)), (1, (1.6, -4.3, 1.45), (0, 1, 1.35))], n, lens=26, fstop=4.0)


def shot_D5b(n):
    reset(); world((0.02, 0.02, 0.025))
    bd, (bw, bh, bc) = modern_room("day", "green", "D5b", seq=n, showa=True)
    sun((0.8, 0.5, -0.4), 4.5, (1, 0.9, 0.75))
    area((0, -2, 3.0), (0, 0, 1.4), 200, size=4, color=(1, 0.92, 0.85))
    cs = chalk_stick(); animate_pen(cs, "D5b", bc, bw, bh, n)
    camera([(0, (0.15, -1.75, 1.45), (0.05, 1, 1.45)), (1, (0.05, -1.35, 1.45), (0.03, 1, 1.42))], n, lens=30, fstop=2.8)


def shot_E1(n):
    reset(); world((0.02, 0.025, 0.03))
    bd, (bw, bh, bc) = modern_room("day", "morph", sweep=[(15, 45), (75, 105)])
    sun((0.8, 0.45, -0.45), 3.0, (1, 0.95, 0.88))
    area((0, -3, 3.0), (0, -3, 0), 250, size=5)
    camera([(0, (-0.9, -3.0, 1.45), (-0.2, 1, 1.45)), (1, (0.9, -2.9, 1.45), (0.2, 1, 1.45))], n, lens=28, fstop=4.0)


def shot_E2(n):
    reset(); world((0.02, 0.025, 0.03))
    bd, (bw, bh, bc) = modern_room("day", "eboard", "EBOARD.png")
    sun((0.8, 0.45, -0.45), 3.5, (1, 0.95, 0.88))
    area((0, -3, 3.0), (0, -3, 0), 250, size=5)
    camera([(0, (0.1, -2.4, 1.5), (0, 1, 1.4)), (1, (1.8, -6.3, 2.4), (0, 0.5, 1.2))], n, lens=26, fstop=5.6)


def shot_E3(n):
    reset(); studio(fog=0.01)
    box("wall", (14, 0.1, 4), (0, 0.06, 2), simple("wallg", (0.16, 0.15, 0.14), 0.9, nvar=0.1, bump_s=0.05))
    xs = (-3.3, -1.1, 1.1, 3.3)
    for x, (kind, tex) in zip(xs, (("black_slate", "GAL_CHALK"), ("green", "GAL_CHALK"), ("white", "WHITE.png"), ("eboard", "EBOARD.png"))):
        plane("gal", 1.8, 0.54, (x, 0.0, 1.5), (math.radians(90), 0, 0), board_mat("gal_" + kind, kind, tex))
        fm = wood("gf", (0.16, 0.09, 0.04), (0.07, 0.035, 0.015)) if kind == "black_slate" else simple("gfm", (0.5, 0.5, 0.52), 0.3, metal=0.9)
        for (sx, sz, dx, z) in [(1.86, 0.03, 0, 1.5 + 0.285), (1.86, 0.03, 0, 1.5 - 0.285), (0.03, 0.57, -0.915, 1.5), (0.03, 0.57, 0.915, 1.5)]:
            box("gfr", (sx, 0.03, sz), (x + dx, -0.01, z), fm)
        spot((x, -2.4, 2.6), (x, 0, 1.45), 110, angle=34, blend=0.85, color=(1, 0.93, 0.85))
    area((0, -4, 1.5), (0, 0, 1.5), 40, size=6)
    camera([(0, (-3.6, -3.4, 1.45), (-3.2, 0, 1.5)), (1, (3.6, -3.4, 1.45), (3.2, 0, 1.5))], n, lens=32, fstop=5.6, ease=False)


def shot_F1(n):
    reset(); world((0.01, 0.01, 0.014), fog=0.015, fog_color=(1, 0.7, 0.45))
    bd, (bw, bh, bc) = modern_room("dusk", "green", "F1", seq=n)
    sun((0.9, 0.25, -0.22), 4.0, (1.0, 0.55, 0.28), angle=0.03)
    area((0, -2.5, 2.9), (0, 1, 1.4), 120, size=3, color=(1, 0.75, 0.55))
    cs = chalk_stick(); animate_pen(cs, "F1", bc, bw, bh, n)
    camera([(0, (0.7, -4.4, 1.4), (0.05, 1, 1.4)), (1, (0.0, -2.05, 1.45), (0.0, 1, 1.45))], n, lens=28, fstop=2.8)


def shot_F2(n):
    reset(); world((0.01, 0.01, 0.014), fog=0.0)
    bd, (bw, bh, bc) = modern_room("dusk", "green", "F2")
    sun((0.9, 0.25, -0.22), 4.0, (1.0, 0.55, 0.28), angle=0.03)
    area((0, -1.5, 2.6), (0, 1, 1.4), 90, size=2, color=(1, 0.75, 0.55))
    # macro over the triangle drawn in F1 (u≈0.62, v≈0.4)
    x = (0.62 - 0.5) * bw; z = bc[2] + (0.5 - 0.42) * bh
    camera([(0, (x - 0.25, 0.25, z + 0.05), (x - 0.05, 1, z)), (1, (x + 0.05, 0.55, z), (x + 0.1, 1, z - 0.02))], n, lens=40, fstop=1.6)


# ------------------------------------------------------------------ main
if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    shot = argv[0]; preview = "--preview" in argv
    n = nframes(shot)
    globals()["shot_" + shot](n)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, n
    out = os.path.join(ROOT, "assets", "frames", "shots", shot); os.makedirs(out, exist_ok=True)
    sc.render.filepath = os.path.join(out, "")
    if preview:
        sc.eevee.taa_render_samples = 8
        frames = [int(x) for x in argv[argv.index("--preview") + 1].split(",")] if len(argv) > argv.index("--preview") + 1 else [1, n // 2, n]
        for f in frames:
            sc.frame_set(f); sc.render.filepath = os.path.join(ROOT, "work", "prev", f"{shot}_{f:04d}.jpg")
            bpy.ops.render.render(write_still=True)
    else:
        sc.render.use_overwrite = False; sc.render.use_placeholder = True
        bpy.ops.render.render(animation=True)
