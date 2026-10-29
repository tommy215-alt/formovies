# pilot_017：事実確認リスト（宇宙の物差し——ヘンリエッタ・スワン・リービット）

調査日：2026-10-29（ユーザーの PC のセッション）。確認方法の定義は `docs/FACT_CHECK_POLICY.md`。

**確認の流れ**：ChatGPT の報告（`gpt_fact_check_prompt.md` の依頼文への回答、2026-10-29）を下書きにし、Claude が主な出典に当たり直した。項目ごとに「Claude が本文を読んだ」「WebFetch（本文を取得し、小さなモデルが質問に沿って抜き出す方法。全文を一字一句は読んでいない）」「検索の抜粋のみ」「ChatGPT の報告のみ」を分ける。

## 物語の核（ガイドライン v2.1 の 5）

- **問題**：暗く見える星が、遠いからなのか、もともと暗いからなのかを見分ける方法がなかった（遠い星の距離は測れない）。
- **困難**：天文台で働く女性たちは望遠鏡の操作を許されず、写真乾板を調べる仕事をしていた（S2）。本人は 17 歳ごろから聴力が落ち（S2）、病気で何度も仕事を離れた（1897〜1902 ごろ、1908 年末〜1910 年 5 月、1913 年に約 3 か月。S3）。
- **本人がしたこと**：マゼラン雲の変光星 1777 個の一覧をまとめ（1908）、明るい変光星ほど周期が長いことに気づいた。1912 年、25 個の星で、周期の対数と明るさがまっすぐな線に乗ることを示し、「星はほぼ同じ距離にあるので、周期は本当の明るさと結びついている」と書いた（S1、Claude が原論文を読んだ）。
- **何が変わったか**：のちの天文学者たちがこれを距離の物差しにし、1923 年にハッブルがアンドロメダの変光星を見つけて、銀河系の外に別の銀河があることを示した（S5）。本人は 1921 年に亡くなっていた。1925 年、推薦を考えた数学者の手紙が届いたが、本人はもういなかった（S3）。
- **現在**：セファイド変光星は、宇宙の膨張の速さ（ハッブル定数）を測る距離の基準に使われている（S4）。

## 出典

| ID | 資料 | URL | 確認方法 |
|---|---|---|---|
| S1 | Leavitt & Pickering「Periods of 25 Variable Stars in the Small Magellanic Cloud」Harvard College Observatory Circular 173（1912 年 3 月 3 日、署名 Edward C. Pickering） | https://articles.adsabs.harvard.edu/pdf/1912HarCi.173....1L | **Claude が原論文の 3 ページを画像にして全文を読んだ** |
| S2 | Harvard–Smithsonian CfA「Remembering Astronomer Henrietta Swan Leavitt」 | https://www.cfa.harvard.edu/news/remembering-astronomer-henrietta-swan-leavitt | **Claude が WebFetch で本文を確認** |
| S3 | MacTutor History of Mathematics「Henrietta Swan Leavitt」（セント・アンドルーズ大学） | https://mathshistory.st-andrews.ac.uk/Biographies/Leavitt/ | **Claude が WebFetch で本文を確認**（手紙は伝記に引用されたもの。原本は未確認） |
| S4 | NASA「Hubble Completes Eight-Year Effort to Measure Expanding Universe」（1999、2025 年更新） | https://science.nasa.gov/missions/hubble/hubble-completes-eight-year-effort-to-measure-expanding-universe | **Claude が WebFetch で本文を確認** |
| S5 | Carnegie Science「Hubble's Famous M31 VAR! plate」、Live Science・Linda Hall Library・Sky & Telescope の解説 | https://carnegiescience.edu/about/history/archives/plate-archives/m31var | 検索の抜粋のみ（Carnegie のページは WebFetch でエラー）。ChatGPT の報告と一致 |
| S6 | Leavitt「1777 Variables in the Magellanic Clouds」Annals of HCO 60, 87–108（1908） | （ADS） | 原論文は未確認。S1 の本文（"In H.A. 60, No. 4, attention was called to the fact that the brighter variables have the longer periods"）と S3 の引用で確認 |

## 事実確認リスト

### FACT-01
- **主張**：遠くの星は、見かけの暗さだけでは、遠いのか、もともと暗いのかを見分けられない。
- **出典**：S1（本当の明るさ "actual emission of light" と見かけの明るさの区別）、天文学の基本（説明）
- **検証結果**：VERIFIED（説明として）

### FACT-02
- **主張**：ハーバード大学天文台で働く女性たちは望遠鏡の操作を許されず、写真乾板に写った星を調べる仕事をしていた。
- **出典**：S2（"These skilled workers were not allowed to operate telescopes"）
- **検証結果**：VERIFIED（機関の解説として、WebFetch）
- **注意点**：彼女個人が一生望遠鏡に触れなかったとは言わない。台本は「女性たちは」と集団として言う。冒頭の「望遠鏡を使わせてもらえなかった女性だった」は使わない。

### FACT-03
- **主張**：1868 年生まれ。17 歳ごろから聴力が落ち、生涯続いた。病気で何度も仕事を離れた。
- **出典**：S2（"At age 17, Leavitt began experiencing hearing loss, which continued to decline throughout her life."）、S3（1897〜1902 ごろ、1908 年末〜1910 年 5 月の入院と療養、1913 年の手術で約 3 か月）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：「耳が聞こえなかった」と言わない。「耳が聞こえにくくなった」。

### FACT-04
- **主張**：1908 年、マゼラン雲の変光星 1777 個の一覧を発表し、明るい変光星ほど周期が長いことに気づいた。
- **出典**：S6、S1（"A Catalogue of 1777 variable stars in the two Magellanic Clouds is given in H.A. 60, No. 4." "In H.A. 60, No. 4, attention was called to the fact that the brighter variables have the longer periods"）、S3（"It is worthy of notice that the brighter variables have the longer periods."）
- **検証結果**：VERIFIED（S1 は原論文、S3 は WebFetch）
- **注意点**：「1777 個を一人で見つけた」と言わない。「1777 個の一覧にまとめた」。

### FACT-05
- **主張**：1912 年、小マゼラン雲の 25 個の変光星で、周期の対数と明るさを並べると、点がまっすぐな線に乗った。
- **出典**：S1（"In Figure 2, the abscissas are equal to the logarithms of the periods … A straight line can readily be drawn among each of the two series of points corresponding to maxima and minima, thus showing that there is a simple relation between the brightness of the variables and their periods."）
- **検証結果**：VERIFIED（Claude が原論文を読んだ）
- **注意点**：論文は Pickering の署名で出たが、冒頭に「This statement … has been prepared by Miss Leavitt」とある。

### FACT-06
- **主張**：星はほぼ同じ距離にあるので、周期は星の本当の明るさと結びついている（周期を測れば本当の明るさが分かる手がかり）。
- **出典**：S1（"Since the variables are probably at nearly the same distance from the Earth, their periods are apparently associated with their actual emission of light"）
- **検証結果**：VERIFIED（Claude が原論文を読んだ）

### FACT-07
- **主張**：のちの天文学者たちが、この関係を距離の物差しにしていった（1913 年のヘルツシュプルングの較正、シャプレーの銀河系の研究など）。
- **出典**：ChatGPT の報告（二次資料）
- **検証結果**：PARTIALLY_VERIFIED（人名と年は台本に出さない。「のちの天文学者たちが」とだけ言う）

### FACT-08
- **主張**：1921 年 12 月 12 日、がんで亡くなった。53 歳。
- **出典**：S2（"On the evening of December 12, 1921, as 53-year old astronomer Henrietta Swan Leavitt succumbed to cancer"）、S3（胃がん）
- **検証結果**：VERIFIED（WebFetch）

### FACT-09
- **主張**：1923 年 10 月 5〜6 日の夜、ハッブルはウィルソン山天文台の 100 インチ望遠鏡でアンドロメダ（M31）を撮った乾板（H335H）に、最初「N」と書いた星を「VAR!」と書き直した。その星はセファイド変光星だった。
- **出典**：S5
- **検証結果**：PARTIALLY_VERIFIED（複数の解説の検索抜粋で一致。Carnegie のページ本文は未取得）
- **注意点**：「その夜にすべてが分かった」と言わない。乾板の本物の画像は使わない（assets.md：商用には許可が必要）。

### FACT-10
- **主張**：アンドロメダの変光星から求めた距離は、当時考えられていた銀河系の大きさより遠く、アンドロメダは銀河系の外の別の銀河だと分かった。
- **出典**：S5（Linda Hall Library：M31 のセファイドから約 100 万光年）、ChatGPT の報告
- **検証結果**：PARTIALLY_VERIFIED（検索抜粋。発表は 1924〜1925 年）
- **注意点**：当時の値（約 100 万光年）はいまの値（約 250 万光年）より小さい。台本に距離の数字は出さない。

### FACT-11
- **主張**：1925 年、スウェーデンの数学者ミッタク＝レフラーが、彼女の死を知らずに手紙を書き、1926 年のノーベル物理学賞への推薦を考えていると伝えた。
- **出典**：S3（"has impressed me so deeply that I feel seriously inclined to nominate you to the Nobel prize in physics for 1926"）
- **検証結果**：VERIFIED（伝記に引用された手紙として、WebFetch。原本は未確認）
- **注意点**：「ノーベル賞に推薦された」と言わない。「推薦を考えた」。ノーベル賞は亡くなった人には贈られない（一般的な規則）。

### FACT-12
- **主張**：セファイド変光星は、いまも宇宙が広がる速さ（ハッブル定数）を測る距離の基準として使われている。
- **出典**：S4（"Although Cepheids are rare, they provide a very reliable 'standard candle' for estimating intergalactic distances."、Key Project はセファイドで距離を較正してハッブル定数を測定）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：セファイドだけで測るのではない（距離のはしごの一段）。「この星の周期が使われている」程度に言う。

## 言ってはいけない言い方

- 「望遠鏡を使わせてもらえなかった女性」（個人について断定になる）
- 「誰にも認められなかった」「一人で宇宙の大きさを測った」「宇宙の膨張を発見した」
- 「ノーベル賞に推薦された」「耳が聞こえなかった」
- 「1777 個を一人で見つけた」

## 演出（事実ではないもの）

| 箇所 | 内容 | 扱い |
|---|---|---|
| 人物 | 顔のない人体（MakeHuman）の後ろ姿・遠景 | 注記「※人物と場面は再現CG」を最初に 1 回 |
| 乾板・星の明滅・アンドロメダの乾板 | 再現 CG（本物の乾板の画像ではない） | 「VAR!」の場面に「※再現」 |
| 宇宙へ伸びる物差し | 説明のための演出 | 「※説明のための図」を 1 回 |
| 本物の写真・図 | `assets.md` の素材だけ | 画面に小さく「写真：出典」 |
