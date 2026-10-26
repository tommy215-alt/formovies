#!/usr/bin/env python3
"""pilot_007 で使う本物の QR コードを作り、消し方ごとに「読めるか」を実際に試して qr_demo.json に保存する。

動画の「読み取り成功／読めない」の表示は、ここで OpenCV（cv2.QRCodeDetector）が実際に読めたかどうかだけを使う。
読み取りの結果は、読み取り機・印刷・撮影の条件でも変わる（ここで試したのは画面上の理想的な画像と 1 種類の読み取り機）。

準備（無料・一度だけ）：pip install --target <作業用フォルダ>/pylib qrcode opencv-python-headless
実行：PYLIB=<作業用フォルダ>/pylib python3 qr_demo.py
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.environ.get("PYLIB", "pylib"))
import cv2  # noqa: E402
import numpy as np  # noqa: E402
import qrcode  # noqa: E402

TEXT = "REVERSE"
HERE = Path(__file__).resolve().parent


def make(level):
    q = qrcode.QRCode(error_correction=level, border=0, box_size=1, version=None)
    q.add_data(TEXT)
    q.make(fit=True)
    return np.array(q.get_matrix(), dtype=np.uint8), q.version


def decode(m):
    n = m.shape[0]
    a = np.full((n + 8, n + 8), 255, np.uint8)
    a[4:4 + n, 4:4 + n] = np.where(m == 1, 0, 255)
    img = cv2.resize(a, None, fx=12, fy=12, interpolation=cv2.INTER_NEAREST)
    s, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
    return s


def erase(m, rects):
    e = m.copy()
    for r0, c0, h, w in rects:
        e[r0:r0 + h, c0:c0 + w] = 0
    return e


H, vh = make(qrcode.constants.ERROR_CORRECT_H)
L, vl = make(qrcode.constants.ERROR_CORRECT_L)
n = H.shape[0]
RECTS = {
    "arm": [[10, 9, 7, 8]],             # オモテが最初に消すところ（ドット絵の左腕に対応）
    "small": [[12, 12, 5, 5]],          # 小さな欠け
    "logo": [[8, 8, 5, 5]],             # 真ん中のロゴ
    "finder": [[0, 0, 8, 8]],           # 左上の位置検出パターン（と周りの余白）
    "big": [[8, 8, 10, 10]],            # 大きな欠け
}
tests = {}
for code_name, m in (("H", H), ("L", L)):
    tests[code_name] = {"clean": decode(m)}
    for k, rects in RECTS.items():
        tests[code_name][k] = decode(erase(m, rects))
out = {"text": TEXT, "size": n, "version": {"H": vh, "L": vl},
       "matrix": {"H": H.tolist(), "L": L.tolist()}, "rects": RECTS,
       "area_percent": {k: round(100 * sum(h * w for _, _, h, w in r) / n / n, 1) for k, r in RECTS.items()},
       "decoded": tests, "decoder": f"OpenCV {cv2.__version__} QRCodeDetector", "qrcode_lib": "qrcode 8.2"}
(HERE / "qr_demo.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
# renderer.html から読み込む用（file:// でも読めるよう、JS の変数として書く）
(HERE / "qr_demo.js").write_text("// qr_demo.py が生成（手で編集しない）\nwindow.QR = " + json.dumps(out, ensure_ascii=False) + ";\n", encoding="utf-8")
for c in tests:
    print(c, {k: (v or "（読めない）") for k, v in tests[c].items()})
print("面積の割合:", out["area_percent"])
