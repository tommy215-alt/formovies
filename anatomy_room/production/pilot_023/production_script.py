#!/usr/bin/env python3
"""pilot_023「死を待つだけの病に、薬が生まれた——インスリンの発見」（チャンネル「リバース」知的設計＋ガイドライン v2.4）の制作スクリプト。

知的設計の編集設定（templates/DESIGN_MODES.md、参考 pilot_022）：
- 話速はオモテ 1.5・W 1.3・行間 0.03。
- 起承転結の頭にカットイン：起 L02・承 L03・結 L11 は暗転の大きな文字 1 回だけ、転 L09（1 月 23 日）は暗転 → 2 カットの 3 回。
- 冒頭のオープニング（約 3 秒）：結論の文字を大きく、W の声（冥鳴ひまり）が読み、本物の写真（バンティングとベストと犬、1921、CC BY 2.0）を中央。
  音は衝撃波の一発（ext/opening_bgm.py のモード open_impact）。
- 共通エンディングは短い版（ending_ext）。BGM は lab_dub（直前の pilot_022 は lab_melodic）。

処理の本体は production/common/pipeline.py、標準の既定値は production/common/standard.py。素材は assets/（scripts/pilot_023/assets.md）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
sys.path.insert(0, str(HERE.parent / "ext"))
import pipeline  # noqa: E402
import standard  # noqa: E402
import music_ext  # noqa: E402,F401
import opening_bgm  # noqa: E402,F401
import ending_ext  # noqa: E402

ending_ext.apply(pipeline)   # 共通エンディングの短い版（この回の処理の中だけ）

V3 = ["../ext/vendor/three147/" + f for f in ["GLTFLoader.js", "RGBELoader.js", "Pass.js", "EffectComposer.js", "RenderPass.js", "ShaderPass.js",
                                               "CopyShader.js", "SimplexNoise.js", "SSAOShader.js", "SSAOPass.js", "BokehShader.js", "BokehPass.js"]]
CI1 = lambda c: [("impact", c, 0.9), ("deep", c, 0.7, 0.02), ("whoosh", c, 0.5, 0.42)]   # カットイン 1 回
CI3 = lambda c: [("impact", c, 1.0), ("deep", c, 0.8, 0.02), ("hit", c, 0.7, 0.45), ("whoosh", c, 0.6, 0.42), ("impact", c, 0.8, 0.95), ("hit", c, 0.6, 1.5)]   # カットイン 3 回

EP = standard.config({
    "id": "pilot_023",
    "out": "reverse_023_insulin.mp4",
    "cues": {
        "open": ("L00", 0.0), "hook": ("L01", 0.0), "boy": ("L01", 0.45), "nodrug": ("L02", 0.0), "diet": ("L02", 0.42),
        "idea": ("L03", 0.0), "note": ("L03", 0.55), "plan": ("L04", 0.0), "lab": ("L05", 0.0), "dogs": ("L05", 0.55), "dogfall": ("L06", 0.0),
        "fail": ("L07", 0.0), "first": ("L07", 0.0), "abscess": ("L07", 0.6), "collip": ("L08", 0.0),
        "turn": ("L09", 0.0), "jan23": ("L09", 0.0), "normal": ("L09", 0.5), "live": ("L10", 0.0), "letter": ("L10", 0.3),
        "legacy": ("L11", 0.0), "patent": ("L11", 0.0), "mass": ("L11", 0.55), "nobel": ("L12", 0.0), "share": ("L12", 0.35), "cure": ("L13", 0.0),
        "back": ("L14", 0.0), "card": ("L14", 1.0),
    },
    "sfx": [("title", "hook", 0.6, 0.02), ("room", "hook", 0.4, 0.1), ("tick", "boy", 0.3), ("tick", "boy", 0.3, 0.6),
            *CI1("nodrug"), ("tick", "diet", 0.35), ("tick", "diet", 0.35, 0.5), ("tick", "diet", 0.35, 1.0),
            *CI1("idea"), ("paper", "note", 0.4), ("scanline", "plan", 0.4), ("paper", "plan", 0.35, 0.3),
            ("room", "lab", 0.35), ("glow", "dogs", 0.35), ("data", "dogfall", 0.45), ("lock", "dogfall", 0.4, 1.4),
            ("deep", "first", 0.45), ("tick", "first", 0.3, 0.3), ("deep", "abscess", 0.4), ("scan", "collip", 0.4), ("shimmer", "collip", 0.35, 1.2),
            *CI3("jan23"), ("zoom", "jan23", 0.5, 1.5), ("reveal", "normal", 0.55), ("data", "normal", 0.4, 0.3), ("lock", "normal", 0.45, 1.3),
            ("bloom", "live", 0.45), ("paper", "letter", 0.4), ("shimmer", "letter", 0.4, 0.5),
            *CI1("patent"), ("ring", "mass", 0.35), ("tick", "mass", 0.3, 0.3), ("tick", "mass", 0.3, 0.6), ("tick", "mass", 0.3, 0.9),
            ("bloom", "nobel", 0.55), ("discover", "nobel", 0.45, 0.1), ("shimmer", "share", 0.35),
            ("glow", "cure", 0.45), ("prism", "cure", 0.35, 0.6), ("glow", "back", 0.4, 0.2), ("shimmer", "card", 0.45), ("discover", "card", 0.4, 0.1)],
    # BGM：オープニングは衝撃波の一発（open_impact）→ 冬の病室（謎）→ 薬はない（陰り）→ 計画（物語）→ 実験（集中）→ 最初の失敗（陰り）→ 精製（集中）
    #      → 転：一度引いて、1 月 23 日で発見 → 13 年・手紙（温かく）→ 結：特許・量産（高まり）→ ノーベル（発見）→ 命をつなぐ（温かく）→ 冒頭へ
    "music": {"style": "lab_dub", "sections": [
        ("t0", 0.0, "open_impact"), ("hook", -0.05, "w_hook"), ("nodrug", -0.5, "w_hold"), ("nodrug", 0.0, "w_shade"),
        ("idea", -0.5, "w_hold"), ("idea", 0.0, "w_story"), ("lab", -0.1, "w_focus"), ("first", -0.1, "w_shade"), ("collip", -0.1, "w_focus"),
        ("jan23", -0.5, "w_hold"), ("jan23", 0.0, "w_discover"), ("live", -0.1, "w_warm"), ("patent", -0.5, "w_hold"), ("patent", 0.0, "w_rise"),
        ("nobel", -0.1, "w_discover"), ("cure", -0.1, "w_warm"), ("end1", -0.6, "ending")]},
    "segments": ["open", "hook", "idea", "fail", "turn", "legacy", "back"],
    "extra_files": ["../ext/hud_ext.js", "../common/cine.js", "assets/assets.js", "assets/scene_assets.js"] + V3,
    "workers": 1,
    "qc_frames": [("open", 0.4), ("open", 2.0), ("hook", 0.5), ("boy", 0.6), ("nodrug", 0.2), ("diet", 0.6), ("idea", 0.2), ("note", 0.6), ("plan", 0.8),
                  ("lab", 0.6), ("dogs", 0.6), ("dogfall", 1.0), ("first", 0.6), ("abscess", 0.6), ("collip", 1.2), ("jan23", 0.2), ("jan23", 0.7),
                  ("jan23", 1.2), ("jan23", 1.9), ("normal", 1.2), ("live", 0.4), ("letter", 1.0), ("patent", 0.2), ("mass", 0.8), ("nobel", 0.8),
                  ("share", 0.8), ("cure", 1.0), ("back", 1.0), ("card", 0.3)],
    "scenes": [
        ("0 オープニング（約 3 秒）", None, "hook", "結論の文字を大きく、本物の写真（A1：バンティングとベストと犬、1921）を中央、背景は漂う光の粒。衝撃波の一発", "open_impact"),
        ("1 冒頭（フック）・起", "hook", "idea", "最初の 1 秒：冬の病室のベッド（再現、顔なし）→【起】カットイン「薬は なかった」→ 小さな食事と時計", "w_hook → w_shade"),
        ("2 計画と実験・承", "idea", "fail", "【承】カットイン「ノートに 書いた計画」→ 夜の机の後ろ姿 → ノートのメモ（原文）→ 夏の研究室の 2 人 → 下がる血糖（模式図）", "w_story → w_focus"),
        ("3 最初の失敗と精製", "fail", "turn", "病室、濁った液の注射器（手のアップなし）→ 澄んでいくフラスコ", "w_shade → w_focus"),
        ("4 1 月 23 日・転", "turn", "legacy", "【転】カットイン 3 回「1月23日 もう一度」→ 澄んだ液の小瓶の極端な寄り → 窓の光の病室 → 朝の光（光の転換）→ 正常の帯に入る血糖 → テディの本物の手紙", "w_hold → w_discover → w_warm"),
        ("5 特許・ノーベル・いま・結", "legacy", "back", "【結】カットイン「特許は 1ドルで」→ 増えていく薬瓶 → メダルの光 → ペン型の注射器", "w_rise → w_discover → w_warm"),
        ("6 冒頭へ", "back", "endcard", "冒頭の病室に朝の光", "w_warm"),
        ("7 共通エンディング（短い版）", "endcard", None, "最後の画の上にロゴと決めゼリフ", "BGM ending"),
    ],
    "plan_notes": [
        "## 演出の方針（知的設計の編集設定＋ガイドライン v2.4＋オープニング）",
        "",
        "- オープニング：結論の文字を画面の上〜中ほどに大きく、W の声ではっきり読む。本物の写真（バンティングとベストと犬、1921、CC BY 2.0）を中央に。背景は動く CG。衝撃波の一発。",
        "- 冒頭（本編）の最初の 1 秒：冬の病室のベッド（決定的な映像）。",
        "- 起承転結のカットイン：起 L02・承 L03・結 L11 は暗転の文字 1 回、転 L09 は 3 回。",
        "- 決定的な瞬間：1 月 23 日、病室に朝の光が差し込む（光の転換）。思いが伝わる場面：テディの本物の手紙。",
        "- 最後の一文と画を冒頭につなげる：冒頭の病室に戻り、朝の光。",
        "- 人物は MPFB の人体の後ろ姿（顔なし、手のアップなし）。少年は布団のふくらみだけで、体は描かない。動物実験は犬も手術も描かず、図で見せる。",
        "- 声：VOICEVOX:玄野武宏（v7）、話速 1.5、行間 0.03 秒。最後の L14 だけ 1.35。オープニングだけ VOICEVOX:冥鳴ひまり。BGM：lab_dub。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
