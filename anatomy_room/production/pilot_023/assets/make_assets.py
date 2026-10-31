#!/usr/bin/env python3
"""pilot_023 の素材を、描画で使う data の JS にまとめる（file:// では fetch も WebGL への画像も使えないため）。

- assets.js：A1 バンティングとベストが犬と写った写真（1921 年 8 月、Henry Mahon 撮影）、A2 テディ・ライダーの手紙（1923 年ごろ）。
  どちらも Thomas Fisher Rare Book Library, University of Toronto が Flickr に CC BY 2.0 で公開したもの（Wikimedia Commons、scripts/pilot_023/assets.md）
- scene_assets.js：人体の GLB（pilot_020 の make_human.py、MPFB、CC0）・Poly Haven の HDRI と質感（CC0）。pilot_022 から複製
"""
import base64
import io
import json
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
b64 = lambda b: base64.b64encode(b).decode()


def jpg(name, q=90):
    im = Image.open(HERE / name).convert("RGB")
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=q)
    return "data:image/jpeg;base64," + b64(buf.getvalue()), im.size


def main():
    dog, s1 = jpg("src_banting_best_dog.jpg")
    letter, s2 = jpg("src_teddy_letter.jpg")
    (HERE / "assets.js").write_text("window.ASSETS = " + json.dumps({"dog": dog, "letter": letter}) + ";\n", encoding="utf-8")
    s3 = {"glb": {p.stem: b64(p.read_bytes()) for p in sorted((HERE / "human").glob("*.glb"))},
          "hdr": b64((HERE / "ph" / "wooden_lounge_1k.hdr").read_bytes()),
          "tex": {p.stem: "data:image/jpeg;base64," + b64(p.read_bytes()) for p in sorted((HERE / "ph").glob("*.jpg"))}}
    (HERE / "scene_assets.js").write_text("window.ASSETS3D = " + json.dumps(s3) + ";\n", encoding="utf-8")
    print("dog", s1, "letter", s2, "glb", len(s3["glb"]))


if __name__ == "__main__":
    main()
