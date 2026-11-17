"""pilot_060「日本終末時計」の計算。真夜中（0 秒）＝日本の人が全員いなくなる。人口の 10 分の 1 を失うごとに 1 分近づく：
    秒 = 60 × log10(1 / 失った割合)
数字の出典は fact_check.md（記号）。python clock.py → clock.json"""
import json, math, pathlib

EV = [  # (記号, 年の表示, 出来事, 失った人, 当時の人口, メモ)
    ("H1", "737年", "天平の天然痘", None, None, "研究者の推計で人口の 25〜35%（100万〜150万人）。中央の 30% を使う"),
    ("H2", "1780年代", "天明の飢饉", 900_000, 30_000_000, "死者 90万人以上（目安）、当時の人口 約3,000万人（目安）"),
    ("H3", "1923年", "関東大震災", 105_000, 55_960_000, "死者・行方不明 約10万5千人、1920年国勢調査 5,596万人"),
    ("H4", "1945年", "戦争", 3_100_000, 71_930_000, "約310万人、1940年 7,193万人"),
    ("H5", "2011年", "東日本大震災", 22_325, 128_060_000, "死者 19,775＋行方不明 2,550、2010年国勢調査 1億2,806万人"),
    ("P1", "2070年", "人口減少（推計）", 126_150_000 - 87_000_000, 126_150_000, "2020年 1億2,615万人 → 2070年 約8,700万人（社人研 令和5年推計・中位）"),
    ("P2", "2120年", "人口減少（参考推計）", 126_150_000 - 49_730_000, 126_150_000, "2120年 約4,973万人（同 長期参考推計）"),
]
SHARE = {"H1": .30}


def sec(share):
    return 60 * math.log10(1 / share)


out = []
for k, yr, name, lost, pop, memo in EV:
    sh = SHARE.get(k, lost / pop if lost else None)
    out.append(dict(key=k, year=yr, name=name, lost=lost, pop=pop, share=round(sh, 6), sec=round(sec(sh), 1), sec_i=round(sec(sh)), memo=memo))
    print(f"{yr:8s} {name:12s} {sh*100:7.3f}%  残り {sec(sh):5.1f} 秒")
real = dict(year=2026, sec=85, memo="本物の終末時計（Bulletin of the Atomic Scientists、2026-01-27）")
pathlib.Path(__file__).with_suffix(".json").write_text(json.dumps(dict(events=out, real=real), ensure_ascii=False, indent=1), encoding="utf-8")
