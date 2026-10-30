#!/usr/bin/env python3
"""pilot_021「氷の上の気球——アンドレーの北極探検」（チャンネル「リバース」設計「悲劇」＋ガイドライン v2.4）の制作スクリプト。

設計「悲劇」（templates/DESIGN_MODES.md、3 回目の更新、2026-10-30）：序盤はコテコテ（効果音・一打・派手な色）、約 1/3（L05）から
起承転結に合わせて少しずつシリアスに、BGM を静かに。最後は環境音（風）と静かなナレーション、暗めの画面、2.6 秒かけて暗転。共通エンディングなし。
ナレーターは本編の最初から最後まで同じ（玄野武宏）。最後の一言（L14）はゆっくりはっきり。
冒頭 3 秒のオープニング（ユーザーの指示）：結論の文字を大きく、W の声（冥鳴ひまり）がはっきり読み、本物の写真を中央に、背景は動く CG、
BGM は本編と別の、不安定なホラー調の音（bgm_file.py のモードの h、合成）。
BGM は Kevin MacLeod「Machinations」（イ短調、140 BPM、CC BY 4.0、ユーザーが選んだ）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
sys.path.insert(0, str(HERE.parent / "ext"))
import pipeline  # noqa: E402
import standard  # noqa: E402
import music_ext  # noqa: E402,F401
import bgm_file  # noqa: E402
import ending_ext  # noqa: E402
import noend_ext  # noqa: E402

ending_ext.apply(pipeline)
noend_ext.apply(pipeline, black=2.6)   # 設計「悲劇」：共通エンディングなし、最後は 2.6 秒かけて暗転
bgm_file.register("file_machinations", HERE / "assets" / "bgm" / "Machinations.mp3", bpm=140, gains={"ending": "m0w70"}, smooth=3.0)

V3 = ["../ext/vendor/three147/" + f for f in ["GLTFLoader.js", "RGBELoader.js", "Pass.js", "EffectComposer.js", "RenderPass.js", "ShaderPass.js",
                                               "CopyShader.js", "SimplexNoise.js", "SSAOShader.js", "SSAOPass.js", "BokehShader.js", "BokehPass.js"]]

EP = standard.config({
    "id": "pilot_021",
    "out": "reverse_021_andree.mp4",
    "cues": {
        "open": ("L00", 0.0), "hook": ("L01", 0.0), "cam": ("L01", 0.5), "rise": ("L02", 0.0), "plan": ("L02", 0.4), "ball": ("L02", 0.72),
        "crew": ("L03", 0.0), "wait": ("L04", 0.0), "launch": ("L04", 0.42), "up": ("L04", 0.78),
        "fall": ("L05", 0.0), "rope": ("L05", 0.45), "pigeon": ("L06", 0.0), "silent": ("L06", 0.55), "icing": ("L07", 0.0), "hours": ("L07", 0.42), "land": ("L07", 0.72),
        "ice": ("L08", 0.0), "months": ("L08", 0.72), "drift": ("L09", 0.0), "island": ("L10", 0.0), "cutrec": ("L10", 0.62),
        "found": ("L11", 0.0), "ship": ("L11", 0.45), "why": ("L12", 0.0), "theories": ("L12", 0.45), "dev": ("L13", 0.0), "last": ("L14", 0.0),
    },
    # 効果音：起（〜L04）はコテコテに多く、承から少しずつ減らし、結は風と低い音だけ
    "sfx": [("deep", "t0", 0.6), ("glitch", "t0", 0.4, 0.3), ("riser", "t0", 0.4, 1.5),
            ("impact", "hook", 0.9), ("hit", "hook", 0.7, 0.03), ("wind", "hook", 0.4, 0.1), ("zoom", "cam", 0.7), ("stamp", "cam", 0.8, 0.1), ("tagpop", "cam", 0.5, 0.4),
            ("whoosh", "rise", 0.8), ("impact", "rise", 0.8, 0.05), ("prism", "rise", 0.6, 0.1), ("stamp", "plan", 0.9), ("hit", "plan", 0.7, 0.03), ("tagpop", "plan", 0.6, 0.3), ("tagpop", "plan", 0.6, 0.5),
            ("riser", "ball", 0.6), ("impact", "ball", 1.0, 0.3), ("discover", "ball", 0.6, 0.35),
            ("tagpop", "crew", 0.7), ("tagpop", "crew", 0.7, 0.35), ("tagpop", "crew", 0.7, 0.7), ("stamp", "crew", 0.6, 1.0),
            ("wind", "wait", 0.5), ("brake", "wait", 0.7, 0.3), ("glitch", "wait", 0.4, 0.4), ("riser", "launch", 0.8), ("whoosh", "up", 1.0), ("impact", "up", 1.0, 0.05), ("prism", "up", 0.7, 0.1), ("sweep_up", "up", 0.5, 0.2),
            ("sweep_down", "rope", 0.6), ("deep", "rope", 0.5, 0.2),
            ("whoosh", "pigeon", 0.4), ("wind", "silent", 0.4),
            ("wind", "icing", 0.4), ("deep", "land", 0.6), ("impact", "land", 0.5, 0.05),
            ("wind", "ice", 0.5), ("step", "ice", 0.3, 0.5), ("step", "ice", 0.3, 1.0), ("tick", "months", 0.3),
            ("wind", "drift", 0.5), ("deep", "island", 0.5), ("wind", "cutrec", 0.5),
            ("wind", "found", 0.5), ("deep", "ship", 0.4), ("wind", "why", 0.4), ("paper", "dev", 0.3), ("wind", "last", 0.5)],
    # BGM：オープニングはホラー調の音だけ（h100）→ 本編は曲（Machinations）全開 → L05 から曲を少しずつ下げ、風を上げる → 結は風だけ
    "music": {"style": "file_machinations", "sections": [
        ("t0", 0.0, "m0w0h100"), ("hook", -0.05, "m100w0"), ("fall", -0.1, "m80w10"), ("pigeon", -0.1, "m65w20"), ("icing", -0.1, "m50w35"),
        ("ice", -0.1, "m35w50"), ("drift", -0.1, "m25w60"), ("island", -0.1, "m12w70"), ("found", -0.1, "m0w65"), ("dev", -0.1, "m0w55"), ("last", -0.1, "m0w70")]},
    "segments": ["open", "hook", "rise", "fall", "ice", "found"],
    "extra_files": ["../ext/hud_ext.js", "../common/cine.js", "assets/assets.js", "assets/scene_assets.js"] + V3,
    "workers": 1,
    "qc_frames": [("open", 0.3), ("open", 1.8), ("hook", 0.4), ("cam", 0.5), ("rise", 0.5), ("plan", 0.4), ("ball", 0.6), ("crew", 0.6), ("wait", 0.5), ("launch", 0.4), ("up", 0.5),
                  ("fall", 0.5), ("rope", 0.6), ("pigeon", 0.6), ("silent", 0.6), ("icing", 0.6), ("hours", 0.5), ("land", 0.6),
                  ("ice", 0.8), ("months", 0.5), ("drift", 1.0), ("island", 0.8), ("cutrec", 0.8), ("found", 0.8), ("ship", 0.8), ("why", 0.8), ("theories", 0.8),
                  ("dev", 0.8), ("last", 1.0), ("last", 3.5)],
    "scenes": [
        ("0 オープニング（3 秒）", None, "hook", "本物の写真（A1）を中央に、結論の文字を大きく。背景は吹雪の CG。ホラー調の音、W の声", "h100"),
        ("1 冒頭（フック）", "hook", "rise", "雪に埋もれたカメラ → 一打で引くと氷の島", "曲 全開"),
        ("2 起：計画と出発（コテコテ）", "rise", "fall", "紙吹雪とふくらむ気球 → 3 人の影と名札 → 風見 → 派手な上昇", "曲 全開"),
        ("3 承：綱・鳩・着氷（ここから少しずつ）", "fall", "ice", "外れて落ちる綱 → 霧へ飛ぶ鳩 → 霜のつく気球、氷原へ", "曲 80 → 50%、風"),
        ("4 転：氷の上", "ice", "found", "そりを引く 3 人 → 流される氷の地図 → 暗い海と白い島", "曲 35 → 12%、風"),
        ("5 結：発見と写真", "found", "endcard", "船の影と雪の装備 → 明朝体の静かな文字 → 浮かび上がる写真 → 冒頭のカメラ", "曲なし、風だけ"),
        ("6 暗転（共通エンディングなし）", "endcard", None, "2.6 秒かけて暗転", "風だけ"),
    ],
    "plan_notes": [
        "## 演出の方針（設計「悲劇」3 回目の更新＋ガイドライン v2.4）",
        "",
        "- オープニング 3 秒：結論の文字を画面の上〜中ほどに大きく、W の声ではっきり読む。本物の写真を中央に。背景は動く CG。BGM は本編と別のホラー調の音。",
        "- 冒頭（本編）の最初の 1 秒：雪に埋もれた古いカメラ（決定的な映像）。",
        "- 起（〜L04）はコテコテ：派手な色（紙吹雪・光の筋）、効果音と一打を多く、跳ねる文字。L05（約 1/3）から少しずつ色・効果音・一打・BGM・声を落とし、結（L11〜）は明朝体の静かな文字、曲なし、風の音、暗めの画面。",
        "- ナレーターは本編の最初から最後まで玄野武宏。最後の一言（L14）は話速 1.0、前に 0.6 秒の間。",
        "- 最後の一文と画を冒頭につなげる：雪に埋もれたカメラ。",
        "- 本物の写真：氷の上のキャンプ（A1、Nils Strindberg、1897、パブリックドメイン）。",
        "- 人物は MPFB の人体の後ろ姿・遠景（顔なし、手のアップなし）。遺体・死の瞬間は見せない。死因は断定しない。",
        "- BGM：Kevin MacLeod「Machinations」（CC BY 4.0）。オープニングの音と風の音は合成。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
