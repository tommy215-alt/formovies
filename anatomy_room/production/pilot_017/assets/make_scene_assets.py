#!/usr/bin/env python3
"""pilot_017：3D の素材（MPFB の人体 GLB・Poly Haven の HDRI と木の質感、どれも CC0）を、描画で使う data の JS にまとめる。

file:// では fetch も WebGL への画像も使えないので、base64 にして window.ASSETS3D に入れる。
  glb：human/*.glb（make_human.py）／hdr：ph/wooden_lounge_1k.hdr／tex：ph/*_{Diffuse,nor_gl,Rough}.jpg
"""
import base64
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
b64 = lambda p: base64.b64encode(p.read_bytes()).decode()
out = {"glb": {p.stem: b64(p) for p in sorted((HERE / "human").glob("*.glb"))},
       "hdr": b64(HERE / "ph" / "wooden_lounge_1k.hdr"),
       "tex": {p.stem: "data:image/jpeg;base64," + b64(p) for p in sorted((HERE / "ph").glob("*.jpg")) if "tonemapped" not in p.name}}
(HERE / "scene_assets.js").write_text("window.ASSETS3D = " + json.dumps(out) + ";\n", encoding="utf-8")
print({k: (len(v) if isinstance(v, str) else {kk: len(vv) for kk, vv in v.items()}) for k, v in out.items()})
