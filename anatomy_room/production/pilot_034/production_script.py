#!/usr/bin/env python3
"""pilot_034「雪の結晶を写した農夫——ウィルソン・ベントレー」（チャンネル「リバース」知的設計（templates/DESIGN_MODES.md の「知的設計の編集設定」、カットインは文字・効果音なしのカメラの動き）＋ガイドライン v2.4）の制作スクリプト。

台本は scripts/pilot_034/script_draft.md（2026-11-01 にユーザーが「OK」）、事実は fact_check.md、画像と曲は assets.md。
BGM は Kevin MacLeod「Evening」（incompetech、CC BY 4.0）。制作の土台は production/ext/kit（epkit・kit.js・shots.js）。
起承転結のカットイン：L03・L05・L09・L11。このファイルは 10 本同時の制作で台本から作った（cues は行ごとに l01・l01m〔0.5 秒後〕など）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ext" / "kit"))
import epkit  # noqa: E402

pipeline, standard = epkit.setup(HERE, "intel", bgm=("Evening.mp3", 101))

EP = standard.config({
    "id": "pilot_034",
    "out": "reverse_034_bentley.mp4",
    "cues": {"open": ["L00", 0.0], "hook": ["L01", 0.0], "ki": ["L03", 0.0], "sho": ["L05", 0.0], "ten": ["L09", 0.0], "ketsu": ["L11", 0.0], "l00": ["L00", 0.0], "l00m": ["L00", 0.5], "l01": ["L01", 0.0], "l01m": ["L01", 0.5], "l02": ["L02", 0.0], "l02m": ["L02", 0.5], "l03": ["L03", 0.0], "l03m": ["L03", 0.5], "l04": ["L04", 0.0], "l04m": ["L04", 0.5], "l05": ["L05", 0.0], "l05m": ["L05", 0.5], "l06": ["L06", 0.0], "l06m": ["L06", 0.5], "l06b": ["L06b", 0.0], "l06bm": ["L06b", 0.5], "l07": ["L07", 0.0], "l07m": ["L07", 0.5], "l08": ["L08", 0.0], "l08m": ["L08", 0.5], "l09": ["L09", 0.0], "l09m": ["L09", 0.5], "l10": ["L10", 0.0], "l10m": ["L10", 0.5], "l11": ["L11", 0.0], "l11m": ["L11", 0.5], "l11b": ["L11b", 0.0], "l11bm": ["L11b", 0.5], "l12": ["L12", 0.0], "l12m": ["L12", 0.5]},
    "sfx": [["title", "hook", 0.6, 0.02], ["whoosh", "hook", 0.4, 0.1], ["scan", "l01", 0.32, 0.15], ["data", "l02", 0.32, 0.15], ["shimmer", "l04", 0.32, 0.15], ["scan", "l06", 0.32, 0.15], ["data", "l06b", 0.32, 0.15], ["tick", "l07", 0.32, 0.15], ["shimmer", "l08", 0.32, 0.15], ["scan", "l10", 0.32, 0.15], ["tick", "l11b", 0.32, 0.15], ["shimmer", "l12", 0.32, 0.15], ["glow", "l12", 0.4, 0.2]],
    "music": {"style": "file_034", "sections": [["t0", 0.0, "open_impact"], ["hook", -0.05, "f_full"], ["l03", -0.5, "w_hold"], ["l03", 0.0, "f_full"], ["l05", -0.5, "w_hold"], ["l05", 0.0, "f_full"], ["l09", -0.5, "w_hold"], ["l09", 0.0, "f_full"], ["l11", -0.5, "w_hold"], ["l11", 0.0, "f_full"], ["end1", -0.6, "ending"]]},
    "segments": ["open", "hook", "ki", "sho", "ten", "ketsu"],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 2.0], ["l01", 0.6], ["l02", 0.6], ["l03", 0.6], ["l04", 0.6], ["l05", 0.6], ["l06", 0.6], ["l06b", 0.6], ["l07", 0.6], ["l08", 0.6], ["l09", 0.6], ["l10", 0.6], ["l11", 0.6], ["l11b", 0.6], ["l12", 0.6]],
    "scenes": [('0 open', None, 'hook', '', ''), ('1 hook', 'hook', 'ki', '', ''), ('2 ki', 'ki', 'sho', '', ''), ('3 sho', 'sho', 'ten', '', ''), ('4 ten', 'ten', 'ketsu', '', ''), ('5 ketsu', 'ketsu', 'endcard', '', ''), ('6 共通エンディング（短い版）', 'endcard', None, '', '')],
    "plan_notes": ["## 演出の方針", "", "- 設計：知的設計（templates/DESIGN_MODES.md の「知的設計の編集設定」、カットインは文字・効果音なしのカメラの動き）。", "- 画面の構成は renderer.html の SHOTS（セリフごとのショットの一覧）。", "- 人物は MPFB の人体の後ろ姿・遠景（顔なし、手のアップなし）。本物の画像は assets.md の権利の確かなものだけ。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
