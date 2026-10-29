#!/usr/bin/env python3
"""pilot_018 の素材を、描画で使う data の JS にまとめる（file:// では fetch も WebGL への画像も使えないため）。

- assets.js：A1 パスツールの肖像（Commons、パブリックドメイン）・A2 1885 年の版画（Wellcome、Public Domain Mark）、
  派手な文字のフォント（Dela Gothic One・Mochiy Pop One、OFL）を、台本と renderer.html に出てくる文字だけに絞ったもの
- scene_assets.js：人体の GLB（make_human.py、CC0）・Poly Haven の HDRI と質感（CC0）
renderer.html の画面の文字を変えたら、もう一度実行する（フォントに文字を入れ直すため）。
"""
import base64
import io
import json
import string
from pathlib import Path

from PIL import Image
from fontTools import subset

HERE = Path(__file__).resolve().parent
EP = HERE.parent
b64 = lambda b: base64.b64encode(b).decode()


def fit(im, n):
    s = n / max(im.size)
    return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS) if s < 1 else im


def font_subset(path, chars):
    opt = subset.Options(); opt.layout_features = ["*"]; opt.name_IDs = ["*"]; opt.notdef_outline = True
    f = subset.load_font(str(path), opt); s = subset.Subsetter(opt); s.populate(text=chars); s.subset(f)
    out = io.BytesIO(); f.save(out); return out.getvalue()


def main():
    out = {}
    buf = io.BytesIO(); fit(Image.open(HERE / "src_pasteur.jpg").convert("L"), 1600).save(buf, "JPEG", quality=90); out["portrait"] = "data:image/jpeg;base64," + b64(buf.getvalue())
    buf = io.BytesIO(); fit(Image.open(HERE / "src_rabbit.jpg").convert("RGB"), 1600).save(buf, "JPEG", quality=90); out["rabbit"] = "data:image/jpeg;base64," + b64(buf.getvalue())
    lines = json.loads((EP / "lines.json").read_text(encoding="utf-8"))
    chars = set("".join("".join(x["sub"]) + x["speech"] for x in lines["lines"]))
    chars |= set((EP / "renderer.html").read_text(encoding="utf-8"))
    kana = "".join(chr(c) for c in range(0x3041, 0x3097)) + "".join(chr(c) for c in range(0x30A1, 0x30FB)) + "ー・「」『』（）！？。、…〜"
    chars |= set(string.printable) | set(kana) | set("０１２３４５６７８９")
    text = "".join(sorted(c for c in chars if not c.isspace() or c == " "))
    for k, f in [("dela", "delagothicone_DelaGothicOne-Regular.ttf"), ("mochiy", "mochiypopone_MochiyPopOne-Regular.ttf")]:
        out["font_" + k] = b64(font_subset(HERE / "fonts" / f, text))
    (HERE / "assets.js").write_text("window.ASSETS = " + json.dumps(out) + ";\n", encoding="utf-8")
    s3 = {"glb": {p.stem: b64(p.read_bytes()) for p in sorted((HERE / "human").glob("*.glb"))},
          "hdr": b64((HERE / "ph" / "wooden_lounge_1k.hdr").read_bytes()),
          "tex": {p.stem: "data:image/jpeg;base64," + b64(p.read_bytes()) for p in sorted((HERE / "ph").glob("*.jpg"))}}
    (HERE / "scene_assets.js").write_text("window.ASSETS3D = " + json.dumps(s3) + ";\n", encoding="utf-8")
    print({k: len(v) for k, v in out.items()}, "glb", len(s3["glb"]))


if __name__ == "__main__":
    main()
