#!/usr/bin/env python3
"""pilot_010「世界の果てに、空を飛べない小さな鳥がいる」（チャンネル「リバース」科学ドキュメンタリー形式）の制作スクリプト。

処理の本体は production/common/pipeline.py。ここには、この話だけの設定（きっかけ・効果音・BGM の構成・場面）を書く。
使い方は pipeline.py の冒頭（python3 production_script.py all など）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
import pipeline  # noqa: E402

EP = {
    "id": "pilot_010",
    "out": "reverse_010_inaccessible_rail.mp4",
    "logo": True,   # 左上の固定ロゴ（この回は表示していた。2026-10-27 以降の新作の標準は表示しない）
    # 映像と効果音のきっかけ：(セリフID, セリフ内の位置 0〜1)。renderer.html と同じ名前
    "cues": {
        "hook": ("L01", 0.0), "glimpse": ("L01", 0.55), "only": ("L02", 0.0), "lean": ("L02", 0.5),
        "globe": ("L03", 0.0), "pin": ("L04", 0.3),
        "aerial": ("L05", 0.0), "cliff": ("L05", 0.15), "name": ("L05", 0.65), "grass": ("L06", 0.0),
        "ground": ("L07", 0.0), "rustle1": ("L07", 0.6),
        "bird": ("L08", 0.0), "size": ("L09", 0.0), "macro": ("L09", 0.35), "smallest": ("L10", 0.0), "chase": ("L10", 0.55),
        "evo": ("L11", 0.0), "dna": ("L12", 0.0), "arc": ("L12", 0.45), "arrive": ("L13", 0.35), "unknown": ("L14", 0.0),
        "wing": ("L15", 0.0), "feathers": ("L15", 0.5), "islands": ("L16", 0.0), "factors": ("L17", 0.0), "factor2": ("L17", 0.35),
        "caveat": ("L18", 0.0), "nod": ("L18", 0.4),
        "alone": ("L19", 0.0), "edge": ("L20", 0.0), "boat": ("L21", 0.0), "iucn": ("L21", 0.55),
        "outro": ("L22", 0.0), "rise": ("L22", 0.5), "last": ("L23", 0.0),
    },
    # 効果音：やわらかい音色（music.sfx_bank_soft）。自然の音（波・風・草）は映像の動きに合わせて控えめに
    "sfx_bank": "soft",
    "sfx": [("deep", "t0", 0.8, 0.0), ("waves", "t0", 0.9, 0.0), ("wind", "t0", 0.6, 1.2), ("waves", "hook", 0.7, 4.5),
            ("sweep_up", "globe", 0.5, -0.2), ("tick", "pin", 0.6),
            ("sweep_down", "aerial", 0.5, -0.2), ("wind", "cliff", 0.7), ("wind", "grass", 0.6, 0.6),
            ("rustle", "rustle1", 0.8), ("rustle", "bird", 0.7, -0.3), ("deep", "bird", 0.5), ("step", "size", 0.7, 0.4), ("step", "macro", 0.6, 1.0),
            ("rustle", "chase", 0.8), ("step", "chase", 0.5, 0.2),
            ("sweep_up", "evo", 0.4, -0.2), ("scan", "arc", 0.4), ("tick", "arrive", 0.5), ("tick", "unknown", 0.4),
            ("rustle", "wing", 0.5), ("tick", "islands", 0.4), ("tick", "factors", 0.4), ("tick", "factor2", 0.4),
            ("sweep_down", "alone", 0.5, -0.2), ("waves", "alone", 0.8, 0.2), ("wind", "edge", 0.6), ("tick", "iucn", 0.45),
            ("rustle", "outro", 0.6, 0.3), ("wind", "rise", 0.6), ("waves", "last", 0.7), ("deep", "last", 0.5, 1.0)],
    "sfx_duck": 0.7,   # セリフ中は効果音を 0.7 倍に
    "music_lp": 5000,  # BGM の高音を丸める（Hz）
    # BGM：tech_deep（100 BPM、ニ短調）。(きっかけ, ずらす秒, モード)。エンディングは自動
    "music": {"style": "tech_deep", "sections": [
        ("t0", 0.0, "ambient"), ("globe", -0.2, "pulse"), ("ground", 0.0, "ambient"), ("bird", -0.1, "rise"), ("evo", 0.0, "pulse"),
        ("wing", 0.0, "ambient"), ("alone", 0.0, "pulse"), ("outro", 0.0, "rise"), ("last", 0.5, "ambient")]},
    # 場面ごとに映像を書き出して保存する区切り
    "lead_in": 0.15,  # 0 秒から問いかけ（映像は暗い海から）
    "segments": ["hook", "globe", "aerial", "ground", "bird", "evo", "wing", "alone", "outro"],
    "extra_files": [],
    "qc_frames": [("t0", 0.3), ("t0", 1.5), ("glimpse", 0.3), ("lean", 0.5), ("globe", 1.0), ("pin", 0.8), ("cliff", 1.0), ("grass", 1.0),
                  ("rustle1", 0.5), ("bird", 0.8), ("macro", 0.8), ("chase", 0.6), ("arc", 1.0), ("unknown", 0.8), ("feathers", 0.8),
                  ("factor2", 1.0), ("nod", 0.5), ("alone", 1.0), ("edge", 1.0), ("iucn", 0.8), ("rise", 1.0), ("last", 1.5)],
    "scenes": [
        ("1 冒頭の問い", None, "globe", "暗い海を低く飛び、巨大な断崖を上昇。霧の中の島の輪郭。草陰に鳥の影が一瞬。崖上の岩にオモテ（島を見下ろし、乗り出す）", "低い音、波、風／BGM ambient"),
        ("2 地球から島へ", "globe", "aerial", "地球の俯瞰 → 南大西洋 → 島の位置の印と地名", "控えめなスイープ／BGM pulse"),
        ("3 近づけない島", "aerial", "ground", "島の空撮。高さ 300 m ほどの崖に沿って回り込み、崖の上の草地へ降りる", "風／BGM pulse"),
        ("4 草の根もと", "ground", "bird", "低い視点で背の高い草の間を進む。葉が揺れる", "草のそよぎ／BGM ambient"),
        ("5 鳥の登場", "bird", "evo", "イナクセシブルクイナが姿を現す。マクロ（くちばし・赤い目・羽毛・脚）。オモテの足との対比。草むらへ入る鳥を、オモテが前のめりに追う", "小さな足音／BGM rise"),
        ("6 祖先と到達", "evo", "wing", "暗い空間の地球儀。南アメリカから島への弧（※経路はイメージ）、DNA のらせん（※イメージ）、「約150万年前（推定）」「渡り方：不明」", "／BGM pulse"),
        ("7 翼と、飛ぶ力を失う理由", "wing", "alone", "小さな翼と毛のような羽のマクロ。世界各地の島（※位置はイメージ）。二つの要因と注記。オモテがうなずく", "／BGM ambient"),
        ("8 この島だけ", "alone", "outro", "海に囲まれた小さな島の俯瞰。崖の縁のオモテの後ろ姿、遠くの船の影（※イメージ）。IUCN：危急種", "波、風／BGM pulse"),
        ("9 結末", "outro", "endcard", "鳥が草むらの奥へ消え、オモテが姿勢を正す。カメラが上昇し、広い海と小さな島", "風、波／BGM rise → ambient"),
        ("10 共通エンディング", "endcard", None, "リバース。世界の仕組みを、はじめから。", "BGM を下げる"),
    ],
    "plan_notes": [
        "## 演出の方針",
        "",
        "- 世界観：暗く洗練された科学ドキュメンタリー。ベースはダークネイビー／チャコール、アクセントはシアン／アイスブルー。自然の場面は緑・土・岩の色を自然に見せる。",
        "- 3D：three.js の一つの場面に、海・島（高さのある地形）・草の株（インスタンス）・鳥・オモテを置き、霧（FogExp2）・リムライト・影で奥行きを出す。被写界深度は、焦点の手前／奥を別に描いてぼかして重ねる（3 回描画）。",
        "- オモテ：顔のない、もちもちした人型ピクトグラム（stage.js の mochi3D）。表情は使わず、体の傾き・うなずき・乗り出し・硬直と、立体の汗のしずくで演技する。話さない。",
        "- 鳥：上面は暗い栗色、下面は暗い灰色に白く細い横じま、赤い目、黒いくちばしと脚、小さな翼（資料の記述に合わせた再現。※再現 CG）。鳴き声は使わない（本物の録音を確認できないため）。",
        "- 文字：日本語だけ。地名・数値は事実確認したものだけ。経路・DNA・船の影は「※イメージ」、鳥の CG は「※再現CG」。",
    ],
}

if __name__ == "__main__":
    pipeline.main(__file__, EP)
