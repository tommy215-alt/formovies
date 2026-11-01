#!/usr/bin/env python3
"""pilot_035「高度31キロから飛び降りた男——ジョー・キッティンジャー」（チャンネル「リバース」ドパ設計（閃光なし、カットインは文字なし・効果音たっぷり、叫ぶ声は style=shout の行だけ青山龍星「熱血」）＋ガイドライン v2.4）の制作スクリプト。

台本は scripts/pilot_035/script_draft.md（2026-11-01 にユーザーが「OK」）、事実は fact_check.md、画像と曲は assets.md。
BGM は Kevin MacLeod「Cyborg Ninja」（incompetech、CC BY 4.0）。制作の土台は production/ext/kit（epkit・kit.js・shots.js）。
起承転結のカットイン：L04・L06・L09・L11。このファイルは 10 本同時の制作で台本から作った（cues は行ごとに l01・l01m〔0.5 秒後〕など）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ext" / "kit"))
import epkit  # noqa: E402

pipeline, standard = epkit.setup(HERE, "dopa", bgm=("Cyborg Ninja.mp3", 160))

EP = standard.config({
    "id": "pilot_035",
    "out": "reverse_035_kittinger.mp4",
    "cues": {"open": ["L00", 0.0], "hook": ["L01", 0.0], "ki": ["L04", 0.0], "sho": ["L06", 0.0], "ten": ["L09", 0.0], "ketsu": ["L11", 0.0], "l00": ["L00", 0.0], "l00m": ["L00", 0.5], "l01": ["L01", 0.0], "l01m": ["L01", 0.5], "l02": ["L02", 0.0], "l02m": ["L02", 0.5], "l03": ["L03", 0.0], "l03m": ["L03", 0.5], "l03b": ["L03b", 0.0], "l03bm": ["L03b", 0.5], "l04": ["L04", 0.0], "l04m": ["L04", 0.5], "l05": ["L05", 0.0], "l05m": ["L05", 0.5], "l06": ["L06", 0.0], "l06m": ["L06", 0.5], "l07": ["L07", 0.0], "l07m": ["L07", 0.5], "l08": ["L08", 0.0], "l08m": ["L08", 0.5], "l08b": ["L08b", 0.0], "l08bm": ["L08b", 0.5], "l09": ["L09", 0.0], "l09m": ["L09", 0.5], "l10": ["L10", 0.0], "l10m": ["L10", 0.5], "l11": ["L11", 0.0], "l11m": ["L11", 0.5], "l12": ["L12", 0.0], "l12m": ["L12", 0.5], "l13": ["L13", 0.0], "l13m": ["L13", 0.5]},
    "sfx": [["deep", "t0", 0.5, 0.05], ["impact", "hook", 1.0], ["hit", "hook", 0.8, 0.02], ["stamp", "hook", 0.7, 0.1], ["impact", "l02", 0.75, 0.05], ["hit", "l02", 0.6, 0.45], ["stamp", "l03", 0.75, 0.05], ["zoom", "l03", 0.6, 0.45], ["whoosh", "l03b", 0.75, 0.05], ["tagpop", "l03b", 0.6, 0.45], ["impact", "l04", 1.0], ["hit", "l04", 0.8, 0.02], ["deep", "l04", 0.7, 0.03], ["whoosh", "l04", 0.7, 0.05], ["zoom", "l04", 0.6, 0.3], ["stamp", "l04", 0.6, 0.42], ["zoom", "l05", 0.75, 0.05], ["prism", "l05", 0.6, 0.45], ["impact", "l06", 1.0], ["hit", "l06", 0.8, 0.02], ["deep", "l06", 0.7, 0.03], ["whoosh", "l06", 0.7, 0.05], ["zoom", "l06", 0.6, 0.3], ["stamp", "l06", 0.6, 0.42], ["riser", "l07", 0.75, 0.05], ["stamp", "l07", 0.6, 0.45], ["prism", "l08", 0.75, 0.05], ["whoosh", "l08", 0.6, 0.45], ["impact", "l08b", 0.75, 0.05], ["hit", "l08b", 0.6, 0.45], ["impact", "l09", 1.0], ["hit", "l09", 0.8, 0.02], ["deep", "l09", 0.7, 0.03], ["whoosh", "l09", 0.7, 0.05], ["zoom", "l09", 0.6, 0.3], ["stamp", "l09", 0.6, 0.42], ["impact", "l09", 0.9, 0.45], ["hit", "l09", 0.7, 0.47], ["glitch", "l09", 0.5, 0.46], ["impact", "l09", 1.0, 0.95], ["deep", "l09", 0.8, 0.96], ["whoosh", "l09", 0.7, 0.97], ["hit", "l09", 0.9, 1.5], ["whoosh", "l10", 0.75, 0.05], ["tagpop", "l10", 0.6, 0.45], ["impact", "l11", 1.0], ["hit", "l11", 0.8, 0.02], ["deep", "l11", 0.7, 0.03], ["whoosh", "l11", 0.7, 0.05], ["zoom", "l11", 0.6, 0.3], ["stamp", "l11", 0.6, 0.42], ["zoom", "l12", 0.75, 0.05], ["prism", "l12", 0.6, 0.45], ["tagpop", "l13", 0.75, 0.05], ["impact", "l13", 0.6, 0.45], ["shimmer", "l13", 0.45, 0.8], ["discover", "l13", 0.4, 0.9]],
    "music": {"style": "file_035", "sections": [["t0", 0.0, "open_impact"], ["hook", -0.05, "f_full"], ["l04", -0.35, "w_hold"], ["l04", 0.0, "f_full"], ["l06", -0.35, "w_hold"], ["l06", 0.0, "f_full"], ["l09", -0.35, "w_hold"], ["l09", 0.0, "f_full"], ["l11", -0.35, "w_hold"], ["l11", 0.0, "f_full"], ["end1", -0.6, "ending"]]},
    "segments": ["open", "hook", "ki", "sho", "ten", "ketsu"],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 2.0], ["l01", 0.6], ["l02", 0.6], ["l03", 0.6], ["l03b", 0.6], ["l04", 0.6], ["l05", 0.6], ["l06", 0.6], ["l07", 0.6], ["l08", 0.6], ["l08b", 0.6], ["l09", 0.6], ["l10", 0.6], ["l11", 0.6], ["l12", 0.6], ["l13", 0.6]],
    "scenes": [('0 open', None, 'hook', '', ''), ('1 hook', 'hook', 'ki', '', ''), ('2 ki', 'ki', 'sho', '', ''), ('3 sho', 'sho', 'ten', '', ''), ('4 ten', 'ten', 'ketsu', '', ''), ('5 ketsu', 'ketsu', 'endcard', '', ''), ('6 共通エンディング（短い版）', 'endcard', None, '', '')],
    "plan_notes": ["## 演出の方針", "", "- 設計：ドパ設計（閃光なし、カットインは文字なし・効果音たっぷり、叫ぶ声は style=shout の行だけ青山龍星「熱血」）。", "- 画面の構成は renderer.html の SHOTS（セリフごとのショットの一覧）。", "- 人物は MPFB の人体の後ろ姿・遠景（顔なし、手のアップなし）。本物の画像は assets.md の権利の確かなものだけ。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
