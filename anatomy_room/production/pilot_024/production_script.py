#!/usr/bin/env python3
"""pilot_024「花火の夜空——ソフィー・ブランシャール」（チャンネル「リバース」設計「悲劇」＋ガイドライン v2.4）の制作スクリプト。

設計「悲劇」（templates/DESIGN_MODES.md）：序盤はコテコテ（効果音・一打・派手な色・紙吹雪）、約 1/3（L06 アルプス）から少しずつシリアスに、BGM を静かに。
結（L10〜）は明朝体の静かな文字、曲を下げて風と遠い群衆の音だけ、暗めの画面。最後は 2.6 秒かけて暗転。共通エンディングなし。
ナレーターは本編の最初から最後まで同じ（玄野武宏）。最後の一言（L13）はゆっくりはっきり。
オープニング（約 3 秒）：結論の文字、W の声（冥鳴ひまり）、本物の版画（燃える気球から落ちるブランシャール、1869、パブリックドメイン）、ホラー調の音（bgm_file のモード h）。
BGM は Kevin MacLeod「Danse Macabre」（サン＝サーンス、CC BY 4.0）。制作の土台は production/ext/kit（2026-11-01〜）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ext" / "kit"))
import epkit  # noqa: E402

pipeline, standard = epkit.setup(HERE, "tragedy", bgm=("Danse Macabre.mp3", 67), black=2.6)

EP = standard.config({
    "id": "pilot_024",
    "out": "reverse_024_blanchard.mp4",
    "cues": {
        "open": ("L00", 0.0), "hook": ("L01", 0.0), "balloon": ("L01", 0.5), "sophie": ("L02", 0.0), "first": ("L02", 0.45),
        "rise": ("L03", 0.0), "husband": ("L03", 0.0), "collapse": ("L03", 0.38), "debt": ("L03", 0.78), "alone": ("L04", 0.0),
        "napoleon": ("L05", 0.0), "wedding": ("L05", 0.5), "milan": ("L05b", 0.0), "alps": ("L06", 0.0), "flood": ("L06", 0.52), "crowd": ("L07", 0.0),
        "night": ("L08", 0.0), "crown": ("L08", 0.45), "fire": ("L09", 0.0), "spark": ("L09", 0.4), "wait": ("L09b", 0.0),
        "fall": ("L10", 0.0), "net": ("L11", 0.0), "age41": ("L11", 0.72), "lastw": ("L12", 0.0), "funeral": ("L12", 0.5), "last": ("L13", 0.0),
    },
    # 効果音：起（〜L05b）はコテコテに多く、L06 から少しずつ減らし、結は風と低い音だけ
    "sfx": [("deep", "t0", 0.6), ("glitch", "t0", 0.4, 0.3), ("riser", "t0", 0.4, 1.5),
            ("impact", "hook", 0.9), ("hit", "hook", 0.7, 0.03), ("prism", "hook", 0.5, 0.1), ("whoosh", "balloon", 0.7), ("discover", "balloon", 0.6, 0.2), ("tagpop", "balloon", 0.5, 0.5),
            ("stamp", "sophie", 0.8, 0.05), ("tagpop", "sophie", 0.6, 0.4), ("stamp", "first", 0.9), ("hit", "first", 0.7, 0.03), ("prism", "first", 0.5, 0.1),
            ("whoosh", "husband", 0.7), ("stamp", "husband", 0.6, 0.2), ("brake", "collapse", 0.6), ("deep", "collapse", 0.5, 0.1), ("stamp", "debt", 0.9), ("glitch", "debt", 0.4, 0.05),
            ("riser", "alone", 0.6), ("whoosh", "alone", 0.8, 0.4), ("impact", "napoleon", 0.9), ("stamp", "napoleon", 0.9, 0.05), ("tagpop", "wedding", 0.6), ("tagpop", "wedding", 0.6, 0.3), ("prism", "wedding", 0.5, 0.2),
            ("paper", "milan", 0.5), ("shimmer", "milan", 0.5, 0.2),
            ("wind", "alps", 0.5), ("deep", "alps", 0.5, 0.2), ("wind", "flood", 0.4), ("bloom", "crowd", 0.5), ("shimmer", "crowd", 0.4, 0.3),
            ("wind", "night", 0.4), ("shimmer", "crown", 0.4), ("deep", "fire", 0.6), ("deep", "spark", 0.6, 0.2), ("wind", "wait", 0.5),
            ("wind", "fall", 0.5), ("deep", "fall", 0.5, 0.6), ("wind", "net", 0.5), ("wind", "lastw", 0.4), ("wind", "last", 0.5)],
    # BGM：オープニングはホラー調の音だけ → 曲（Danse Macabre）全開 → L06 から少しずつ下げ、風を上げる → 結は風だけ
    "music": {"style": "file_024", "sections": [
        ("t0", 0.0, "m0w0h100"), ("hook", -0.05, "m100w0"), ("alps", -0.1, "m80w10"), ("crowd", -0.1, "m70w15"), ("night", -0.1, "m55w25"), ("fire", -0.1, "m40w35"),
        ("wait", -0.1, "m25w45"), ("fall", -0.1, "m12w60"), ("net", -0.1, "m0w65"), ("lastw", -0.1, "m0w55"), ("last", -0.1, "m0w70")]},
    "segments": ["open", "hook", "rise", "night", "fall"],
    "extra_files": epkit.FILES,
    "workers": 1,
    "qc_frames": [("open", 0.3), ("open", 2.0), ("hook", 0.4), ("balloon", 0.8), ("sophie", 0.5), ("first", 0.8), ("husband", 0.3), ("collapse", 0.4), ("debt", 0.6), ("alone", 0.8),
                  ("napoleon", 0.4), ("wedding", 0.8), ("milan", 1.0), ("alps", 0.6), ("flood", 0.8), ("crowd", 0.8), ("night", 0.5), ("crown", 0.8), ("fire", 0.4), ("spark", 0.8),
                  ("wait", 1.0), ("fall", 1.0), ("net", 0.8), ("age41", 0.6), ("lastw", 1.0), ("funeral", 1.2), ("last", 1.0), ("last", 3.5)],
    "scenes": [
        ("0 オープニング（3 秒）", None, "hook", "本物の版画（燃える気球から落ちる、1869）を中央に、結論の文字を大きく。背景は夜空の 3D。ホラー調の音、W の声", "h100"),
        ("1 冒頭（フック）", "hook", "rise", "最初の 1 秒：夜の公園の上で花火の冠をつけた気球がふくらむ → 本物の肖像（1811）", "曲 全開"),
        ("2 起：一人で空へ（コテコテ）→ 承：アルプス（ここから少しずつ）", "rise", "night", "海峡の上の気球 → 倒れる夫の影 → 破産の寸前 → 一人で上がる → 祝典の旗と紙吹雪 → 本物の版画（ミラノ 1811）→ 雪の山・水の野原 → 夜の花火", "曲 全開 → 80 → 70%"),
        ("3 転：最後の夜", "night", "fall", "花火の冠の寄り → 火花が上がり、気球の下が赤く光る → 着陸を待つ群衆の後ろ姿", "曲 55 → 25%、風"),
        ("4 結：屋根と通り（明朝体の静かな文字）", "fall", "endcard", "燃える気球が屋根へ（遠景）→ 暗い通りに網だけ → 葬儀の行列の影 → 冒頭の夜空、残り火が消える", "曲なし、風だけ"),
        ("5 暗転（共通エンディングなし）", "endcard", None, "2.6 秒かけて暗転", "風だけ"),
    ],
    "plan_notes": [
        "## 演出の方針（設計「悲劇」＋ガイドライン v2.4）",
        "",
        "- オープニング 3 秒：結論の文字を画面の上〜中ほどに大きく、W の声。本物の版画（A1、1869）を中央に。背景は動く夜空。ホラー調の音。",
        "- 最初の 1 秒：夜の公園の上の、花火の冠をつけた気球（決定的な映像の前ぶれ）。",
        "- 起（〜L05b）はコテコテ：紙吹雪・派手な色・効果音・一打・跳ねる文字。L06（約 1/3）から色・効果音・一打・BGM・声を少しずつ落とし、結（L10〜）は明朝体の静かな文字、曲なし、風の音、暗めの画面。",
        "- 死の瞬間・遺体は見せない（屋根の遠景、通りに残った網だけ）。拍手・最後の言葉など確認できない話は入れない。",
        "- 最後の一文と画を冒頭につなげる：冒頭の夜空、花火の残り火が消える。",
        "- 人物は遠景の小さな影（顔なし）。本物の画像：A1 落下の版画（1869）・A2 肖像（Luigi Rados 1811、ミラノの夜の上昇）。どちらもパブリックドメイン。",
        "- BGM：Kevin MacLeod「Danse Macabre」（CC BY 4.0）。オープニングの音と風の音は合成。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
