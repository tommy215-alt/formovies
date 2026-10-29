# pilot_016：事実確認リスト（大陸は動いている——アルフレート・ヴェーゲナー）

調査日：2026-10-29（ユーザーの PC のセッション）。確認方法の定義は `docs/FACT_CHECK_POLICY.md`。

**確認の流れ**：ChatGPT の報告（`gpt_fact_check_prompt.md` の依頼文）を下書きにし、Claude が主な出典に当たり直した。項目ごとに「Claude が本文を読んだ（WebFetch）」「ChatGPT の報告のみ」を分ける。WebFetch は本文を取得し、小さなモデルが質問に沿って抜き出す方法（全文を一字一句は読んでいない）。

## 物語の核（ガイドライン v2.1 の 5）

- **最も大きな困難**：大陸が動いた証拠（海岸線・化石・地層・昔の気候）を集めても、大陸を動かす力を説明できなかった（S1・S3）。そのため 1926 年のニューヨークのシンポジウムなどで厳しい批判を受けた（S4）。
- **具体的な出来事**：1912 年 1 月 6 日のフランクフルトでの発表（S2・S3）。1929 年の改訂版の一文「The Newton of drift theory has not yet appeared.」（S1、NASA の解説の英訳）。
- **本人がしたこと**：分野をまたいだ証拠を集め、本を改訂し続けた（1915 → 1920 → 1922 → 1929）。
- **何が変わったか**：本人の死後、1960 年代に海洋底拡大と海底の磁気の縞模様が見つかり、プレートテクトニクスとして「大陸は動く」が認められた（S5・S6）。ただし彼の考えた仕組みは正しくなかった。
- **現在**：大西洋中央海嶺では海底が平均で年約 2.5 cm 広がり、GPS で地殻の動きを測れる（S5）。

## 出典

| ID | 資料 | URL | 確認方法 |
|---|---|---|---|
| S1 | NASA Earth Observatory「Alfred Wegener」 | https://science.nasa.gov/earth/earth-observatory/alfred-wegener | **Claude が WebFetch で本文を確認** |
| S2 | Alfred Wegener Institute（AWI）「Alfred Wegener」 | https://www.awi.de/en/about-us/organisation/alfred-wegener.html | **Claude が WebFetch で本文を確認** |
| S3 | Wegener「Die Entstehung der Kontinente」（1912）、『Die Entstehung der Kontinente und Ozeane』（1915・1929 第 4 改訂版）、Nature の書評（1929） | （ChatGPT の報告による） | ChatGPT の報告（原著の本文の照合は未完了） |
| S4 | Nature の書評（1928、AAPG のシンポジウムの論文集）、APS「January 6, 1912」 | （ChatGPT の報告による） | ChatGPT の報告のみ |
| S5 | USGS『This Dynamic Earth』「Understanding plate motions」 | https://pubs.usgs.gov/gip/dynamic/understanding.html | **Claude が WebFetch で本文を確認** |
| S6 | USGS「Harry Hammond Hess」、英国地質学会「Vine and Matthews」 | （ChatGPT の報告による） | ChatGPT の報告のみ |
| S7 | 米国議会図書館「A Drifting World: The Supercontinent of Pangaea」 | （ChatGPT の報告による） | ChatGPT の報告のみ |

## 事実確認リスト

### FACT-01
- **主張**：1880 年 11 月 1 日、ベルリンに生まれた。大学では物理学・気象学・天文学を学んだ（地質学が専門ではない）。
- **台本**：L02
- **出典**：S1（"born in Berlin on November 1, 1880"）、S2（"studied from 1900 to 1904 physics, meteorology and astronomy"）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：「素人」と言わない。「気象学者」とする（S2：「31-year-old meteorologist Alfred Wegener」）。

### FACT-02
- **主張**：1912 年 1 月 6 日、フランクフルトで大陸移動の考えを発表した。
- **台本**：L02
- **出典**：S2（「the day 31-year-old meteorologist Alfred Wegener gave his talk on the formation of the oceans and continents」）、S3
- **検証結果**：VERIFIED（S2 は WebFetch。日付は S3 の論文の記述として ChatGPT の報告）
- **注意点**：「世界で初めて思いついた」とは言わない。

### FACT-03
- **主張**：当時、大陸は動かないと考えられ、離れた大陸の同じ化石は、沈んだ陸の橋で説明されていた。
- **台本**：L03
- **出典**：S1（「Wegener began by demolishing the theory that large land bridges had once connected the continents」）
- **検証結果**：PARTIALLY_VERIFIED（陸橋の説は WebFetch で確認。「誰もが動かないと考えた」とは言わない）

### FACT-04
- **主張**：証拠は、海岸線の形・海をはさんだ同じ化石・つながる地層・昔の氷河の跡。
- **台本**：L04、L05
- **出典**：S1、S3
- **検証結果**：PARTIALLY_VERIFIED（NASA の解説で確認。原著のページごとの照合は未完了）
- **注意点**：海岸線だけで証明されたと言わない。

### FACT-05
- **主張**：彼は、破れた新聞を切り口と文字の並びでつなぎ直すことに例えた。
- **台本**：L06
- **出典**：S1（"It is just as if we were to refit the torn pieces of a newspaper by matching their edges"、続けて印刷の行がつながるかを確かめる）
- **検証結果**：PARTIALLY_VERIFIED（NASA の英訳で確認。ドイツ語の原文のページは未確認）。台本では「例えた」とする。

### FACT-06
- **主張**：大陸を動かす力を説明できなかった。地球の自転の遠心力や、太陽と月の引力による力を挙げたが、足りないと自分でも気づいていた。
- **台本**：L07
- **出典**：S1（"He realized these forces were inadequate."）
- **検証結果**：VERIFIED（WebFetch）

### FACT-07
- **主張**：1926 年、ニューヨークのシンポジウム（アメリカ石油地質学者協会）で、多くの研究者が批判した。
- **台本**：L08
- **出典**：S4
- **検証結果**：PARTIALLY_VERIFIED（ChatGPT の報告のみ）。「全員が笑った」とは言わない。発言の引用は使わない。

### FACT-08
- **主張**：1929 年の改訂版（第 4 版）に「大陸移動説のニュートンは、まだ現れていない」と書いた。
- **台本**：L09、L10
- **出典**：S1（"In his last (1929) revision … 'The Newton of drift theory has not yet appeared.'"）、S3（第 4 版は 1929 年）
- **検証結果**：PARTIALLY_VERIFIED（NASA の解説で確認。ドイツ語の原文のページは未確認）

### FACT-09
- **主張**：1930 年 11 月 1 日、グリーンランドの氷床の観測基地アイスミッテで 50 歳の誕生日を祝い、その日に基地を出発した。帰り道で亡くなった（11 月 16 日ごろと推定）。遺体は 1931 年 5 月 12 日に見つかった。
- **台本**：L11、L12
- **出典**：S1（"on November 1, the group gaily celebrated Wegener's 50th birthday"、最後の写真の説明「taken on 1 November 1930 … as they were leaving the 'Eismitte' Station」、遺体は 1931 年 5 月 12 日）、S2（"presumably about 16th of November, 1930"、"On the 12th of May, 1931 the searching expedition … found Wegener's gravesite"、死因は「Only heart failure could be assumed」）
- **検証結果**：VERIFIED（WebFetch。死亡日は推定、死因は不確定）
- **注意点**：死を科学界の反対と結びつけない。心の中を描かない。

### FACT-10
- **主張**：1960 年代、海底が海嶺から両側へ広がっていること（海洋底拡大、ヘス 1962 年）と、海底の磁気の縞模様（ヴァイン、マシューズ 1963 年）が分かり、プレートテクトニクスにつながった。
- **台本**：L13、L14
- **出典**：S5、S6
- **検証結果**：PARTIALLY_VERIFIED（年は ChatGPT の報告。USGS の解説は WebFetch で一部確認）

### FACT-11
- **主張**：彼の考えた仕組み（大陸が海底を押し分けて進む）は正しくなかったが、大陸が動くという大枠は正しかった。
- **台本**：L15、L16
- **出典**：S1、S5
- **検証結果**：VERIFIED（結論として）
- **注意点**：「彼の説がそのまま正しかった」と言わない。

### FACT-12
- **主張**：大西洋中央海嶺では、海底が平均で年約 2.5 cm 広がっている。GPS で地殻の動きを測れる。
- **台本**：L17
- **出典**：S5（"The rate of spreading along the Mid-Atlantic Ridge averages about 2.5 centimeters per year"、"the GPS has been the most useful for studying the Earth's crustal movements"）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：「大陸が毎年 2.5 cm 離れる」と言い切らない。台本は「海嶺で海底が広がっている」。L18 の「いまも少しずつ離れ続けている」は大枠として。

## 言ってはいけない言い方

- 「誰もが笑った」「科学者たちは無知だった」「反対されたから死んだ」
- 「彼の説は完全に正しかった」「世界で初めて大陸移動を思いついた」
- 「海岸線が合ったから証明された」

## 演出（事実ではないもの）

| 箇所 | 内容 | 扱い |
|---|---|---|
| 人物 | 顔のない人形の後ろ姿・遠景 | 注記「※人物と場面は再現CG」を最初に 1 回 |
| 大陸が合わさる・動く地球 | 説明のための図（実際の地質年代の正確な再現ではない） | 「※説明のための図」を 1 回 |
| 本物の写真・図 | `assets.md` の素材だけ | 画面に小さく「写真：出典」 |
