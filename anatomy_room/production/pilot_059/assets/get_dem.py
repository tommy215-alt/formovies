#!/usr/bin/env python3
"""pilot_059 の標高データと衛星画像を落とす（登録・キー不要）。
標高：AWS Terrain Tiles（terrarium 形式の PNG、https://registry.opendata.aws/terrain-tiles/ 。中身は SRTM・GMTED2010・ETOPO1 など、USGS／NOAA のパブリックドメイン）
衛星画像：NASA Blue Marble（world.200412、パブリックドメイン）
    python assets/get_dem.py → assets/dem/<名前>.npy（標高 m の配列）と .json（範囲）、assets/photo/world.jpg"""
import io, json, math, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
UA = {"User-Agent": "reverse-pilot059/1.0"}


def tile_xy(lat, lon, z):
    n = 2 ** z; x = (lon + 180) / 360 * n; y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n; return x, y


def grab(name, lat, lon, z, half):
    """中心 (lat, lon) のまわり ±half タイルを集めて 1 枚に"""
    cx, cy = tile_xy(lat, lon, z); x0, y0 = int(cx) - half, int(cy) - half; N = 2 * half + 1
    H = np.zeros((N * 256, N * 256), np.float32)
    for j in range(N):
        for i in range(N):
            req = urllib.request.Request(URL.format(z=z, x=x0 + i, y=y0 + j), headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                a = np.asarray(Image.open(io.BytesIO(r.read())).convert("RGB"), np.float32)
            H[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    n = 2 ** z
    lon0 = x0 / n * 360 - 180; lon1 = (x0 + N) / n * 360 - 180
    lat0 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y0 + N) / n)))); lat1 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y0 / n))))
    np.save(HERE / "dem" / f"{name}.npy", H)
    (HERE / "dem" / f"{name}.json").write_text(json.dumps({"z": z, "lon": [lon0, lon1], "lat": [lat0, lat1], "shape": H.shape}), encoding="utf-8")
    print(name, H.shape, round(float(H.min())), round(float(H.max())), "lon", round(lon0, 3), round(lon1, 3), "lat", round(lat0, 3), round(lat1, 3))


if __name__ == "__main__":
    (HERE / "dem").mkdir(exist_ok=True); (HERE / "photo").mkdir(exist_ok=True)
    grab("everest", 27.988, 86.925, 11, 2)       # エベレストのまわり（約 100 km 四方、約 70 m ごと）
    grab("fuji", 35.361, 138.728, 11, 1)         # 富士山（同じ細かさ）
    grab("himalaya", 30.5, 84.0, 6, 2)           # ヒマラヤ全体（地図に重ねる形、約 3 km ごと）
    # 衛星画像は Wikimedia の "Whole world - land and oceans.jpg"（NASA Earth Observatory、PD、8192x4096）を curl で photo/world.jpg に（NASA のサーバーは応答しなかった）
