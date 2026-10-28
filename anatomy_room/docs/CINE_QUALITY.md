# 映像品質（シネマティック）の仕組みと、GPU の使い方

2026-10-28、ユーザーの指示「REVERSE 映像品質アップグレード指示」で調べ、作ったもの。標準ルール v4（`templates/REVERSE_STANDARD_RULES.md`）の「映像品質」の実体。

## 1. 制作環境の調査結果（ユーザーの PC、実測）

| 項目 | 結果 |
|---|---|
| GPU | NVIDIA GeForce RTX 3070、VRAM 8 GB（待機時の使用 約 1 GB）、ドライバ 610.88 |
| 描画 | three.js r149（`common/vendor/three.min.js`）を Chromium（Playwright）の WebGL2 で。ANGLE 経由の Direct3D11 で **GPU が実際に使われている**（`render_frames.js` が起動時に表示） |
| WebGL2 の上限 | テクスチャ 16384、MSAA 8 サンプル、半精度・浮動小数の描画先あり、異方性フィルタ 16 |
| three.js r149 で使える | PMREM（周りの光の映り込み）、MeshPhysicalMaterial（透過・屈折・布の光沢・クリアコート）、半精度の描画先、影（PCF・VSM）、インスタンス描画。**使えない**：EffectComposer・SSAO・UnrealBloom など examples の部品（vendor に入っていない）→ 光のにじみは 2D の GPU フィルタで代用 |
| 1 コマの時間（pilot_012、従来の描画） | WebGL の描画 36〜160 ms（最初の 1 コマはシェーダーのコンパイルで 0.6 秒）、**画面の撮影（PNG）0.3〜0.6 秒が大半** |
| 動画の書き出し | ffmpeg の libx264（CPU）、CRF 18、1080×1920、30fps。ffmpeg は h264_nvenc・hevc_nvenc・av1_nvenc（GPU の書き出し）も使える。今は書き出しが律速ではないので変えていない |

**GPU で速くなる／ならない**：3D の描画（光・影・素材・超解像度・動きのぶれの複数回描画）は GPU。画面の撮影（PNG の作成と受け渡し）・2D の文字・音声合成（VOICEVOX）・BGM の合成（numpy）は GPU では速くならない。

## 2. 作ったもの：`production/common/cine.js`（新しい回だけが読み込む）

| 機能 | 何が良くなるか | 負荷 |
|---|---|---|
| `Cine.init` / `Cine.useEnv(scene, "cold"・"warm"・"studio"・"lamp", 強さ)` | 周りの光の映り込み（IBL）。金属・陶器・水・つやのある面に、場面の光（冷たい窓・暖かい光・ランプ・明るい室内）が映る | 起動時に 1 回（PMREM 4 種） |
| `Cine.surface(材質, 種類, {repeat, normal})` | 凹凸（法線）と、つや・ざらつき（ラフネス）の地図を手続き的に作って足す：wood・stone・plaster・fabric・metal（細かい傷）・paper・skin・porcelain | 地図は起動時に作ってキャッシュ |
| `Cine.water()` / `Cine.glass()` | 透過・屈折する水とガラス（屈折率 1.33／1.5、厚み、吸収の色） | 透過の追加描画 1 回 |
| `Cine.shaft({from, to, r0, r1, color, opacity})` | 差し込む光の筋。縁と先がやわらかく消え、空気のむらでゆっくり揺らぐ | 小さい |
| `Cine.dust({min, max, count})` | 光の中の埃。種つきで、時刻だけで位置が決まる（並列に描いても同じ） | 小さい |
| `Cine.motionBlur(ctx, t, {n, shutter}, draw)` | 動きのぶれ。1 コマの露光（1/60 秒＝シャッター 180°）の間に n 回描いて平均 | 描画 × n |
| `Cine.bloom(ctx, 強さ)` | 明るい所（窓・ランプ・水の反射）だけをにじませる | 小さい（2D、1/4 の大きさ） |

各話の renderer では、さらに次をする（pilot_012 の `renderer_cine.html` が見本）：
- **超解像度**：WebGL を 1.5 倍（1620×2880）で描き、縮めて重ねる（`SS = 1.5`）。影の地図は 4096。
- 被写界深度（DOF）の透明な層には、加算の光の筋と埃を描かない（不透明な暗い色として残り、画面全体を覆った。pilot_012 の試作で発生）。
- 光の筋・埃・映り込みの切り替えは、場面の感情に合わせる（`atmos(t, name)`）。

## 3. 負荷の実測（pilot_012、同じ 16 コマの静止画）

| 版 | 1 コマ | 内容 |
|---|---|---|
| 従来（renderer.html） | 0.66〜0.74 秒 | |
| シネマティック（renderer_cine.html） | 0.85〜1.01 秒 | 超解像度 1.5 倍＋動きのぶれ 3 回＋映り込み＋凹凸の地図＋光の筋と埃＋光のにじみ |

約 1.3〜1.4 倍。全編 3,000 コマなら、3 並列で約 25 分 → 約 35 分の見込み（全編ではまだ測っていない）。VRAM は 8 GB のうち描画中も余裕がある（待機 約 1 GB）。

## 4. 使い方（新しい回）

1. renderer.html に `<script src="../common/cine.js"></script>` を足す（stage.js のあと）。
2. 場面を組み立てたあとで `Cine.init(THREE, R)`、材質に `Cine.surface(...)`、水・ガラスは `Cine.water()`・`Cine.glass()`。
3. 決定的な場面に光の筋と埃。毎コマ `atmos(t, name)` で強さ・色・映り込みを決める。
4. `renderFrame` で `Cine.motionBlur(bg, t, {n: 3, shutter: 1/60}, tk => drawScene(tk, S.sceneAt(tk)))`、色調のあとに `Cine.bloom(bg, k)`。
5. 比較は `node ../common/render_frames.js --dir . --renderer <ファイル> --stills …`（静止画）と `--clip 58,67 out.mp4`（短い映像、音なし）。

## 5. まだできていないこと・今後の案

- 画面全体の陰影（SSAO）・本物の体積光（レイマーチング）：three.js の examples の部品がないため未実装。自前のシェーダーで書けば可能（負荷は増える）。
- 人物は顔のない人形のまま。肌と服の質感は上がったが、形（シルエット）・手の造形は変えていない。人物の表現（視線・手の動き・姿勢）を上げるには、人形の関節と手の形を作り直す必要がある。
- 液体の飛沫・煙の物理シミュレーションはない（粒子は手続き的な動き）。
- 書き出しの画質：YouTube に上げる前提なら CRF 16・`-tune film` も候補（ファイルは大きくなる）。NVENC は速いが、同じ大きさなら libx264 のほうが画質が良い。
- 画面の撮影（PNG）が律速。WebGL の画素を直接 ffmpeg に渡せれば 1 コマ 0.3 秒ほど縮む見込み（未検証）。
