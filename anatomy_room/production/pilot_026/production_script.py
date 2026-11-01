#!/usr/bin/env python3
"""pilot_026「地球の年齢と、空の鉛——クレア・パターソン」（チャンネル「リバース」知的設計＋ガイドライン v2.4）の制作スクリプト。

知的設計の編集設定（templates/DESIGN_MODES.md）：話速はオモテ 1.5・W 1.3・行間 0.03。起承転結の頭にカットイン（カメラの動きだけ、文字・効果音なし）：
起 L03＝傾いた寄りから引く、承 L05＝引きから急に寄る、転 L09＝低い角度 → 机の紙の寄り → 引きの 3 回、結 L12＝寄りから大きく引く。
オープニング（約 3 秒）：結論の文字、W の声、本物の写真（バリンジャー・クレーター、USGS、パブリックドメイン）、衝撃波の一発（open_impact）。共通エンディングは短い版。
BGM は外のフリー音源 Kevin MacLeod「Clean Soul」（CC BY 4.0、scripts/pilot_026/assets.md）。制作の土台は production/ext/kit（2026-11-01〜）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ext" / "kit"))
import epkit  # noqa: E402

pipeline, standard = epkit.setup(HERE, "intel", bgm=("Clean Soul.mp3", 90))

EP = standard.config({
    "id": "pilot_026",
    "out": "reverse_026_patterson.mp4",
    "cues": {
        "open": ("L00", 0.0), "hook": ("L01", 0.0), "bench": ("L01", 0.5), "uran": ("L02", 0.0),
        "dirt": ("L03", 0.0), "contam": ("L03", 0.42), "clean": ("L04", 0.0), "age": ("L05", 0.0), "err": ("L05", 0.75),
        "source": ("L06", 0.0), "ocean": ("L07", 0.0), "sky": ("L08", 0.0), "pump": ("L08", 0.45),
        "warn": ("L09", 0.0), "hundred": ("L09", 0.45), "ice": ("L10", 0.0), "muro": ("L10", 0.5), "fight": ("L11", 0.0), "law": ("L11", 0.5),
        "end": ("L12", 0.0), "un": ("L12b", 0.0), "back": ("L13", 0.0), "card": ("L13", 1.0),
    },
    "sfx": [("title", "hook", 0.6, 0.02), ("whoosh", "hook", 0.5, 0.1), ("room", "bench", 0.4), ("scan", "uran", 0.4), ("tick", "uran", 0.3, 0.6),
            ("glitch", "contam", 0.35), ("tick", "contam", 0.3, 0.3), ("shimmer", "clean", 0.4, 0.2), ("reveal", "age", 0.55, 0.5), ("lock", "err", 0.45),
            ("deep", "source", 0.4), ("data", "ocean", 0.4, 0.2), ("whoosh", "sky", 0.4), ("paper", "pump", 0.35),
            ("data", "hundred", 0.45), ("lock", "hundred", 0.4, 1.2), ("scan", "ice", 0.4), ("tagpop", "muro", 0.4, 0.2), ("deep", "fight", 0.4), ("tick", "law", 0.3), ("tick", "law", 0.3, 0.4),
            ("data", "end", 0.4, 0.4), ("bloom", "un", 0.45), ("glow", "back", 0.4, 0.2), ("shimmer", "card", 0.45), ("discover", "card", 0.4, 0.1)],
    # BGM：オープニングは衝撃波の一発 → 曲（Clean Soul）。カットインの前は少し引く（w_hold）。結から温かく
    "music": {"style": "file_026", "sections": [
        ("t0", 0.0, "open_impact"), ("hook", -0.05, "f_full"), ("dirt", -0.5, "w_hold"), ("dirt", 0.0, "f_full"), ("age", -0.5, "w_hold"), ("age", 0.0, "f_full"),
        ("warn", -0.5, "w_hold"), ("warn", 0.0, "f_full"), ("end", -0.5, "w_hold"), ("end", 0.0, "f_full"), ("end1", -0.6, "ending")]},
    "segments": ["open", "hook", "dirt", "source", "warn", "end"],
    "extra_files": epkit.FILES + ["../common/vendor/earth/earth_tex.js"],
    "workers": 1,
    "qc_frames": [("open", 0.4), ("open", 2.0), ("hook", 0.5), ("bench", 0.8), ("uran", 1.0), ("dirt", 0.2), ("contam", 0.8), ("clean", 1.2), ("age", 0.2), ("age", 1.4), ("err", 0.6),
                  ("source", 0.8), ("ocean", 1.5), ("sky", 0.3), ("pump", 1.0), ("warn", 0.2), ("warn", 0.7), ("warn", 1.2), ("hundred", 1.5), ("ice", 1.0), ("muro", 1.0),
                  ("fight", 0.6), ("law", 1.2), ("end", 0.2), ("end", 1.5), ("un", 1.0), ("back", 1.0), ("card", 0.3)],
    "scenes": [
        ("0 オープニング（約 3 秒）", None, "hook", "結論の文字を大きく、本物の写真（バリンジャー・クレーター）を中央、背景は漂う光の粒。衝撃波の一発", "open_impact"),
        ("1 冒頭（フック）", "hook", "dirt", "最初の 1 秒：宇宙から落ちてくる隕石 → 実験台の後ろ姿 → ウランが鉛に変わる図（模式）", "Clean Soul"),
        ("2 汚れた実験室・起〜承", "dirt", "source", "【起】カットイン（傾いた寄りから引く）→ 空気に浮かぶ赤い鉛の粒 → 白くなる実験室 →【承】カットイン（引きから急に寄る）→ 45.5 億年（決定的な瞬間）", "Clean Soul"),
        ("3 鉛はどこから", "source", "warn", "実験室の窓と粒 → 海の断面（模式）→ 本物の写真（ETHYL の給油機）と空へ上がる粒", "Clean Soul"),
        ("4 警告・転", "warn", "end", "【転】カットイン 3 回：低い角度の机 → 紙の寄り → 引き → 最大 100 倍（見積もり）→ 氷の層（模式）と室住正世 → 大きな建物の影の前の後ろ姿 → 規制の年表", "Clean Soul"),
        ("5 世界から消える・結", "end", "endcard", "【結】カットイン（寄りから大きく引く）→ 地球の上の赤い点が消えていく → 年 120 万人 → 澄んだ地球から宇宙へ", "Clean Soul"),
        ("6 共通エンディング（短い版）", "endcard", None, "最後の画の上にロゴと決めゼリフ", "BGM ending"),
    ],
    "plan_notes": [
        "## 演出の方針（知的設計の編集設定＋ガイドライン v2.4＋オープニング）",
        "",
        "- オープニング：結論の文字を画面の上〜中ほどに大きく、W の声。本物の写真（バリンジャー・クレーター、USGS）を中央に。衝撃波の一発。",
        "- 最初の 1 秒：宇宙から落ちてくる隕石（決定的な映像の前ぶれ）。決定的な瞬間：L05「45.5 億年」。",
        "- カットインはカメラの動きだけ（文字・効果音なし、2026-11-01 のユーザーの指示）。斜めの光の筋（Cine.shaft）は使わない。",
        "- 最後の一文と画を冒頭につなげる：澄んだ地球から宇宙へ引き、隕石が横切る。",
        "- 人物は MPFB の人体の後ろ姿（顔なし、手のアップなし）。本人の写真は権利が不明なので使わない。グラフ・断面・氷の層は模式図。",
        "- 声：VOICEVOX:玄野武宏（v7）、話速 1.5、最後の L13 だけ 1.35。オープニングだけ VOICEVOX:冥鳴ひまり。BGM：Kevin MacLeod「Clean Soul」（CC BY 4.0）。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
