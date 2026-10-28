#!/usr/bin/env python3
"""pilot_013「宇宙飛行士の命を、数字で支えた女性——キャサリン・ジョンソン」（チャンネル「リバース」標準ルール v4）の制作スクリプト。

処理の本体は production/common/pipeline.py、標準の既定値は production/common/standard.py。映像品質の部品は common/cine.js（renderer.html が読み込む）。
使い方は pipeline.py の冒頭（python production_script.py all など）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
import pipeline  # noqa: E402
import standard  # noqa: E402

EP = standard.config({
    "id": "pilot_013",
    "out": "reverse_013_katherine_johnson.mp4",
    # 映像と効果音のきっかけ：(セリフID, セリフ内の位置 0〜1)。renderer.html と同じ名前
    "cues": {
        "hook": ("L01", 0.0), "lift": ("L01", 0.12), "cut": ("L01", 0.36),
        "girl": ("L02", 0.0), "count": ("L03", 0.0), "school": ("L04", 0.0), "shapes": ("L04", 0.25), "campus": ("L04", 0.62),
        "naca": ("L05", 0.0), "room": ("L06", 0.0), "west": ("L07", 0.0), "cafe": ("L08", 0.0), "work": ("L09", 0.0),
        "orbit": ("L10", 0.0), "path": ("L11", 0.0), "back": ("L11", 0.3), "team": ("L12", 0.0),
        "trust": ("L13", 0.0), "machine": ("L14", 0.0), "ask": ("L15", 0.0), "check": ("L16", 0.0), "quiet": ("L16", 1.0),
        "space": ("L17", 0.0), "wide": ("L18", 0.0), "ground": ("L19", 0.0),
        "end": ("L20", 0.0), "desk2": ("L21", 0.0), "window": ("L22", 0.0), "last": ("L23", 0.0),
    },
    # 効果音：やわらかい音色（music.sfx_bank_soft）。(効果音, きっかけ, 音量, ずらす秒)
    "sfx": [("roar", "t0", 1.0, 0.0), ("impact", "lift", 0.7), ("deep", "lift", 0.5, 0.1), ("pencil", "cut", 0.9, 0.05), ("pencil", "cut", 0.7, 0.9),
            ("paper", "girl", 0.5, 0.2), ("step", "count", 0.5, 0.2), ("step", "count", 0.4, 0.8), ("pencil", "shapes", 0.6), ("sweep_up", "shapes", 0.3, 0.6),
            ("room", "naca", 0.6, -0.2), ("calc", "room", 0.7, 0.3), ("calc", "room", 0.5, 1.6), ("tick", "west", 0.4), ("deep", "cafe", 0.4), ("calc", "work", 0.7, 0.1), ("pencil", "work", 0.6, 1.4),
            ("sweep_up", "orbit", 0.35, -0.3), ("deep", "orbit", 0.5, 0.2), ("sweep_down", "back", 0.3, 0.4), ("paper", "team", 0.5, 0.3),
            ("room", "trust", 0.6, -0.2), ("tape", "machine", 0.8), ("tick", "machine", 0.4, 1.0), ("paper", "ask", 0.6, 1.2),
            ("calc", "check", 0.8, 0.2), ("pencil", "check", 0.7, 1.6), ("calc", "check", 0.6, 3.0), ("tick", "quiet", 0.5, 0.2),
            ("glow", "space", 0.6, 0.1), ("deep", "wide", 0.4), ("paper", "ground", 0.5, 0.6),
            ("deep", "end", 0.35), ("paper", "desk2", 0.4, 0.4), ("deep", "last", 0.4, 0.6)],
    # BGM：tech_drive（124 BPM）。冒頭は強いリズム → 少女時代は温かく穏やか → 研究所は冷たい緊張 → 隔離の札で孤独 → 計算を積み上げる → 宇宙へ広がる
    #   → グレン → 計算の確認は音数を減らす（計算機の音を聞かせる）→ 宇宙船の成功で希望の和音 → 余韻
    "music": {"sections": [
        ("t0", 0.0, "doc_hook"), ("girl", -0.1, "doc_warm"), ("naca", -0.2, "doc_tense"), ("cafe", -0.1, "doc_alone"), ("work", -0.1, "doc_drive"),
        ("orbit", -0.2, "doc_build"), ("trust", -0.2, "doc_drive"), ("check", -0.1, "doc_alone"), ("space", -0.3, "doc_hope"),
        ("end", -0.2, "doc_warm"), ("last", 0.0, "doc_warm_end"), ("end1", -0.6, "ending")]},
    "segments": ["hook", "girl", "naca", "orbit", "trust", "space", "end"],
    "extra_files": [],
    "workers": 2,   # 同時に書き出すブラウザの数（3 では起動直後に 3 つとも閉じた：超解像度・影 4096・地球の画像。2 に減らす）
    "qc_frames": [("t0", 0.3), ("lift", 0.6), ("cut", 0.5), ("girl", 1.0), ("count", 1.2), ("shapes", 0.8), ("campus", 1.0), ("naca", 1.2), ("room", 1.5),
                  ("west", 1.2), ("cafe", 1.5), ("work", 1.5), ("orbit", 1.0), ("path", 1.5), ("back", 1.0), ("team", 1.5), ("trust", 1.5), ("machine", 1.5),
                  ("ask", 2.0), ("check", 1.0), ("check", 4.0), ("quiet", 0.6), ("space", 1.5), ("wide", 1.5), ("ground", 2.0), ("end", 1.5), ("desk2", 1.5),
                  ("window", 1.5), ("last", 2.0)],
    "scenes": [
        ("1 冒頭（フック）", None, "girl", "夜明けの発射台：Atlas ロケットを見上げる → 点火、上昇（金属に朝日）→「女性の計算」で一瞬に暗い部屋、計算用紙を走る鉛筆の手もと（轟音が消え、鉛筆の音だけ）", "1 拍目から BGM doc_hook、轟音 → 鉛筆の音"),
        ("2 数字が好きだった少女", "girl", "naca", "机の女性の後ろ姿 → 1930 年代の町、階段を上る少女 → ノートの数字が図形に、図形が楕円に → 大学の黒板", "BGM doc_warm（やわらかな自然光）"),
        ("3 才能だけでは越えられない壁", "naca", "orbit", "1950 年代の研究所、計算室と卓上計算機 → 部門の札 → 人のいない食堂と奥のテーブルの札 → 計算を積み上げる手", "BGM doc_tense → doc_alone → doc_drive、寒色の室内光"),
        ("4 人間が宇宙へ向かう時代", "orbit", "trust", "計算用紙の曲線から宇宙へ → 地球の周りの軌道、帰還の地点へ下りる線 → 机に戻り、紙をめくる", "BGM doc_build、宇宙は深い黒と地球の青"),
        ("5 計算を託された瞬間", "trust", "space", "電子計算機の部屋（磁気テープ、出力の紙）→ 紙がキャサリンの机へ → 計算機を打つ手、ペン先が止まる → 手もとから顔へ寄る（間）", "BGM doc_drive → doc_alone（音数を減らし、計算機と鉛筆の音）、彩度を抑える"),
        ("6 地球を周回する宇宙船", "space", "end", "地球を回る Mercury カプセル。大気の層、雲、太陽光 → 宇宙船の周りから地球の全景へ → 地上の研究所へ戻る", "BGM doc_hope（長調の和音が差し込む）"),
        ("7 数字の向こうにいた人間", "end", "endcard", "地球へゆっくり寄る → 机の計算用紙にやわらかな光 → 窓辺の後ろ姿と空 → ゆっくり引いて暗転", "BGM doc_warm → doc_warm_end（余韻）、冷たい色から温かい光へ"),
        ("8 共通エンディング", "endcard", None, "リバース。世界の仕組みを、はじめから。", "BGM ending"),
    ],
    "plan_notes": [
        "## 演出の方針",
        "",
        "- 標準ルール v4：cine.js（映り込み・素材の凹凸とつや・光の筋と埃・超解像度 1.5 倍・動きのぶれ・光のにじみ）。字幕 1.2 倍、ロゴなし。",
        "- **決定的な映像**：L17〜L18 の地球を回る宇宙船。NASA の地球の画像（Visible Earth）に、昼夜の境目・海の反射・雲の層・大気の縁を自前のシェーダーで重ね、太陽光を受ける金属のカプセルの周りから地球の全景へカメラが回る。直前の「計算の確認」（音数を減らした静けさ）との対比で、BGM doc_hope の長調の和音が差し込む。",
        "- 人物は顔のない人形（実際の顔は描かない）。キャサリン：まとめ髪、1950〜60 年代の服。表情は作らず、手の動き・姿勢・カメラの寄りで見せる。",
        "- 人種隔離は、人のいない食堂のテーブルと札だけで示す（NASA の資料の記述の再現）。侮辱の場面やセリフは作らない。",
        "- 事実の範囲：グレンの言葉は本人の回想として伝聞で。電子計算機の機種・商標は描かない。彼女一人が飛行を支えたとは言わない。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
