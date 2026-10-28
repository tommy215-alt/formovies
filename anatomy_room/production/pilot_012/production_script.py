#!/usr/bin/env python3
"""pilot_012「手を洗うだけで、救える命があった」（ゼンメルワイス、チャンネル「リバース」標準ルール v3）の制作スクリプト。

処理の本体は production/common/pipeline.py、標準の既定値は production/common/standard.py
（ロゴなし・BGM tech_drive・やわらかい効果音・冒頭 0.1 秒で話し始める）。ここには、この話だけの設定を書く。
使い方は pipeline.py の冒頭（python production_script.py all など）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
import pipeline  # noqa: E402
import standard  # noqa: E402

EP = standard.config({
    "id": "pilot_012",
    "out": "reverse_012_semmelweis.mp4",
    # 映像と効果音のきっかけ：(セリフID, セリフ内の位置 0〜1)。renderer.html と同じ名前
    "cues": {
        "hook": ("L01", 0.0), "freeze": ("L01", 0.36), "hands": ("L01", 0.42), "lives": ("L01", 0.66),
        "ward": ("L02", 0.0), "beds": ("L03", 0.0), "family": ("L03", 0.55), "record": ("L04", 0.0),
        "clinics": ("L05", 0.0), "ratio": ("L06", 0.0), "first": ("L07", 0.0), "second": ("L07", 0.5), "gap": ("L08", 0.0),
        "search": ("L09", 0.0), "autopsy": ("L10", 0.0), "compare": ("L11", 0.0), "walk": ("L12", 0.0), "theory": ("L13", 0.0), "thought": ("L13", 0.72),
        "wash": ("L14", 0.0), "dip": ("L14", 0.45),
        "numbers": ("L15", 0.0), "y1846": ("L16", 0.0), "y1848": ("L17", 0.0), "drop": ("L17", 0.2), "home": ("L18", 0.0),
        "conflict": ("L19", 0.0), "miasma": ("L20", 0.0), "oppose": ("L21", 0.0), "support": ("L22", 0.0), "alone": ("L22", 0.3),
        "today": ("L23", 0.0), "family2": ("L24", 0.0), "last": ("L25", 0.0),
    },
    # 効果音：やわらかい音色（music.sfx_bank_soft）。(効果音, きっかけ, 音量, ずらす秒)
    "sfx": [("deep", "t0", 0.6, 0.0), ("tick", "freeze", 0.5), ("impact", "hands", 0.8), ("water", "hands", 0.45, 0.1), ("deep", "lives", 0.4),
            ("room", "ward", 0.6, -0.3), ("step", "ward", 0.4, 0.3), ("paper", "record", 0.5, 0.2),
            ("paper", "ratio", 0.5, 0.3), ("tick", "first", 0.45), ("tick", "second", 0.45), ("hit", "gap", 0.5, 0.4),
            ("deep", "autopsy", 0.5), ("paper", "compare", 0.5, 0.2), ("step", "walk", 0.5, 0.2), ("sweep_up", "thought", 0.3, -0.2),
            ("water", "dip", 0.8), ("water", "dip", 0.5, 1.2),
            ("paper", "numbers", 0.5, 0.3), ("tick", "y1846", 0.45), ("sweep_down", "drop", 0.35), ("glow", "drop", 0.6, 0.3),
            ("room", "conflict", 0.7, -0.2), ("deep", "oppose", 0.4), ("step", "alone", 0.4, 0.3),
            ("water", "today", 0.7, 0.2), ("water", "family2", 0.6, 0.2), ("water", "last", 0.5, 0.2)],
    # BGM：tech_drive（124 BPM）。(きっかけ, ずらす秒, モード)。物語の感情に合わせて変える（標準ルール v3 の「BGM の感情設計」）
    #   不安：doc_tense → 疑問と執念：doc_drive → doc_build → 発見前の一瞬の間：doc_break → 希望：doc_hope（長調の和音が差し込む）
    #   → 対立と孤独：doc_alone（希望の音を引き、音数を減らす）→ 現代：doc_warm（温かい和音＋穏やかなビート）→ エンディング
    "music": {"sections": [
        ("t0", 0.0, "doc_hook"), ("ward", -0.1, "doc_tense"), ("clinics", -0.1, "doc_drive"), ("search", -0.1, "doc_build"),
        ("wash", -0.1, "doc_build"), ("numbers", -0.1, "doc_break"), ("y1846", -0.1, "doc_drive"), ("y1848", -0.2, "doc_hope"),
        ("conflict", -0.3, "doc_alone"), ("today", -0.3, "doc_warm"), ("last", 0.0, "doc_warm_end"), ("end1", -0.6, "ending")]},
    "segments": ["hook", "ward", "clinics", "search", "wash", "numbers", "conflict", "today"],
    "extra_files": [],
    "qc_frames": [("t0", 0.4), ("freeze", 0.3), ("hands", 0.5), ("lives", 0.8), ("ward", 1.0), ("beds", 1.0), ("family", 1.0), ("record", 1.5),
                  ("clinics", 1.0), ("ratio", 1.5), ("first", 0.8), ("second", 0.8), ("gap", 1.5), ("search", 1.0), ("autopsy", 1.5),
                  ("compare", 1.5), ("walk", 1.5), ("theory", 1.5), ("thought", 0.8), ("wash", 1.0), ("dip", 1.0), ("numbers", 1.0),
                  ("y1846", 1.5), ("y1848", 1.5), ("home", 1.5), ("conflict", 1.5), ("miasma", 1.5), ("oppose", 1.5), ("alone", 1.5),
                  ("today", 1.5), ("family2", 2.0), ("last", 2.0)],
    "scenes": [
        ("1 冒頭（フック）", None, "ward", "暗い 19 世紀の病棟：空のベッドと消えかけたランプへ急速に寄る →「手を洗う」で一瞬止まり、医師の手もとへ →「救える命」で洗面器の水面に光", "1 拍目から BGM doc_hook、手もとで低い impact と水の音"),
        ("2 命が失われていた病院", "ward", "clinics", "廊下を行き交う医師と看護の人、静まり返った病室と並ぶベッド、戸口の家族のシルエット、記録簿を確かめる手もと。冷たい青とグレー", "BGM doc_tense（低音とキック、冷たいパルス）"),
        ("3 一人の医師が疑問を抱く", "clinics", "search", "廊下を歩くゼンメルワイス。記録簿の数字。二つの病棟を左右に並べる。1846 年の数字（第一産科 11.4%／第二産科 2.8%）", "BGM doc_drive"),
        ("4 原因を探し続ける", "search", "wash", "考え込む姿 → 解剖室（布をかけた台、遺体は描かない）→ 記録を比べる → 解剖室から廊下を通って病棟へ向かう手 → 手のまわりの光の粒（当時の考えのイメージ）", "BGM doc_build（密度を上げる）"),
        ("5 手洗いの導入", "wash", "numbers", "病棟の入口の洗面器。塩素を含む液に手を浸して洗う", "水の音／BGM doc_build"),
        ("6 数字が変わり始める", "numbers", "conflict", "記録簿に数字。グラフ 11.4%（1846）→ 1.3%（1848）。病室に暖かい光が少しずつ差し込む。家族のもとへ帰る母親のシルエット", "BGM doc_break（一瞬の間）→ doc_hope（長調の和音とやわらかい鍵盤が差し込む）、暖色の光"),
        ("7 それでも理解されなかった", "conflict", "today", "冷たい光の会議の場。資料を示すゼンメルワイスと、顔を背ける医師たち。暗い廊下で一人記録を見つめる姿", "BGM doc_alone（希望の音を引き、音数を減らす）、色調は冷たい青とグレーへ戻る"),
        ("8 今、私たちが手を洗う理由", "today", "endcard", "現代の病院の洗面台で手を洗う医療従事者 → 家庭で親が子どもの手を洗う → 帰宅した人が洗面台で手を洗う。自然な白色光とやわらかな暖色", "BGM doc_warm（温かい和音＋穏やかなビート）→ 最後の一文で薄く"),
        ("9 共通エンディング", "endcard", None, "リバース。世界の仕組みを、はじめから。", "BGM ending"),
    ],
    "plan_notes": [
        "## 演出の方針",
        "",
        "- 標準ルール v3：暗めのテック調を基本に、**色調と BGM を物語の感情に合わせて変える**（不安＝冷たい青 → 調査＝手もとだけに光 → 成果＝暖かい光が差し込む → 対立＝冷たい青へ戻る → 現代＝自然な白色光とやわらかな暖色）。字幕は従来の約 1.2 倍。",
        "- 人物は顔のない人形（stage.js の mochi3D）。ゼンメルワイスは暗い上着の若い医師。実際の顔は描かない。苦しむ患者・遺体は描かない（空のベッド、布をかけた台で示す）。",
        "- 注記は人物と場面が再現であることを最初の歴史の場面で 1 回、当時の考えのイメージ（光の粒）に 1 回だけ。",
        "- 事実の範囲：数字は第一産科の年間の値（1846 年 11.4%、1848 年 1.3%、ゼンメルワイスの 1861 年の著書の表）。「細菌」「消毒」という現代の言葉を、当時の彼の理解として使わない。反対した医師を悪人として描かない。支持した医師もいたことを言う。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
