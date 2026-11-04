#!/usr/bin/env python3
"""リバースの制作の土台（kit、2026-11-01〜）：素材を描画で使う data の JS にまとめる（file:// では fetch も WebGL への画像も使えないため）。

- 共通の 3D 素材（人体の GLB〔MPFB、CC0〕・Poly Haven の HDRI と質感〔CC0〕）は 1 回だけ作り、全部の回で使い回す：
    python anatomy_room/production/ext/kit/make_assets.py shared      → ext/kit/scene_assets.js
  元のファイルは production/pilot_021/assets/{human,ph}（pilot_020 の make_human.py で作ったもの）。
- 各回の素材（本物の写真＋派手な文字のフォントを使う文字だけに絞ったもの）は、各回の assets/make_assets.py から episode() を呼ぶ：
    kit.episode(HERE, {"photo": ("src_x.jpg", "L"), ...})          → <回>/assets/assets.js
  フォント（Dela Gothic One・Mochiy Pop One・Shippori Mincho、OFL）の元は production/pilot_021/assets/fonts。
  renderer.html の画面の文字や lines.json を変えたら、もう一度実行する（フォントに文字を入れ直すため）。
"""
import base64
import io
import json
import string
import sys
from pathlib import Path

from PIL import Image

KIT = Path(__file__).resolve().parent
SRC = KIT.parent.parent / "pilot_021" / "assets"
b64 = lambda b: base64.b64encode(b).decode()
FONTS = [("dela", "delagothicone_DelaGothicOne-Regular.ttf"), ("mochiy", "mochiypopone_MochiyPopOne-Regular.ttf"),
         ("mincho", "shipporimincho_ShipporiMincho-SemiBold.ttf")]


def fit(im, n):
    s = n / max(im.size)
    return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS) if s < 1 else im


def font_subset(path, chars):
    from fontTools import subset
    opt = subset.Options(); opt.layout_features = ["*"]; opt.name_IDs = ["*"]; opt.notdef_outline = True
    f = subset.load_font(str(path), opt); s = subset.Subsetter(opt); s.populate(text=chars); s.subset(f)
    out = io.BytesIO(); f.save(out); return out.getvalue()


def episode(here, photos, size=1800, fonts=True):
    """photos：{キー: (ファイル名, "L"〔白黒〕か "RGB")}。here は <回>/assets"""
    here = Path(here); ep = here.parent; out = {}
    for k, (f, mode) in photos.items():
        buf = io.BytesIO(); fit(Image.open(here / f).convert(mode), size).save(buf, "JPEG", quality=90)
        out[k] = "data:image/jpeg;base64," + b64(buf.getvalue())
    if fonts:
        lines = json.loads((ep / "lines.json").read_text(encoding="utf-8"))
        subs = lambda x: x.get("sub") if isinstance(x.get("sub"), str) else "".join(x.get("sub") or [])
        chars = set("".join(subs(x) + x["speech"] for x in lines["lines"]))
        chars |= set((ep / "renderer.html").read_text(encoding="utf-8")) | set((KIT / "kit.js").read_text(encoding="utf-8"))
        kana = "".join(chr(c) for c in range(0x3041, 0x3097)) + "".join(chr(c) for c in range(0x30A1, 0x30FB)) + "ー・「」『』（）！？。、…〜"
        chars |= set(string.printable) | set(kana) | set("０１２３４５６７８９")
        text = "".join(sorted(c for c in chars if not c.isspace() or c == " "))
        for k, f in FONTS:
            out["font_" + k] = b64(font_subset(SRC / "fonts" / f, text))
    (here / "assets.js").write_text("window.ASSETS = " + json.dumps(out) + ";\n", encoding="utf-8")
    print({k: len(v) for k, v in out.items()})


def add_font(here, key, file, chars):
    """assets.js にフォントを 1 つ足す（使う文字だけ）。2026-11-04〜：選択設計の札の字体 Yuji Syuku（OFL）"""
    here = Path(here); p = here / "assets.js"; s = p.read_text(encoding="utf-8")
    out = json.loads(s[len("window.ASSETS = "):].rstrip().rstrip(";"))
    kana = "".join(chr(c) for c in range(0x3041, 0x3097)) + "".join(chr(c) for c in range(0x30A1, 0x30FB)) + "ー・「」『』（）！？。、…〜／"
    text = "".join(sorted(set(chars) | set(kana) | set(string.ascii_letters + string.digits)))
    out["font_" + key] = b64(font_subset(SRC / "fonts" / file, text))
    p.write_text("window.ASSETS = " + json.dumps(out) + ";\n", encoding="utf-8"); print("font", key, len(out["font_" + key]))


def shared():
    s3 = {"glb": {p.stem: b64(p.read_bytes()) for p in sorted((SRC / "human").glob("*.glb"))},
          "hdr": b64((SRC / "ph" / "wooden_lounge_1k.hdr").read_bytes()),
          "tex": {p.stem: "data:image/jpeg;base64," + b64(p.read_bytes()) for p in sorted((SRC / "ph").glob("*.jpg"))}}
    (KIT / "scene_assets.js").write_text("window.ASSETS3D = " + json.dumps(s3) + ";\n", encoding="utf-8")
    print("glb", sorted(s3["glb"]), "tex", len(s3["tex"]))


if __name__ == "__main__":
    if sys.argv[1:] == ["shared"]:
        shared()
