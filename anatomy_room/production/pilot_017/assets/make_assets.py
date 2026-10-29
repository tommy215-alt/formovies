#!/usr/bin/env python3
"""pilot_017 の本物の写真・図（scripts/pilot_017/assets.md）を、描画で使う形にする。

- A1 肖像（Commons、パブリックドメイン）→ portrait.jpg（長辺 1600）
- A2 HCO Circular 173（1912）の 3 ページ目 Fig. 2 → fig2.png（ADS のスキャンの PDF から切り出し）
- A3 ESA/Hubble heic1502a（CC BY 4.0）→ m31.jpg（長辺 2400）
- assets.js：file:// の画像は WebGL に渡せないので data URI にまとめる
使い方：python make_assets.py <Circular 173 の PDF>
"""
import base64
import io
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent


def fit(im, n):
    s = n / max(im.size)
    return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS) if s < 1 else im


def main(pdf):
    import pypdfium2 as pdfium
    page = pdfium.PdfDocument(pdf)[2].render(scale=5).to_pil().convert("L")
    w, h = page.size
    # Fig. 2 は 3 ページ目の右側の図（ページ幅の 0.53〜0.82、高さの 0.18〜0.42 あたり）。枠の内側だけを残す
    fig = page.crop((int(w * .525), int(h * .178), int(w * .823), int(h * .418)))
    fig.save(HERE / "fig2.png")
    fit(Image.open(HERE / "src_leavitt.jpg").convert("L"), 1600).save(HERE / "portrait.jpg", quality=90)
    fit(Image.open(HERE / "src_heic1502a.jpg").convert("RGB"), 2400).save(HERE / "m31.jpg", quality=88)
    out = {}
    for k, f, mime in [("portrait", "portrait.jpg", "jpeg"), ("fig2", "fig2.png", "png"), ("m31", "m31.jpg", "jpeg")]:
        out[k] = f"data:image/{mime};base64," + base64.b64encode((HERE / f).read_bytes()).decode()
    (HERE / "assets.js").write_text("window.ASSETS = " + json.dumps(out) + ";\n", encoding="utf-8")
    print({k: len(v) for k, v in out.items()})


if __name__ == "__main__":
    main(sys.argv[1])
