#!/usr/bin/env python3
"""pilot_025「1秒で止まる男——ジョン・ポール・スタップ」（チャンネル「リバース」ドパ設計＋ガイドライン v2.4）の制作スクリプト。

ドパ設計（templates/DESIGN_MODES.md）：叩きつける文字・跳ねる字幕・画面の一打・効果音たっぷり。閃光は使わない。叫ぶ声は L01・L08・L09 だけ（青山龍星「熱血」）。
起承転結のカットイン（2026-11-01 のユーザーの指示）：文字は入れず、カメラの傾き・急な寄り・引き＋切れ目ごとに効果音と画面の一打をたっぷり。
起 L04＝傾いた寄りから引く、承 L06＝引きから急に寄る、転 L09＝ノズルの寄り → 水のブレーキ → 止まる瞬間の 3 回、結 L12＝寄りから大きく引く。
オープニング：結論の文字、W の声、本物の写真（そりに固定されるスタップ、米軍、パブリックドメイン）、衝撃波の一発。共通エンディングは短い版。
BGM は Kevin MacLeod「Raving Energy (faster)」（CC BY 4.0）。制作の土台は production/ext/kit（2026-11-01〜）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ext" / "kit"))
import epkit  # noqa: E402

pipeline, standard = epkit.setup(HERE, "dopa", bgm=("Raving Energy (faster).mp3", 134))

# カットインの効果音（文字なし、切れ目ごとにたっぷり）
CI1 = lambda c: [("impact", c, 1.0), ("hit", c, 0.8, 0.02), ("deep", c, 0.7, 0.03), ("whoosh", c, 0.7, 0.05), ("zoom", c, 0.6, 0.3), ("stamp", c, 0.6, 0.42)]
CI3 = lambda c: [("impact", c, 1.0), ("hit", c, 0.8, 0.02), ("whoosh", c, 0.7, 0.05), ("impact", c, 0.9, 0.45), ("hit", c, 0.7, 0.47), ("glitch", c, 0.5, 0.46),
                 ("impact", c, 1.0, 0.95), ("deep", c, 0.8, 0.96), ("whoosh", c, 0.7, 0.97), ("riser", c, 0.5, 1.1), ("hit", c, 0.9, 1.5)]

EP = standard.config({
    "id": "pilot_025",
    "out": "reverse_025_stapp.mp4",
    "cues": {
        "open": ("L00", 0.0), "hook": ("L01", 0.0), "ignite": ("L01", 0.55), "sled": ("L02", 0.0), "speed": ("L02", 0.5), "plane": ("L02b", 0.0), "man": ("L03", 0.0),
        "why": ("L04", 0.0), "g18": ("L04", 0.45), "eject": ("L05", 0.0), "self": ("L05", 0.75),
        "train": ("L06", 0.0), "injur": ("L07", 0.0), "rib": ("L07", 0.3), "wrist": ("L07", 0.72), "set": ("L08", 0.0), "setk": ("L08", 0.62),
        "final": ("L09", 0.0), "stop": ("L09", 0.5), "g40": ("L10", 0.0), "blind": ("L10", 0.45), "ton": ("L10b", 0.0), "finger": ("L11", 0.0), "ok": ("L11", 0.75),
        "ban": ("L11b", 0.0), "legacy": ("L12", 0.0), "belt": ("L12", 0.5), "back": ("L13", 0.0), "card": ("L13", 1.0),
    },
    "sfx": [("deep", "t0", 0.5, 0.05), ("impact", "hook", 1.0), ("hit", "hook", 0.8, 0.02), ("stamp", "hook", 0.7, 0.1), ("wind", "hook", 0.4, 0.2),
            ("riser", "ignite", 0.6, -0.3), ("impact", "ignite", 1.0), ("whoosh", "ignite", 0.9, 0.05), ("zoom", "ignite", 0.7, 0.1),
            ("whoosh", "sled", 0.9), ("sweep_up", "sled", 0.6, 0.1), ("stamp", "speed", 0.9), ("hit", "speed", 0.8, 0.02), ("tagpop", "speed", 0.5, 0.3), ("tagpop", "speed", 0.5, 0.45),
            ("whoosh", "plane", 1.0), ("zoom", "plane", 0.7, 0.2), ("stamp", "man", 0.8, 0.1), ("tagpop", "man", 0.6, 0.6), ("tagpop", "man", 0.6, 0.9),
            *CI1("why"), ("stamp", "g18", 0.9), ("glitch", "g18", 0.4, 0.1), ("whoosh", "eject", 0.8), ("impact", "eject", 0.7, 0.4), ("stamp", "self", 1.0), ("hit", "self", 0.9, 0.02),
            *CI1("train"), ("stamp", "train", 0.8, 0.5), ("tagpop", "injur", 0.6), ("hit", "rib", 0.8), ("stamp", "rib", 0.7, 0.05), ("hit", "wrist", 0.9), ("brake", "wrist", 0.6, 0.05),
            ("step", "set", 0.5), ("step", "set", 0.5, 0.35), ("hit", "setk", 1.0), ("stamp", "setk", 1.0, 0.05), ("glitch", "setk", 0.5, 0.05),
            *CI3("final"), ("brake", "stop", 1.0, 1.0), ("impact", "stop", 1.0, 1.05), ("deep", "g40", 1.0), ("stamp", "g40", 1.0, 0.05), ("glitch", "blind", 0.6), ("deep", "blind", 0.6, 0.1),
            ("tick", "ton", 0.5), ("tick", "ton", 0.5, 0.15), ("stamp", "ton", 0.9, 0.4), ("tagpop", "finger", 0.6, 0.3), ("tagpop", "finger", 0.6, 0.6), ("tagpop", "finger", 0.6, 0.9), ("discover", "ok", 0.7),
            ("stamp", "ban", 0.9, 0.3), ("hit", "ban", 0.8, 0.9), ("brake", "ban", 0.6, 0.92),
            *CI1("legacy"), ("prism", "belt", 0.6), ("discover", "belt", 0.6, 0.2), ("lock", "back", 1.0, 0.7), ("glow", "back", 0.5, 0.8), ("shimmer", "card", 0.45), ("discover", "card", 0.4, 0.1)],
    # BGM：オープニングは衝撃波の一発 → 曲を全開。カットインの直前に一瞬引いて、切れ目で戻す
    "music": {"style": "file_025", "sections": [
        ("t0", 0.0, "open_impact"), ("hook", -0.05, "f_full"), ("why", -0.35, "w_hold"), ("why", 0.0, "f_full"), ("train", -0.35, "w_hold"), ("train", 0.0, "f_full"),
        ("final", -0.4, "w_hold"), ("final", 0.0, "f_full"), ("blind", 0.0, "f_low"), ("finger", 0.0, "f_mid"), ("ban", 0.0, "f_full"),
        ("legacy", -0.35, "w_hold"), ("legacy", 0.0, "f_full"), ("end1", -0.6, "ending")]},
    "segments": ["open", "hook", "why", "train", "final", "legacy"],
    "extra_files": epkit.FILES,
    "workers": 1,
    "qc_frames": [("open", 0.4), ("open", 2.0), ("hook", 0.3), ("ignite", 0.4), ("sled", 0.5), ("speed", 0.8), ("plane", 0.5), ("man", 1.2), ("why", 0.2), ("g18", 0.8), ("eject", 0.4), ("self", 0.6),
                  ("train", 0.2), ("train", 1.0), ("rib", 0.6), ("wrist", 0.6), ("set", 0.4), ("setk", 0.5), ("final", 0.2), ("final", 0.7), ("final", 1.2), ("stop", 1.5),
                  ("g40", 0.5), ("blind", 0.8), ("ton", 0.8), ("finger", 1.0), ("ok", 0.6), ("ban", 1.2), ("legacy", 0.2), ("belt", 1.0), ("back", 1.2), ("card", 0.3)],
    "scenes": [
        ("0 オープニング（約 3 秒）", None, "hook", "結論の文字を大きく、本物の写真（B2：そりに固定されるスタップ）を中央。衝撃波の一発", "open_impact"),
        ("1 冒頭（フック）", "hook", "why", "最初の 1 秒：砂漠のレールの上のそり、9 本のノズルが点火 → 一気に加速、速度の数字 → 旅客機を追い越す → 座席に固定された後ろ姿", "曲 全開"),
        ("2 18G・起", "why", "train", "【起】カットイン（傾いた寄りから引く＋一打）→ 18G の数字 → 戦闘機から飛び出す座席 → 自分の体", "曲 全開"),
        ("3 けが・承", "train", "final", "【承】カットイン（引きから急に寄る＋一打）→ 35G → 本物の連続写真（B3）とけがの札 → 夕方の砂漠を歩く後ろ姿", "曲 全開"),
        ("4 最後の走行・転", "final", "legacy", "【転】カットイン 3 回：ノズルの寄り → 水のブレーキのしぶき → 止まる瞬間（決定的な瞬間）→ 40G、暗くなる視界 → 約 3 トン → ぼやけた医師の姿がはっきり → 1600 キロの計画に ×", "曲 全開 → 低く → 全開"),
        ("5 シートベルト・結", "legacy", "endcard", "【結】カットイン（寄りから大きく引く）→ 戦闘機の座席から車のシートベルトへ → 金具が締まる → 冒頭のレールへ", "曲 全開"),
        ("6 共通エンディング（短い版）", "endcard", None, "最後の画の上にロゴと決めゼリフ", "BGM ending"),
    ],
    "plan_notes": [
        "## 演出の方針（ドパ設計＋ガイドライン v2.4＋オープニング）",
        "",
        "- オープニング：結論の文字、W の声、本物の写真（B2）を中央。衝撃波の一発。",
        "- 最初の 1 秒：砂漠のレールの上、9 本のノズルの点火（決定的な映像の前ぶれ）。決定的な瞬間：L09 の停止（スロー）。",
        "- カットインは文字なし。カメラの動き＋切れ目ごとに効果音（impact・hit・whoosh・zoom・stamp）と画面の一打（2026-11-01 のユーザーの指示）。閃光は使わない。",
        "- 最後の一文と画を冒頭につなげる：シートベルトの金具 → 砂漠のレール。",
        "- 人物は MPFB の人体の後ろ姿・ヘルメット（顔なし、手のアップなし）。けがは札と本物の写真で示し、傷は描かない。",
        "- 本物の写真 B3（顔がゆがむ 6 枚）は 1954 年 6 月発表の走行（12G・22G）。12 月 10 日の走行の写真としては見せない（L07「29 回の走行で」の場面だけ）。",
        "- 声：VOICEVOX:玄野武宏、話速 1.5。L01・L08・L09 だけ VOICEVOX:青山龍星「熱血」。オープニングは VOICEVOX:冥鳴ひまり。BGM：Kevin MacLeod「Raving Energy (faster)」（CC BY 4.0）。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
