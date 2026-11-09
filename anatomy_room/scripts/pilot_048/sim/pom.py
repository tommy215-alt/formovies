"""pilot_048「東京に体長500mのポメラニアンが現れたら？」の計算。

方針：本物のポメラニアン（FCI の標準：体高 21 cm、体長＝体高の正方形の体つき、体重 2.5 kg）を、形も動き方もそのままに k 倍する。
- 長さ ×k、面積 ×k²、体積・重さ ×k³
- 時間は ×√k、速さも ×√k（動物の動きの似せ方：フルード数をそろえる。大きな動物ほどゆっくり動き、でも速い）
- 体がその重さに耐えられるか（骨の強さは ×k² しか増えない）は考えない（もしもの設定）。
数字はすべてこの 1 本から出す。元の値の出典と「目安」の区別は ../fact_check.md。
python pom.py → results.md・pom.json
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- 本物のポメラニアン（元の値）
DOG = dict(
    withers_m=0.21,        # 体高（FCI：21 cm ±3）。体長＝体高（AKC・FCI：正方形）
    mass_kg=2.5,           # 体重（AKC 3〜7 ポンド＝1.4〜3.2 kg、理想 4〜6 ポンド）
    eye_m=0.26,            # 目の高さ（目安：写真の比率から、体高の約 1.25 倍）
    paw_m=0.025,           # 前足の幅（目安：写真の比率から）
    pad_m=0.012,           # いちばん大きな肉球の幅（目安）
    coat_m=0.05,           # 体の上毛の長さ（目安。テディベアカット 2.5〜5 cm より長い）
    tidal_ml_kg=15.0,      # 1 回の息の量（犬 10〜20 mL/kg）
    breath_per_min=20.0,   # 安静時の呼吸（犬 10〜30 回/分）
    exhale_s=1.2,          # 吐く時間（目安）
    nostril_d_m=0.003,     # 鼻の穴の直径（目安）
    pant_per_min=300.0,    # ハァハァ（300〜400 回/分と言われる。少なめを使う）
    bark_db_1m=90.0,       # 吠える声の大きさ（1 m で 80〜100 dB と言われる。中ほど）
    walk_ms=1.1,           # 歩く速さ（目安：時速 4 km）
    run_ms=8.9,            # 全力で走る速さ（時速 20 マイル＝32 km/h と言われる）
    walk_km=1.5,           # 1 回の散歩の距離（目安：20〜30 分）
    zoomie_min=2.0,        # 急に走り回る「ハッスルタイム」の長さ（目安：1〜3 分）
    poop_g=20.0,           # 1 回のうんちの量（目安：1 日のフード約 65 g、うんちはその 45% ほどを 1〜2 回）
    poop_h_m=0.03,         # うんちの山の高さ（目安）
    pee_ml=20.0,           # 1 回のおしっこ（マーキング）の量（目安）
    leg_lift_m=0.10,       # マーキングで上げた足の高さ（目安）
    stride_hz_run=4.0,     # 走るときの 1 秒の歩数（目安）
    flight_m=0.02,         # 走るとき体が浮く高さ（目安）
    shake_hz=7.0,          # 体をブルブルする速さ（小型犬は 1 秒に 7 回ほど）
)
TARGET_LEN_M = 500.0       # 体長 500 m（ユーザーの条件）
k = TARGET_LEN_M / DOG["withers_m"]
sk = math.sqrt(k)

# ---------------------------------------------------------------- 比べるもの
TOKYO_DOME_M3 = 1.24e6     # 東京ドームの容積
POOL25_M3 = 25 * 12.5 * 1.2  # 25 m プール（12.5 m × 深さ 1.2 m の目安）
SKYTREE_M = 634.0
TOKYO_TOWER_M = 333.0
SOUND_MS = 340.0
WARD23_KM2 = 627.5         # 東京 23 区の面積（国土地理院）
WARD23_POP = 9_733_276     # 23 区の人口（令和 2 年国勢調査）
JP_MAX_GUST = 85.3         # 日本の観測史上最大の瞬間風速（m/s、1966 年 宮古島）
G = 9.81


def scaled():
    o = {}
    o["scale"] = k
    o["withers_m"] = DOG["withers_m"] * k
    o["eye_m"] = DOG["eye_m"] * k
    o["mass_t"] = DOG["mass_kg"] * k ** 3 / 1000
    o["mass_dome_water"] = DOG["mass_kg"] * k ** 3 / 1000 / TOKYO_DOME_M3   # 東京ドーム何杯分の水と同じ重さか
    o["paw_m"] = DOG["paw_m"] * k
    o["pad_m"] = DOG["pad_m"] * k
    o["coat_m"] = DOG["coat_m"] * k
    # 立っているとき前足 1 本にかかる重さ（前 60%）と、足の裏の圧力
    load = .3 * DOG["mass_kg"] * k ** 3 * G
    area = math.pi * (o["paw_m"] / 2) ** 2
    o["paw_mpa"] = load / area / 1e6
    # 息
    tv = DOG["tidal_ml_kg"] * 1e-6 * DOG["mass_kg"] * k ** 3          # m³
    o["breath_m3"] = tv
    o["breath_dome"] = tv / TOKYO_DOME_M3
    o["breath_every_s"] = 60 / DOG["breath_per_min"] * sk
    o["exhale_s"] = DOG["exhale_s"] * sk
    nos = 2 * math.pi * (DOG["nostril_d_m"] * k / 2) ** 2
    o["nostril_d_m"] = DOG["nostril_d_m"] * k
    o["breath_wind_ms"] = tv / o["exhale_s"] / nos
    o["pant_per_min"] = DOG["pant_per_min"] / sk
    # 鳴き声：声を出す面積が k² 倍 → 音の力も k² 倍。同じ大きさに聞こえる距離が k 倍になる
    o["bark_db_at"] = {f"{d}m": DOG["bark_db_1m"] - 20 * math.log10(d / k) for d in (100, 1000, 5000, 10000, 20000)}
    o["bark_90db_km"] = k / 1000
    # 歩く・散歩
    o["walk_kmh"] = DOG["walk_ms"] * sk * 3.6
    o["walk_km"] = DOG["walk_km"] * k
    o["walk_h"] = DOG["walk_km"] * 1000 / DOG["walk_ms"] * sk / 3600
    # うんち・おしっこ
    o["poop_t"] = DOG["poop_g"] * 1e-6 * k ** 3
    o["poop_m3"] = o["poop_t"] / 1.05
    o["poop_dome"] = o["poop_m3"] / TOKYO_DOME_M3
    o["poop_h_m"] = DOG["poop_h_m"] * k
    o["pee_m3"] = DOG["pee_ml"] * 1e-6 * k ** 3
    o["pee_pools"] = o["pee_m3"] / POOL25_M3
    o["leg_lift_m"] = DOG["leg_lift_m"] * k
    # 身震い
    o["shake_s"] = 1 / DOG["shake_hz"] * sk
    # 走る
    v = DOG["run_ms"] * sk
    o["run_ms"] = v
    o["run_kmh"] = v * 3.6
    o["run_mach"] = v / SOUND_MS
    o["stride_km"] = v / (DOG["stride_hz_run"] / sk) / 1000
    o["stride_every_s"] = sk / DOG["stride_hz_run"]
    # 着地 1 回で地面に入るエネルギー → 揺れ（地震に変わる割合 0.1% を仮定。log E = 1.5 M + 4.8）
    h = DOG["flight_m"] * k
    e = DOG["mass_kg"] * k ** 3 * G * h
    o["landing_J"] = e
    o["landing_M"] = (math.log10(e * 1e-3) - 4.8) / 1.5
    # 衝撃波（ソニックブーム）：Carlson（1978）の簡易式。地面を走るので、体からの距離 r で
    # Δp = Kr·√(pv·pg)·(M²−1)^(1/8)·r^(−3/4)·l^(3/4)·Ks、Kr=2、Ks=0.15（ずんぐりした形の目安）
    L = DOG["withers_m"] * 1.4 * k   # 鼻先から尻までの長さの目安
    def boom(r):
        return 2 * 101325 * (o["run_mach"] ** 2 - 1) ** (1 / 8) * r ** -.75 * L ** .75 * .15
    o["boom_pa"] = {f"{r}m": boom(r) for r in (500, 1000, 3000, 5000, 10000)}
    # 窓ガラスが割れ始める 1 kPa に下がる距離
    o["boom_glass_km"] = (2 * 101325 * (o["run_mach"] ** 2 - 1) ** (1 / 8) * L ** .75 * .15 / 1000) ** (4 / 3) / 1000
    # ハッスルタイム：犬の 2 分 → 人の時間で何分、何 km 走るか。踏みつぶす幅は体の幅（毛を含めて体高の約 0.8 倍の目安）
    o["zoomie_min"] = DOG["zoomie_min"] * sk
    o["zoomie_km"] = v * o["zoomie_min"] * 60 / 1000
    o["swath_m"] = .8 * DOG["withers_m"] * k
    o["zoomie_km2"] = o["zoomie_km"] * o["swath_m"] / 1000
    o["zoomie_vs_23ku"] = o["zoomie_km2"] / WARD23_KM2
    o["ward23_km2"] = WARD23_KM2
    o["ward23_pop"] = WARD23_POP
    o["gust_ratio"] = o["breath_wind_ms"] / JP_MAX_GUST
    return o


def fmt(o):
    L = ["# pilot_048 の計算結果（pom.py）", "", f"倍率 k = {k:,.0f}（時間・速さ ×{sk:.1f}）", ""]
    rows = [
        ("体高（肩の高さ）", f"{o['withers_m']:,.0f} m（東京タワー {TOKYO_TOWER_M:.0f} m）"),
        ("目の高さ", f"{o['eye_m']:,.0f} m（スカイツリー {SKYTREE_M:.0f} m とほぼ同じ）"),
        ("体重", f"{o['mass_t']/1e4:,.0f}万トン（東京ドーム {o['mass_dome_water']:.0f} 杯分の水と同じ重さ）"),
        ("前足の幅／肉球", f"{o['paw_m']:.0f} m／{o['pad_m']:.0f} m"),
        ("足の裏の圧力", f"{o['paw_mpa']:.0f} MPa（ふつうのコンクリートの強さ 20〜30 MPa を超える → めり込む）"),
        ("毛の長さ", f"{o['coat_m']:.0f} m"),
        ("1 回の息", f"{o['breath_m3']/1e4:,.0f}万 m³（東京ドーム {o['breath_dome']:.2f} 杯）、{o['breath_every_s']/60:.1f} 分に 1 回、吐くのに {o['exhale_s']:.0f} 秒"),
        ("鼻の穴／鼻息の風", f"直径 {o['nostril_d_m']:.0f} m／秒速 {o['breath_wind_ms']:.0f} m（日本の観測史上最大の瞬間風速 85.3 m/s の {o['gust_ratio']:.1f} 倍）"),
        ("ハァハァ", f"1 分に {o['pant_per_min']:.1f} 回"),
        ("鳴き声", "、".join(f"{d} 先 {v:.0f} dB" for d, v in o["bark_db_at"].items()) + f"（{o['bark_90db_km']:.1f} km 先で 90 dB＝電車の高架下くらい）"),
        ("歩く速さ", f"時速 {o['walk_kmh']:.0f} km"),
        ("いつもの散歩", f"{o['walk_km']:,.0f} km（{o['walk_h']:.0f} 時間）"),
        ("うんち 1 回", f"{o['poop_t']/1e4:.0f}万トン（東京ドーム {o['poop_dome']:.2f} 杯）、高さ {o['poop_h_m']:.0f} m"),
        ("おしっこ 1 回", f"{o['pee_m3']/1e4:.0f}万 m³（25 m プール {o['pee_pools']:,.0f} 杯）、足を上げる高さ {o['leg_lift_m']:.0f} m"),
        ("ブルブル 1 回", f"{o['shake_s']:.0f} 秒"),
        ("全力で走る", f"時速 {o['run_kmh']:,.0f} km（マッハ {o['run_mach']:.2f}）、一歩 {o['stride_km']:.1f} km・{o['stride_every_s']:.0f} 秒ごと"),
        ("着地 1 回の揺れ", f"{o['landing_J']:.1e} J → M{o['landing_M']:.1f}（地震に変わる割合 0.1% の仮定）"),
        ("衝撃波", "、".join(f"{d} 先 {v/1000:.1f} kPa" for d, v in o["boom_pa"].items()) + f"（窓ガラスが割れ始める 1 kPa は {o['boom_glass_km']:.1f} km 先まで）"),
        ("ハッスルタイム", f"犬の 2 分＝人の {o['zoomie_min']:.0f} 分。{o['zoomie_km']:,.0f} km 走り、幅 {o['swath_m']:.0f} m で {o['zoomie_km2']:,.0f} km² を踏む（23 区 {WARD23_KM2} km² の {o['zoomie_vs_23ku']:.1f} 倍）"),
    ]
    L += ["| 項目 | 結果 |", "|---|---|"] + [f"| {a} | {b} |" for a, b in rows]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    o = scaled()
    (HERE / "pom.json").write_text(json.dumps(dict(dog=DOG, k=k, out=o), ensure_ascii=False, indent=1), encoding="utf-8")
    md = fmt(o)
    (HERE / "results.md").write_text(md, encoding="utf-8")
    print(md)
