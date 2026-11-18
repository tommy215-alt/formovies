"""pilot_060 v5 の場面ごとの舞台の素材（Poly Haven、すべて CC0）を assets/ph/ に落とす（git に入れない）。権利は scripts/pilot_060/assets.md。"""
import json, urllib.request
from pathlib import Path
OUT = Path(__file__).resolve().parents[1] / "assets" / "ph"; UA = {"User-Agent": "reverse-pilot060/1.0"}
HDRI = ["kloofendal_overcast", "industrial_sunset", "approaching_storm", "misty_dawn", "urban_street_01", "modern_evening_street"]
TEX = ["japanese_cedar_planks", "clay_plaster", "mud_cracked_dry_03", "brown_planks_07", "rubble", "brick_wall_001",
       "burned_ground_01", "cracked_concrete_wall", "damp_beach_sand", "precast_concrete_wall", "concrete_tiles_02", "concrete_tile_facade",
       "floor_tiles_06", "plastered_wall"]
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
