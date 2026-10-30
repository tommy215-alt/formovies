#!/usr/bin/env python3
"""pilot_022 の素材を、描画で使う data の JS にまとめる（file:// では fetch も WebGL への画像も使えないため）。

- assets.js：A1 ピロリ菌（ヘリコバクター）のコロニーの走査電子顕微鏡写真（David Gregory & Debbie Marshall、Wellcome Collection、CC BY 4.0。下の目盛りの帯を切り落とす。
  2026-10-30 の直しでオープニングからは外した：グロテスク）、A2 グレイ解剖学の胃の図（H. V. Carter、1918 年版 Fig. 1046、Commons の SVG、パブリックドメイン。英語の注記は外す。
  2 回目の直しで使わなくなった）、A3 マーシャルが飲んだ培養液の瓶（ノーベル博物館、Gaius Cornelius、Commons、CC BY 4.0。オープニングの中央）
- scene_assets.js：人体の GLB（pilot_020 の make_human.py、MPFB、CC0）・Poly Haven の HDRI と質感（CC0）
"""
import base64
import io
import json
import re
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
b64 = lambda b: base64.b64encode(b).decode()


def main():
    im = Image.open(HERE / "src_hpylori_sem.jpg").convert("RGB")
    im = im.crop((0, 0, im.width, int(im.height * .925)))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=90)
    jar = Image.open(HERE / "src_marshall_jar.jpg").convert("RGB"); jar.thumbnail((900, 1680)); jb = io.BytesIO(); jar.save(jb, "JPEG", quality=88)
    svg = (HERE / "src_gray1046.svg").read_text(encoding="utf-8")
    svg = re.sub(r"<text[\s\S]*?</text>", "", svg)   # 英語の注記を外す（線画だけ）
    (HERE / "assets.js").write_text("window.ASSETS = " + json.dumps({"sem": "data:image/jpeg;base64," + b64(buf.getvalue()), "gray": "data:image/svg+xml;base64," + b64(svg.encode("utf-8")), "jar": "data:image/jpeg;base64," + b64(jb.getvalue())}) + ";\n", encoding="utf-8")
    s3 = {"glb": {p.stem: b64(p.read_bytes()) for p in sorted((HERE / "human").glob("*.glb"))},
          "hdr": b64((HERE / "ph" / "wooden_lounge_1k.hdr").read_bytes()),
          "tex": {p.stem: "data:image/jpeg;base64," + b64(p.read_bytes()) for p in sorted((HERE / "ph").glob("*.jpg"))}}
    (HERE / "scene_assets.js").write_text("window.ASSETS3D = " + json.dumps(s3) + ";\n", encoding="utf-8")
    print("sem", im.size, "glb", len(s3["glb"]))


if __name__ == "__main__":
    main()
