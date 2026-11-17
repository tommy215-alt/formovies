"""pilot_060「イエスを言い続けたら、一週間」の計算。出典つきの数字（S）と、この動画の仮定（A）を分ける。fact_check.md と同じ記号。
python yes_week.py → yes_week.json"""
import json, pathlib

S = dict(nomikai=4237,                  # S1 飲み会 1 回の平均（Money Campus、20〜50 代 1,000 人）
         scam_yen=1272e8, scam_n=10237,  # S2 SNS 型投資・ロマンス詐欺 2024 年の被害額・件数（警察白書 令和 7 年版）
         fitd_yes=.76, fitd_cold=.17,    # S3 Freedman & Fraser 1966：小さなお願いのあとの大きなお願い 76%、いきなり 17%
         cooling_days=8)                 # S4 訪問販売・電話勧誘販売のクーリング・オフ 8 日間（特定商取引法）
A = dict(bag=5, oomori=150, hosho=1980, sub_month=3980, kifu=1000, sake2=4237)   # A：この動画の仮定（円）

days = [  # (曜日, イエスの中身, 円)
    ("月", "レジ袋", A["bag"]), ("月", "今夜飲みに行こう", S["nomikai"]),
    ("火", "大盛りにしますか", A["oomori"]), ("火", "延長保証つけますか", A["hosho"]),
    ("水", "電話でお得なプラン（月額）", A["sub_month"]),
    ("木", "署名だけでも → 寄付も", A["kifu"]),
    ("金", "必ず増える投資", round(S["scam_yen"] / S["scam_n"])),
    ("土", "二次会も行こう", A["sake2"]),
]
total = sum(y for _, _, y in days)
out = dict(days=days, total=total, scam_avg=round(S["scam_yen"] / S["scam_n"]), before_scam=sum(y for d, _, y in days if d != "金"), **S, **A)
pathlib.Path(__file__).with_suffix(".json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: out[k] for k in ("total", "scam_avg", "before_scam")}, ensure_ascii=False))
