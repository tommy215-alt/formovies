"""1 km メッシュ（国勢調査の 3 次メッシュ）の格子を作る。

出力 data/grid.npz：
  night  … 常住人口（2020 年国勢調査、e-Stat statsId T001140）
  day    … 昼間人口の推定（東京都は区市町村ごとの昼夜間人口比率、埼玉・千葉・神奈川は県の比率、ほかは 1）
  land   … 陸地（Natural Earth 10m の陸地＋人の住むメッシュ）
  isl    … 島の番号（陸地のつながり。海峡は橋・トンネルで別につなぐ）
格子の位置：row = 緯度×120 − ROW0、col = (経度−100)×80 − COL0（1 マスは 30 秒×45 秒、約 0.93×1.14 km）
"""
import csv, glob, json, os
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
ROW0, COL0 = 46 * 80, 28 * 80
NR, NC = 23 * 80, 19 * 80


def mesh_rc(code):
    code = str(code)
    r = int(code[0:2]) * 80 + int(code[4]) * 10 + int(code[6])
    c = int(code[2:4]) * 80 + int(code[5]) * 10 + int(code[7])
    return r - ROW0, c - COL0


def latlon_rc(lat, lon):
    return int(lat * 120) - ROW0, int((lon - 100) * 80) - COL0


def load_pop():
    night = np.zeros((NR, NC), np.float32)
    for f in glob.glob(os.path.join(D, "mesh", "*.txt")):
        with open(f, encoding="cp932", errors="replace") as fh:
            rd = csv.reader(fh)
            next(rd); next(rd)
            for row in rd:
                if not row or not row[0].isdigit() or len(row[0]) != 8:
                    continue
                v = row[4].strip()
                if not v.isdigit():
                    continue  # 秘匿（*）など
                r, c = mesh_rc(row[0])
                if 0 <= r < NR and 0 <= c < NC:
                    night[r, c] += int(v)
    return night


def day_factor():
    f = np.ones((NR, NC), np.float32)
    # 埼玉 87.6・千葉 88.3・神奈川 89.9（総務省統計局、2020 年、不詳補完値）
    for pref, ratio in (("11", 0.876), ("12", 0.883), ("14", 0.899)):
        with open(os.path.join(D, f"mesh{pref}.csv"), encoding="cp932") as fh:
            rd = csv.reader(fh); next(rd)
            for code, _, m in rd:
                r, c = mesh_rc(m)
                f[r, c] = ratio
    ratio = {}
    with open(os.path.join(D, "tj20zv0100.csv"), encoding="utf-8-sig") as fh:
        rd = csv.reader(fh); next(rd)
        for row in rd:
            if row[0] == "2" or (row[0] == "3"):
                try:
                    ratio[row[1]] = float(row[9]) / 100
                except ValueError:
                    pass
    with open(os.path.join(D, "mesh13.csv"), encoding="cp932") as fh:
        rd = csv.reader(fh); next(rd)
        seen = set()
        for code, _, m in rd:
            if m in seen or code not in ratio:
                continue  # 区境のメッシュは最初の区で
            seen.add(m)
            r, c = mesh_rc(m)
            if 0 <= r < NR and 0 <= c < NC:
                f[r, c] = ratio[code]
    return f, ratio


def land_mask(night):
    img = Image.new("L", (NC, NR), 0)
    dr = ImageDraw.Draw(img)
    gj = json.load(open(os.path.join(D, "ne_10m_land.geojson"), encoding="utf-8"))
    for feat in gj["features"]:
        g = feat["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            ring = poly[0]
            xs = [(lon - 100) * 80 - COL0 for lon, lat in ring]
            ys = [lat * 120 - ROW0 for lon, lat in ring]
            if max(xs) < 0 or min(xs) > NC or max(ys) < 0 or min(ys) > NR:
                continue
            dr.polygon(list(zip(xs, ys)), fill=1)
    land = np.array(img, bool) | (night > 0)
    return land


def label(land):
    """4 近傍でつながる陸地に番号（海峡の 1 マスの斜めのつながりは切る）。"""
    isl = np.zeros(land.shape, np.int32)
    n = 0
    for r0, c0 in zip(*np.nonzero(land)):
        if isl[r0, c0]:
            continue
        n += 1
        q = deque([(r0, c0)]); isl[r0, c0] = n
        while q:
            r, c = q.popleft()
            for dr_, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr_, c + dc
                if 0 <= rr < NR and 0 <= cc < NC and land[rr, cc] and not isl[rr, cc]:
                    isl[rr, cc] = n; q.append((rr, cc))
    return isl


if __name__ == "__main__":
    night = load_pop()
    f, ratio = day_factor()
    day = night * f
    land = land_mask(night)
    isl = label(land)
    np.savez_compressed(os.path.join(D, "grid.npz"), night=night, day=day, land=land, isl=isl)
    print("常住人口の合計", int(night.sum()), "昼間人口の推定の合計", int(day.sum()))
    print("新宿区の比率", ratio.get("13104"), "陸地のマス", int(land.sum()))
    for name, (lat, lon) in {"都庁": (35.6896, 139.6917), "下関": (33.957, 130.941), "門司": (33.945, 130.962),
                             "青森": (40.82, 140.74), "函館": (41.77, 140.73), "岡山": (34.66, 133.92),
                             "高松": (34.34, 134.05), "神戸": (34.69, 135.19), "淡路": (34.40, 134.85),
                             "徳島": (34.07, 134.55), "尾道": (34.41, 133.20), "今治": (34.07, 133.00)}.items():
        r, c = latlon_rc(lat, lon)
        print(name, "島", isl[r, c], "人口", int(night[r, c]))
    ids, cnt = np.unique(isl[isl > 0], return_counts=True)
    top = sorted(zip(cnt, ids), reverse=True)[:8]
    print("大きな島（マス, 番号）", top)
