#!/usr/bin/env python3
"""pilot_031「見えない光——クラレンス・ダリー」（チャンネル「リバース」設計「悲劇」5 回目の更新（明朝体・最初から暗く張り詰めた編集・悲しい BGM で終盤は無音・知的設計と同じオープニング・共通エンディングなし）＋ガイドライン v2.4）の制作スクリプト。

台本は scripts/pilot_031/script_draft.md（2026-11-01 にユーザーが「OK」）、事実は fact_check.md、画像と曲は assets.md。
BGM は Kevin MacLeod「Despair and Triumph」（incompetech、CC BY 4.0）。制作の土台は production/ext/kit（epkit・kit.js・shots.js）。
起承転結のカットイン：なし（悲劇）。このファイルは 10 本同時の制作で台本から作った（cues は行ごとに l01・l01m〔0.5 秒後〕など）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ext" / "kit"))
import epkit  # noqa: E402

pipeline, standard = epkit.setup(HERE, "tragedy", bgm=("Despair and Triumph.mp3", 43), black=2.6)

EP = standard.config({
    "id": "pilot_031",
    "out": "reverse_031_dally.mp4",
    "cues": {"open": ["L00", 0.0], "hook": ["L01", 0.0], "a": ["L03", 0.0], "b": ["L07", 0.0], "c": ["L10", 0.0], "l00": ["L00", 0.0], "l00m": ["L00", 0.5], "l01": ["L01", 0.0], "l01m": ["L01", 0.5], "l01b": ["L01b", 0.0], "l01bm": ["L01b", 0.5], "l02": ["L02", 0.0], "l02m": ["L02", 0.5], "l03": ["L03", 0.0], "l03m": ["L03", 0.5], "l04": ["L04", 0.0], "l04m": ["L04", 0.5], "l05": ["L05", 0.0], "l05m": ["L05", 0.5], "l06": ["L06", 0.0], "l06m": ["L06", 0.5], "l07": ["L07", 0.0], "l07m": ["L07", 0.5], "l08": ["L08", 0.0], "l08m": ["L08", 0.5], "l09": ["L09", 0.0], "l09m": ["L09", 0.5], "l10": ["L10", 0.0], "l10m": ["L10", 0.5], "l11": ["L11", 0.0], "l11m": ["L11", 0.5], "l12": ["L12", 0.0], "l12m": ["L12", 0.5]},
    "sfx": [["deep", "hook", 0.5], ["wind", "hook", 0.3, 0.1], ["wind", "l01b", 0.35, 0.2], ["paper", "l03", 0.35, 0.2], ["deep", "l05", 0.35, 0.2], ["wind", "l07", 0.35, 0.2], ["paper", "l09", 0.35, 0.2], ["deep", "l11", 0.35, 0.2]],
    "music": {"style": "file_031", "sections": [["t0", 0.0, "open_impact"], ["hook", -0.05, "m100w0"], ["l04", -0.1, "m85w10"], ["l05", -0.1, "m65w20"], ["l07", -0.1, "m45w30"], ["l09", -0.1, "m25w45"], ["l10", -0.1, "m10w55"], ["l11", -0.1, "m0w65"], ["l12", -0.1, "m0w70"]]},
    "segments": ["open", "hook", "a", "b", "c"],
    "extra_files": epkit.FILES + ["../ext/kit/shots.js"],
    "workers": 1,
    "qc_frames": [["open", 0.4], ["open", 2.0], ["l01", 0.6], ["l01b", 0.6], ["l02", 0.6], ["l03", 0.6], ["l04", 0.6], ["l05", 0.6], ["l06", 0.6], ["l07", 0.6], ["l08", 0.6], ["l09", 0.6], ["l10", 0.6], ["l11", 0.6], ["l12", 0.6]],
    "scenes": [('0 open', None, 'hook', '', ''), ('1 hook', 'hook', 'a', '', ''), ('2 a', 'a', 'b', '', ''), ('3 b', 'b', 'c', '', ''), ('4 c', 'c', 'endcard', '', ''), ('5 暗転', 'endcard', None, '', '')],
    "plan_notes": ["## 演出の方針", "", "- 設計：設計「悲劇」5 回目の更新（明朝体・最初から暗く張り詰めた編集・悲しい BGM で終盤は無音・知的設計と同じオープニング・共通エンディングなし）。", "- 画面の構成は renderer.html の SHOTS（セリフごとのショットの一覧）。", "- 人物は MPFB の人体の後ろ姿・遠景（顔なし、手のアップなし）。本物の画像は assets.md の権利の確かなものだけ。"],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
