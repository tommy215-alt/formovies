"""yt_stats.js で保存した画面の文字から表を作る：日付・視聴回数・エンゲージビュー・視聴を継続・平均視聴時間・平均視聴割合・高評価・登録・ショートフィード・長さ・題名"""
import json, os, re, sys
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "publish", "stats", sys.argv[1])  # 日付のフォルダ
rows = json.load(open(os.path.join(D, "rows.json"), encoding="utf-8"))
def after(lines, key, n=1, start=0):
    for i in range(start, len(lines)):
        if lines[i].strip() == key: return lines[i + n].strip()
    return ""
out = []
for r in rows:
    f = os.path.join(D, r["id"] + "_tab-interest_viewers.txt")
    if not os.path.exists(f): continue
    E = open(f, encoding="utf-8").read().splitlines(); O = open(os.path.join(D, r["id"] + "_tab-overview.txt"), encoding="utf-8").read().splitlines()
    R = open(os.path.join(D, r["id"] + "_tab-reach_viewers.txt"), encoding="utf-8").read().splitlines()
    p = r["text"].split(" | "); title = p[1] if len(p) > 1 else ""
    date = re.search(r"(\d{4}/\d{2}/\d{2})", r["text"]); 
    iv = E.index("視聴者維持率を左右する重要なシーン") if "視聴者維持率を左右する重要なシーン" in E else 0
    feed = after(R, "ショート フィード")
    out.append(dict(id=r["id"], dur=p[0], date=date.group(1) if date else "", title=title[:42], views=after(O, "視聴回数"), engaged=after(E, "エンゲージ ビュー"),
                    keep=after(E, "視聴を継続", -1, iv), avgt=after(E, "平均視聴時間", 1), avgp=after(E, "平均視聴割合", -1), likes=after(O, "高評価数", 2), subs=after(O, "チャンネル登録者数"), feed=feed,
                    vis=" ".join(x for x in p if re.search("公開|予約|非公開", x))[:20]))
out.sort(key=lambda x: x["date"])
for x in out: print("\t".join(str(x[k]) for k in ("date", "views", "engaged", "keep", "avgt", "avgp", "likes", "subs", "feed", "dur", "title")))
json.dump(out, open(os.path.join(D, "stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
