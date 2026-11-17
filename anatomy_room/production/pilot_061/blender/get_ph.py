"""pilot_061 の 3D の素材（Poly Haven、すべて CC0）を assets/ph/ に落とす（git に入れない）。権利は scripts/pilot_061/assets.md。"""
import json, urllib.request
from pathlib import Path
OUT = Path(__file__).resolve().parents[1] / "assets" / "ph"; UA = {"User-Agent": "reverse-pilot061/1.0"}
HDRI = ["brown_photostudio_02", "studio_small_08"]
TEX = ["wood_table_001", "dark_wood", "brushed_concrete"]
def get(url, p):
    if p.exists() and p.stat().st_size: return
    p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()); print("got", p.name)
def files(pid): return json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.polyhaven.com/files/{pid}", headers=UA), timeout=60))
for h in HDRI:
    f = files(h); get(f["hdri"]["2k"]["hdr"]["url"], OUT / "hdri" / f"{h}_2k.hdr")
for t in TEX:
    try: f = files(t)
    except Exception as e: print("skip", t, e); continue
    for k, key in (("Diffuse", "diff"), ("nor_gl", "nor"), ("Rough", "rough")):
        if k in f: get(f[k]["2k"]["jpg"]["url"], OUT / "tex" / t / f"{key}.jpg")
