# pilot_047 の素材と権利（もしも設計）

> PD・CC0・CC BY（と互換の規約）だけ。本物の写真は使わない（CG と計算の地図だけ）。

## 効果音（pilot_046 と同じファイル。OpenGameArt・Freesound、すべて CC0）

- 壊れる・ぶつかる・ガラス・金属・木・爆発・地鳴り（`assets/sfx/break/`）：権利は `scripts/pilot_046/assets.md` のとおり（75 CC0 breaking / falling / hit sfx、100 CC0 SFX、Glass Break、Chunky Explosion、Crash Collision、Earthquake and open sesame、Dull Explosion）
- 時計の音・雑踏（`assets/sfx/clock.mp3`・`crowd.mp3`）：時計＝Clock ticking by Mortifreshman https://freesound.org/s/237210/ 、雑踏＝Generic Exterior Walla by brunoboselli https://freesound.org/s/634880/ （どちらも Freesound の CC0、pilot_045 と同じ）
- 空を切る音・湯気・低い衝撃は、production_script.py の中で合成（ノイズと正弦波）

## 地図とデータ

- 陸地：Natural Earth 10m の陸地（パブリックドメイン）。pilot_045 の `sim/data/ne_10m_land.geojson`
- 人の光・人数：総務省統計局「令和2年国勢調査」1 km メッシュ（e-Stat、pilot_045 の格子）、沖縄県「令和2年国勢調査結果（確報値）による補間補正人口」
- 地図の投影：都庁を中心にした正距方位図法（`production/pilot_047/blender/make_maps.py`）

## フォント

- BIZ UDPゴシック Bold（Morisawa、SIL OFL 1.1）。pilot_045 と同じ（`assets/fonts/OFL.txt`）

## 3D

- すべて Blender で自前に作った模式（都庁・議事堂・新宿の街は pilot_045 と同じ形、名古屋城・隕石・地球・月・火星は手続き的）。人物は顔のないピクトグラム。
