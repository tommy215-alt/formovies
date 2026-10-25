"""Subtitles (SRT + styled ASS) from the narration timeline, plus on-screen titles / labels."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tl = json.load(open(os.path.join(ROOT, "assets", "audio", "timeline.json")))

HL = r"{\c&H3FD2FF&\fscx108\fscy108}"   # highlight: warm yellow, slightly larger
RS = r"{\r}"

# documentary labels: (start, end, style, text)  — style Label (top), Note (small), Title, Big
LABELS = [
    (0.25, 7.9, "Title", r"なぜ黒板は{\c&H6BD98A&}緑色{\r}なのか？"),
    (8.4, 12.8, "Label", "1800年ごろの教室（CG再現）"),
    (12.9, 17.1, "Note", "一人ひとりが小さな石板に書いては消して学んだ"),
    (20.55, 26.2, "Label", "19世紀初頭"),
    (26.4, 30.4, "Note", "壁掛けの大きな黒板で、全員に同じ図を見せる"),
    (30.6, 33.9, "Note", "※「最初の発明者」には諸説あります"),
    (44.3, 46.4, "Label", "天然の石の板（スレート）"),
    (46.4, 48.5, "Label", "黒く塗った木の板"),
    (48.8, 54.0, "Label", "木の板 ＋ 鉄板 ＋ ほうろう"),
    (50.8, 54.0, "Note", "ほうろう＝金属の表面にガラス質を焼き付けたもの"),
    (54.3, 59.2, "Label", "黒い塗装面　｜　緑のほうろう面"),
    (54.3, 59.2, "Note", "※同じ照明での比較イメージ"),
    (59.5, 65.8, "Label", "1954年　黒板のJIS規格（JIS S 6007）制定"),
    (70.5, 74.7, "Label", "黒板 → ホワイトボード → 電子黒板"),
    (79.25, 80.6, "Label", "石板の黒板"),
    (80.6, 82.2, "Label", "緑の黒板"),
    (82.2, 83.8, "Label", "ホワイトボード"),
    (83.8, 84.55, "Label", "電子黒板"),
    (91.3, 95.0, "Big", "身近なものの、\\N意外な歴史。"),
]


def fmt_srt(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def fmt_ass(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def plain(c): return c.replace("{", "").replace("}", "").replace("|", "")


def chunks():
    out = []
    for l in tl["lines"]:
        subs = l["subs"]; a, b = l["start"], l["end"]
        w = [max(2, len(plain(c))) for c in subs]; tot = sum(w)
        t = a
        for c, ww in zip(subs, w):
            d = (b - a) * ww / tot
            out.append((t, t + d, c)); t += d
    # keep each chunk up a little longer (until the next one starts, max +0.35 s)
    res = []
    for i, (s, e, c) in enumerate(out):
        nxt = out[i + 1][0] if i + 1 < len(out) else e + 0.6
        res.append((s, min(nxt - 0.02, e + 0.35), c))
    return res


def main():
    ch = chunks()
    with open(os.path.join(ROOT, "subtitles.srt"), "w") as f:
        for i, (s, e, c) in enumerate(ch, 1):
            text = c.replace("{", "").replace("}", "").replace("|", "\n")
            f.write(f"{i}\n{fmt_srt(s)} --> {fmt_srt(e)}\n{text}\n\n")
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Noto Sans CJK JP,64,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,-1,0,0,0,100,100,1,0,1,6,3,2,90,90,360,1
Style: Title,Noto Sans CJK JP,84,&H00FFFFFF,&H00FFFFFF,&H00141414,&HA0000000,-1,0,0,0,100,100,2,0,1,7,4,8,70,70,250,1
Style: Label,Noto Sans CJK JP,46,&H00F2F2F2,&H00FFFFFF,&H00202020,&H8C000000,-1,0,0,0,100,100,3,0,3,14,0,8,80,80,300,1
Style: Note,Noto Sans CJK JP,38,&H00E6E6E6,&H00FFFFFF,&H00151515,&H64000000,0,0,0,0,100,100,1,0,1,4,2,8,80,80,390,1
Style: Big,Noto Sans CJK JP,92,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,-1,0,0,0,100,100,4,0,1,6,3,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for s, e, c in ch:
        txt = re.sub(r"\{([^}]*)\}", lambda m: HL + m.group(1) + RS, c).replace("|", r"\N")
        ev.append(f"Dialogue: 2,{fmt_ass(s)},{fmt_ass(e)},Sub,,0,0,0,,{{\\fad(90,90)}}{txt}")
    for s, e, st, txt in LABELS:
        fx = r"{\fad(250,250)}" if st != "Big" else r"{\fad(600,0)\pos(540,820)}"
        ev.append(f"Dialogue: 1,{fmt_ass(s)},{fmt_ass(e)},{st},,0,0,0,,{fx}{txt}")
    open(os.path.join(ROOT, "work", "subs.ass"), "w").write(head + "\n".join(ev) + "\n")
    print(len(ch), "subtitle chunks")


if __name__ == "__main__":
    main()
