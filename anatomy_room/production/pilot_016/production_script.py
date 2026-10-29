#!/usr/bin/env python3
"""pilot_016「大陸は動いている——アルフレート・ヴェーゲナー」（チャンネル「リバース」標準ルール v6・ガイドライン v2.2）の制作スクリプト。

処理の本体は production/common/pipeline.py、標準の既定値は production/common/standard.py、外付けの部品は production/ext/。
いまは台本の段階（尺の実測だけ）。演出（効果音・BGM・場面）は、ユーザーが台本を OK してから書く。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
sys.path.insert(0, str(HERE.parent / "ext"))
import pipeline  # noqa: E402
import standard  # noqa: E402
import music_ext  # noqa: E402,F401

EP = standard.config({
    "id": "pilot_016",
    "out": "reverse_016_wegener.mp4",
    "cues": {"hook": ("L01", 0.0), "announce": ("L02", 0.0), "evidence": ("L04", 0.0), "wall": ("L07", 0.0),
             "ice": ("L11", 0.0), "sea": ("L13", 0.0), "today": ("L16", 0.0)},
    "sfx": [],
    "music": {"style": "warm_drive", "sections": [("t0", 0.0, "w_hook"), ("end1", -0.6, "ending")]},
    "segments": ["hook", "announce", "evidence", "wall", "ice", "sea", "today"],
    "workers": 2,
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
