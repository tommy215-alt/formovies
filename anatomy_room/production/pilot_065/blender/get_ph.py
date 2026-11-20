"""pilot_065 の舞台の素材（Poly Haven、すべて CC0）を assets/ph/ に落とす（git に入れない）。権利は scripts/pilot_065/assets.md。"""
import json, urllib.request
from pathlib import Path
OUT = Path(__file__).resolve().parents[1] / "assets" / "ph"; UA = {"User-Agent": "reverse-pilot065/1.0"}
HDRI = ["modern_evening_street", "brown_photostudio_02", "studio_small_08", "hospital_room_2", "farm_sunset", "school_hall", "aarfontein_dirt_road", "hotel_rooftop_balcony", "ninomaru_teien", "canary_wharf", "potsdamer_platz", "modern_buildings_2", "lythwood_lounge", "stuttgart_suburbs", "courtyard", "sepulchral_chapel_rotunda", "large_corridor"]
TEX = ["wood_floor", "grass_ground", "marble_01", "dark_wood", "brushed_concrete", "floor_tiles_06", "raked_dirt", "park_dirt", "gravel_floor", "asphalt_02", "concrete_floor_02"]
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
