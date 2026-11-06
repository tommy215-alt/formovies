"""国勢調査（e-Stat 統計地図、statsId T001140）の 1 km メッシュ人口を、日本の主な島の範囲で取る。"""
import io, os, sys, zipfile, urllib.request, concurrent.futures as cf

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
URL = "https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001140&code={}&downloadType=2"

def get(code):
    path = os.path.join(OUT, f"{code}.txt")
    if os.path.exists(path):
        return code, "cached"
    try:
        with urllib.request.urlopen(URL.format(code), timeout=60) as r:
            data = r.read()
        z = zipfile.ZipFile(io.BytesIO(data))
        name = [n for n in z.namelist() if n.endswith(".txt")][0]
        open(path, "wb").write(z.read(name))
        return code, "ok"
    except zipfile.BadZipFile:
        return code, "none"
    except Exception as e:
        return code, f"err {e}"

codes = [f"{a}{b}" for a in range(46, 69) for b in range(28, 47)]
with cf.ThreadPoolExecutor(6) as ex:
    res = list(ex.map(get, codes))
ok = [c for c, s in res if s in ("ok", "cached")]
err = [(c, s) for c, s in res if s.startswith("err")]
print("ok", len(ok), "none", sum(s == "none" for _, s in res), "err", err[:5])
