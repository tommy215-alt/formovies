#!/usr/bin/env python3
"""pilot_015「太陽は何でできているか——セシリア・ペイン」（チャンネル「リバース」標準ルール v5・ガイドライン v2.1＋ pilot_015 の修正事項）の制作スクリプト。

処理の本体は production/common/pipeline.py、標準の既定値は production/common/standard.py。
いまは台本の段階（尺の実測だけ）。演出（効果音・BGM・場面）は、ユーザーが台本を OK してから書く。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
import pipeline  # noqa: E402
import standard  # noqa: E402

EP = standard.config({
    "id": "pilot_015",
    "out": "reverse_015_cecilia_payne.mp4",
    # 場面の区切り（renderer.html と同じ名前）。演出のきっかけは台本の OK のあとに足す
    "cues": {"hook": ("L01", 0.0), "cambridge": ("L02", 0.0), "harvard": ("L06", 0.0), "method": ("L07", 0.0),
             "result": ("L11", 0.0), "letter": ("L14", 0.0), "after": ("L18", 0.0), "today": ("L21", 0.0)},
    "sfx": [],
    "segments": ["hook", "cambridge", "harvard", "method", "result", "letter", "after", "today"],
    "workers": 2,
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
