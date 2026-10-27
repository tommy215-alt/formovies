#!/usr/bin/env python3
"""pilot_011「紙袋を変えた女性、マーガレット・ナイト」（チャンネル「リバース」標準ルール v2）の制作スクリプト。

処理の本体は production/common/pipeline.py、標準の既定値は production/common/standard.py
（ロゴなし・BGM tech_drive・やわらかい効果音・冒頭 0.1 秒で話し始める）。ここには、この話だけの設定を書く。
使い方は pipeline.py の冒頭（python3 production_script.py all など）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
import pipeline  # noqa: E402
import standard  # noqa: E402

EP = standard.config({
    "id": "pilot_011",
    "out": "reverse_011_margaret_knight.mp4",
    # 映像と効果音のきっかけ：(セリフID, セリフ内の位置 0〜1)。renderer.html と同じ名前
    "cues": {
        "hook": ("L01", 0.0), "freeze": ("L01", 0.22), "split": ("L01", 0.32), "steal": ("L01", 0.6),
        "woman": ("L02", 0.0), "name": ("L02", 0.55),
        "mill": ("L03", 0.0), "loom": ("L04", 0.0), "girl": ("L05", 0.0), "shuttle": ("L06", 0.0), "guard": ("L06", 0.55),
        "bagshop": ("L07", 0.0), "envelope": ("L08", 0.0), "topple": ("L08", 0.62),
        "workshop": ("L09", 0.0), "steps": ("L09", 0.0), "feed": ("L09", 0.04), "cut": ("L09", 0.15), "fold": ("L09", 0.25), "bottom": ("L09", 0.36), "auto": ("L09", 0.6),
        "trial": ("L10", 0.0), "wood": ("L10", 0.62), "shop": ("L11", 0.0),
        "dispute": ("L12", 0.0), "annan": ("L12", 0.0), "claim": ("L13", 0.0), "hall": ("L14", 0.0), "quote": ("L15", 0.0),
        "evidence": ("L16", 0.0), "spread": ("L16", 0.72), "items": ("L17", 0.0), "witness": ("L17", 0.55),
        "patent": ("L18", 0.0), "machine": ("L19", 0.0), "mass": ("L19", 0.5), "improve": ("L20", 0.0),
        "today": ("L21", 0.0), "lift": ("L22", 0.0), "last": ("L23", 0.0),
    },
    # 効果音：やわらかい音色（music.sfx_bank_soft）。紙・機械・部屋の音は場面に限って控えめに。(効果音, きっかけ, 音量, ずらす秒)
    "sfx": [("deep", "t0", 0.6, 0.0), ("paper", "hook", 0.6, 0.2), ("tick", "freeze", 0.5), ("paper", "split", 0.6), ("impact", "steal", 0.9), ("sweep_down", "steal", 0.3, 0.05),
            ("room", "woman", 0.6, -0.3),
            ("loom", "mill", 0.7), ("loom", "loom", 0.9), ("loom", "girl", 0.7), ("loom", "shuttle", 0.8), ("tick", "guard", 0.5),
            ("paper", "bagshop", 0.6, 0.5), ("paper", "envelope", 0.5), ("hit", "topple", 0.45, 0.35),
            ("paper", "feed", 0.6), ("cut", "cut", 0.8), ("paper", "fold", 0.6), ("tick", "bottom", 0.5), ("machine", "auto", 0.7),
            ("paper", "trial", 0.5, 0.3), ("tick", "wood", 0.45), ("gear", "shop", 0.6), ("machine", "shop", 0.45, 0.4),
            ("deep", "annan", 0.5), ("paper", "claim", 0.5, 0.2), ("room", "hall", 0.8), ("deep", "quote", 0.35),
            ("unroll", "spread", 0.9, -0.3), ("tick", "items", 0.4), ("tick", "witness", 0.35), ("step", "witness", 0.5, 0.2),
            ("paper", "patent", 0.6, 0.1), ("impact", "patent", 0.5, 0.5), ("machine", "machine", 0.8), ("gear", "mass", 0.6),
            ("sweep_up", "improve", 0.4, -0.2), ("sweep_down", "today", 0.4, -0.2), ("paper", "lift", 0.6, 0.2), ("deep", "last", 0.4)],
    # BGM：tech_drive（124 BPM）。(きっかけ, ずらす秒, モード)。エンディングは end1 の少し前から
    "music": {"sections": [
        ("t0", 0.0, "doc_hook"), ("mill", -0.1, "doc_drive"), ("bagshop", -0.1, "doc_drive"), ("steps", -0.1, "doc_build"),
        ("annan", -0.2, "doc_break"), ("hall", -0.1, "doc_build"), ("quote", 0.0, "doc_break"), ("evidence", -0.1, "doc_peak"),
        ("patent", -0.2, "doc_drive"), ("machine", 0.0, "doc_build"), ("today", -0.2, "doc_outro"), ("end1", -0.6, "ending")]},
    "segments": ["hook", "mill", "bagshop", "workshop", "dispute", "patent", "today"],
    "extra_files": [],
    "qc_frames": [("t0", 0.4), ("freeze", 0.5), ("steal", 0.6), ("name", 1.0), ("mill", 1.0), ("girl", 1.2), ("guard", 0.8), ("bagshop", 1.5),
                  ("topple", 0.8), ("feed", 0.3), ("bottom", 0.5), ("auto", 1.5), ("wood", 1.0), ("shop", 1.5), ("annan", 1.5), ("claim", 1.5),
                  ("hall", 1.5), ("quote", 1.5), ("spread", 0.5), ("items", 2.0), ("witness", 1.5), ("patent", 1.5), ("mass", 1.0),
                  ("improve", 1.5), ("today", 1.5), ("lift", 2.0), ("last", 2.0)],
    "scenes": [
        ("1 冒頭（フック）", None, "mill", "現代の店：手が紙袋の口をつまむ → 静止 → 輪郭の線と「平らな紙 → 筒 → 底」の図 →「盗まれかけた」で 19 世紀の机：設計図を奥の手が引っぱる → 引くと、窓を背にした女性のシルエット", "1 拍目から BGM doc_hook、紙の音、引っぱる瞬間に低い impact"),
        ("2 綿の工場", "mill", "bagshop", "れんがの工場、並ぶ織機と天井の回転軸、窓の光。織機を見上げる低い視点。織機の間の少女。杼の動きと、止める仕組みの線", "織機の規則的な音／BGM doc_drive"),
        ("3 紙袋の工場", "bagshop", "workshop", "作業台で袋を折る女性たち。封筒型の袋に物を入れると倒れる", "紙の音、やわらかい打音"),
        ("4 機械を考える", "workshop", "dispute", "送る → 切る → 折る → 底を作る（模式）→ 機械全体。夜の机：線が増える設計図、くしゃくしゃの紙、試作の袋、木の模型。ボストンの機械工場で組み上がる機械", "紙・刃・機械の音／BGM doc_build"),
        ("5 発明を奪われかける", "dispute", "patent", "機械の奥に男のシルエット（山高帽）。申請書類がすべる。長い机の手前にナイト、奥にアナン。主張の場面はアナンへ寄る。設計図を広げ、日誌・模型が並ぶ。後ろに証言した人たち", "BGM doc_break → doc_build → doc_break（主張）→ doc_peak（証拠）、部屋の空気、設計図を広げる音"),
        ("6 特許", "patent", "today", "設計図の上に特許の書類（No.116,842, July 11, 1871）。機械がゆっくり → 速く、紙袋が次々に出る。その後の改良（模式）", "BGM doc_drive → doc_build、機械と歯車の音"),
        ("7 現代へ", "today", "endcard", "冒頭と同じ構図の店。手が袋の口をつまみ、商品を入れる。紙袋を持って歩く人の後ろ姿", "BGM doc_outro"),
        ("8 共通エンディング", "endcard", None, "リバース。世界の仕組みを、はじめから。", "BGM ending"),
    ],
    "plan_notes": [
        "## 演出の方針",
        "",
        "- 標準ルール v2：暗めのテック調、左上のロゴなし、注記は人物と場面の再現であることを最初の歴史の場面で 1 回だけ。BGM は tech_drive（124 BPM）、声は v7。",
        "- 主役は紙袋ではなく、マーガレット・ナイト。人物は顔のない人形（実際の顔は描かない）。ナイト：まとめ髪・青灰色の長いドレス。アナン：山高帽と暗い上着（悪役の誇張はしない）。",
        "- 縦長の画面に合わせ、向かい合う二人は奥行き方向に置く（肩越し）。手もとのアップで「引っぱられる設計図」「並ぶ証拠」を見せる。",
        "- 事実の範囲：審理の場は「法廷」と書かない。アナンの主張は「〜という」（伝聞）。1871 年の特許だけを扱い、1879 年の改良特許と混同しない。",
    ],
})

if __name__ == "__main__":
    pipeline.main(__file__, EP)
