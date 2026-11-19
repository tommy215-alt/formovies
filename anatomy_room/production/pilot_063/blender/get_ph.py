"""pilot_062 の舞台の素材（Poly Haven、すべて CC0）を assets/ph/ に落とす（git に入れない）。権利は scripts/pilot_062/assets.md。"""
import json, urllib.request
from pathlib import Path
OUT = Path(__file__).resolve().parents[1] / "assets" / "ph"; UA = {"User-Agent": "reverse-pilot062/1.0"}
HDRI = ["stadium_01", "orlando_stadium", "meadow_2"]
TEX = ["running_track", "grass_ground", "raked_dirt", "park_dirt", "wood_floor"]
def get(url, p):
    if p.exists() and p.stat().st_size: return
    p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()); print("got", p.name, flush=True)
def files(pid): return json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.polyhaven.com/files/{pid}", headers=UA), timeout=60))
for h in HDRI:
    f = files(h); get(f["hdri"]["2k"]["hdr"]["url"], OUT / "hdri" / f"{h}_2k.hdr")
for t in TEX:
    try: f = files(t)
    except Exception as e: print("skip", t, e); continue
    for k, key in (("Diffuse", "diff"), ("nor_gl", "nor"), ("Rough", "rough")):
        if k in f: get(f[k]["2k"]["jpg"]["url"], OUT / "tex" / t / f"{key}.jpg")
        else: print("missing", t, k)
