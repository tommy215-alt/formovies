"""pilot_051 の群れの猫（数千〜3.7 万匹）。毛の曲線は付けない（遠くの猫）、手前の数匹は cat.py の毛のある猫を使う。
軽くする工夫（2026-11-12、メモリ feedback-time-budget）：
  1. 柄 × 姿勢 × 歩きのコマを、それぞれ 1 つの形（メッシュ）に固めて work/patches.blend に保存（bake_poses）。
  2. 群れは 1 つの点の集まり。点ごとに「どの形か（fi）・向き（rot）・大きさ（sc）」を持たせ、ジオメトリノードで形を置く（Crowd）。
     毎コマ変わるのは点の位置と属性だけ。Cycles に渡すのは猫の数の分の instance（数万）で、草や石のように数百万にはならない。"""
from common import *
import cat, track

COATS = ["mike", "chatora", "kuro", "shiro", "sabatora", "hachiware"]


def _join_eval(objs, name):
    """姿勢をつけた部品（メッシュ）を、世界座標で 1 つのメッシュにまとめる（材質も引き継ぐ）"""
    dg = bpy.context.evaluated_depsgraph_get(); bm = bmesh.new(); mats = []
    for o in objs:
        oe = o.evaluated_get(dg); me = oe.to_mesh(); tmp = bmesh.new(); tmp.from_mesh(me); tmp.transform(o.matrix_world)
        base = len(mats); mats += [s_.material for s_ in o.material_slots]
        for f in tmp.faces:
            f.material_index += base
        m2 = bpy.data.meshes.new("_tmp"); tmp.to_mesh(m2); tmp.free(); bm.from_mesh(m2); bpy.data.meshes.remove(m2); oe.to_mesh_clear()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    return bpy.data.objects.new(name, me)


def bake_poses(coat, mode="walk", n=8, seed=1):
    """柄 coat の猫を mode で n コマ分、1 つずつの形にする（毛なし）。キャッシュがあれば読むだけ"""
    names = [f"cc_{coat}_{mode}_{k}" for k in range(n)]; c_ = track.cached(names)
    if c_:
        return c_
    c = cat.build_cat(f"tmp_{coat}", coat, seed, fur=False)
    parts = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(f"tmp_{coat}") and not o.hide_render]
    out = []
    for k in range(n):
        cat.cpose(c, pos=(0, 0), heading=0.0, mode=mode, t=k / n * 1.6, ph=k / n); bpy.context.view_layer.update()
        o = _join_eval(parts, names[k]); track._patch_col().objects.link(o); out.append(o)
    for o in [o for o in bpy.data.objects if o.name.startswith(f"tmp_{coat}")]:
        bpy.data.objects.remove(o, do_unlink=True)
    track.save_cache(); log("bake_poses", coat, mode, n); return out


def frames_collection(name, objs):
    col = bpy.data.collections.new(name); sc.collection.children.link(col)
    for o in objs:
        col.objects.link(o)
    bpy.context.view_layer.layer_collection.children[col.name].exclude = True
    return col


class Crowd:
    """N 匹の群れ。update(t) で pos_fn(t) → (位置 N×3, 向き N, 形の番号 N) を受け取り、点を動かす"""
    def __init__(self, name, frames, pos_fn, scale=None, seed=1):
        self.fn = pos_fn; self.col = frames_collection(name + "_frames", frames)
        P, R, F = pos_fn(0.0); N = len(P); self.N = N
        me = bpy.data.meshes.new(name); me.from_pydata(np.asarray(P).tolist(), [], []); me.update()
        me.attributes.new("rot", "FLOAT", "POINT"); me.attributes.new("fi", "INT", "POINT"); me.attributes.new("sc", "FLOAT", "POINT")
        s = np.asarray(scale if scale is not None else np.random.default_rng(seed).uniform(.88, 1.1, N), np.float32); me.attributes["sc"].data.foreach_set("value", s)
        self.me = me; self.o = link(bpy.data.objects.new(name, me))
        ng = bpy.data.node_groups.new(name + "_gn", "GeometryNodeTree"); Nn = ng.nodes; L = ng.links
        ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry"); ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        gi = Nn.new("NodeGroupInput"); go = Nn.new("NodeGroupOutput"); mp = Nn.new("GeometryNodeMeshToPoints")
        ci = Nn.new("GeometryNodeCollectionInfo"); ci.inputs["Collection"].default_value = self.col; ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
        ip = Nn.new("GeometryNodeInstanceOnPoints"); ip.inputs["Pick Instance"].default_value = True

        def attr(nm, typ):
            a = Nn.new("GeometryNodeInputNamedAttribute"); a.data_type = typ; a.inputs["Name"].default_value = nm
            return next(o for o in a.outputs if o.enabled and o.name == "Attribute")
        cx = Nn.new("ShaderNodeCombineXYZ"); L.new(attr("rot", "FLOAT"), cx.inputs["Z"])
        L.new(gi.outputs[0], mp.inputs["Mesh"]); L.new(mp.outputs["Points"], ip.inputs["Points"]); L.new(ci.outputs[0], ip.inputs["Instance"])
        L.new(attr("fi", "INT"), ip.inputs["Instance Index"]); L.new(cx.outputs[0], ip.inputs["Rotation"]); L.new(attr("sc", "FLOAT"), ip.inputs["Scale"]); L.new(ip.outputs[0], go.inputs[0])
        self.o.modifiers.new("gn", "NODES").node_group = ng
        DYN.append(self.update); self.update(0.0)

    def update(self, t):
        P, R, F = self.fn(t)
        self.me.vertices.foreach_set("co", np.asarray(P, np.float32).ravel())
        self.me.attributes["rot"].data.foreach_set("value", np.asarray(R, np.float32)); self.me.attributes["fi"].data.foreach_set("value", np.asarray(F, np.int32))
        self.me.update()


def walk_frames(coats=COATS, n=8, mode="walk"):
    """全部の柄の歩きのコマ。返り値：形の一覧と、柄 i・コマ k → 番号（i*n + k）"""
    out = []
    for i, c in enumerate(coats):
        out += bake_poses(c, mode, n, seed=11 + i)
    return out
