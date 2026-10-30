# pilot_020：事実確認リスト（スコットの南極点隊、1910〜1913 年）

調査日：2026-10-30（ユーザーの PC のセッション）。確認方法の定義は `docs/FACT_CHECK_POLICY.md`。悲劇用（`templates/DESIGN_MODES.md`）の 1 本目。

**確認の流れ**：ChatGPT の報告（`gpt_fact_check_prompt.md` への回答）を下書きにし、Claude が主な出典に当たり直した。WebFetch は本文を取得し、小さなモデルが質問に沿って抜き出す方法（全文を一字一句は読んでいない）。日記は 1913 年刊行版（Wikisource の翻刻）で確認し、大英図書館の原手稿とは照合していない（刊行版では一部の記述が省かれている：大英図書館の目録、ChatGPT の報告）。

## 物語の核

- **困難**：南極点に着くと、アムンセンが先に着いていた（S1・S2）。帰り道でエヴァンスが倒れて死亡（S2）、オーツは凍傷で歩けなくなり、吹雪の中へ出て戻らなかった（S1）。氷点下 40 度（S1）、燃料が足りない（S1）、研究ではこの年の 3 月は平年よりかなり寒かった（S4）。
- **本人たちがしたこと**：最後まで人がそりを引き、約 16 kg の岩石標本を運び続けた（S6）。補給所まで 11 マイル（約 18 km）の地点で、毎日出発の準備をしたが、21 日から強風がやまなかった（S1）。
- **結末**：3 月 29 日の最後の日記「For God's sake look after our people.」（S1・S3）。11 月 12 日、捜索隊がテントを見つけた（ChatGPT の報告：1913 年刊行版の第 2 巻）。

## 出典

| ID | 資料 | URL | 確認方法 |
|---|---|---|---|
| S1 | Robert Falcon Scott『Scott's Last Expedition』Vol. I（1913）の日記、第 18〜20 章（Wikisource の翻刻） | https://en.wikisource.org/wiki/Scott%27s_Last_Expedition/Volume_1/Chapter_18 ・ /Chapter_19 ・ /Chapter_20 | **Claude が WebFetch で本文を確認** |
| S2 | Royal Museums Greenwich「History of Antarctic explorers」 | https://www.rmg.co.uk/stories/maritime-history/history-antarctic-explorers | **Claude が WebFetch で本文を確認** |
| S3 | 大英図書館「Antarctic Anniversaries: Captains James Cook and Robert Scott」 | https://www.bl.uk/stories/blogs/posts/antarctic-anniversaries | **Claude が WebFetch で本文を確認** |
| S4 | Susan Solomon & C. R. Stearns「On the role of the weather in the deaths of R. F. Scott and his companions」PNAS 96(23), 1999 | https://pubmed.ncbi.nlm.nih.gov/10557264/ | **Claude が WebFetch で抄録を確認**（本文の表は未確認） |
| S5 | Royal Museums Greenwich 記念碑の登録「M3284」（オブザベーション・ヒルの十字架） | https://memorials.rmg.co.uk/m3284/ | ChatGPT の報告のみ（台本では使わない） |
| S6 | 岩石標本 35 ポンド（約 16 kg）：SPRI の教育資料「Focus on Science」、1913 年 2 月の新聞記事（Papers Past）、ほか | https://www.spri.cam.ac.uk/museum/resources/teacherpackscienceobjectsfromantarctica.pdf ・ https://dynamic-rsnz.natlib.govt.nz/newspapers/MH19130215.2.15 | ChatGPT の報告＋Claude の検索の抜粋（SPRI の PDF は本文を取り出せなかった）。30 ポンドとする資料もある |
| S7 | ケンブリッジ大学「Final letters mark centenary of Scott's last march」 | https://www.cam.ac.uk/research/news/final-letters-mark-centenary-of-scotts-last-march | ChatGPT の報告のみ |

## 事実確認リスト

### FACT-01（冒頭）
- **主張**：スコット隊は南極点の手前で黒い旗を見つけ、先を越されたと知った。南極点にはノルウェーのテントがあり、アムンセンの手紙（ノルウェー王への手紙を託すもの）が残っていた。
- **出典**：S1（1 月 16 日 "The Norwegians have forestalled us and are first at the Pole."／1 月 19 日 "the ominous black flag which has first apprised us of our predecessors' success"／1 月 18 日 "A note from Amundsen, which I keep, asks me to forward a letter to King Haakon!"）、S2（"They find Amundsen's tent and realise they have been beaten."）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：冒頭の「あと少し」は演出の言い方（黒い旗を見たのは南極点の前日）。「旗が立っていた」は黒い旗とノルウェーの旗の両方に当てはまる。

### FACT-02
- **主張**：スコット隊（1910 年出発）の目的は南極点への到達と科学調査。南極点隊は 5 人（スコット、ウィルソン、バワーズ、オーツ、エドガー・エヴァンス）。
- **出典**：S2（"Scott and his crew leave Cardiff on the Terra Nova on 15 June."、5 人の名前）、S3
- **検証結果**：VERIFIED（WebFetch）

### FACT-03
- **主張**：アムンセン隊は犬ぞりで、1911 年 12 月に南極点に到達。スコット隊は 1912 年 1 月 17 日。差は 1 か月以上。
- **出典**：S3（"reached the South Pole on this day, 17 January, 1912."）、S1（1 月 17 日の日記）、S2（アムンセンは 1911 年 12 月 15 日・スコットは 1912 年 1 月 18 日と書く）、ChatGPT の報告（アムンセン 12 月 14 日、34 日差）
- **検証結果**：PARTIALLY_VERIFIED。日付は資料で 1 日ずれる → 台本は「1912年1月」「1か月以上も先」とし、日にちは言わない。

### FACT-04
- **主張**：スコット隊は動力そり・ポニー・犬を使い、最後は人がそりを引いた。
- **出典**：ChatGPT の報告（S2・Cherry-Garrard）
- **検証結果**：PARTIALLY_VERIFIED（ChatGPT の報告のみ。広く知られた事実）。「犬を使わなかった」とは言わない。距離の数字は出さない。

### FACT-05
- **主張**：スコットの日記（1 月 17 日）「Great God! this is an awful place」。
- **出典**：S1（"Great God! this is an awful place and terrible enough for us to have laboured to it without the reward of priority."）
- **検証結果**：VERIFIED（WebFetch）。台本の訳「なんということだ、ここは恐ろしい場所だ」。

### FACT-06
- **主張**：1912 年 2 月 17 日、エドガー・エヴァンスが帰り道で倒れて死亡。
- **出典**：S2（17 February 1912 "Petty Officer Edgar Evans dies in his tent after collapsing during the trip back."）
- **検証結果**：VERIFIED（WebFetch）。死因は断定しない。

### FACT-07
- **主張**：3 月 16 日か 17 日、凍傷で歩けなくなっていたオーツが「I am just going outside and may be some time.」と言ってテントを出て、戻らなかった（スコットの日記の記述）。
- **出典**：S1（3 月 16 日または 17 日の項、"I am just going outside and may be some time."／"He went out into the blizzard and we have not seen him since."）、S2
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：「自殺した」「仲間を救うために」と内心を断定しない。言葉はオーツ本人の記録ではなく、スコットの日記に書かれたもの。

### FACT-08
- **主張**：3 月の気温は氷点下 40 度。研究では 1912 年 2 月下旬〜3 月の最低気温は、1985 年以降の同じ地域・季節より華氏 10〜20 度（約 6〜11℃）低かった。
- **出典**：S1（3 月 16 日または 17 日 "The cold is intense, −40° at midday."、3 月 19 日 "−40° temp. to-day"）、S4（抄録：10〜20°F 低い、"their deaths were therefore due, at least in part, to the unusual weather conditions they endured"）
- **検証結果**：VERIFIED（WebFetch。日記の温度は華氏。−40°F＝−40℃）
- **注意点**：寒さだけを原因にしない（台本は「〜とされる」）。

### FACT-09
- **主張**：燃料と食料が足りなかった。
- **出典**：S1（2 月 24 日 "shortage oil"、3 月 2 日 "a shortage of oil"、3 月 29 日 "We had fuel to make two cups of tea apiece and bare food for two days on the 20th."）
- **検証結果**：VERIFIED（WebFetch）。燃料が漏れた原因は台本で言わない。

### FACT-10
- **主張**：補給所（ワントン・デポ）まで 11 マイル（約 18 km）。21 日から強風（吹雪）がやまず、出発できなかった。
- **出典**：S1（3 月 21 日 "Got within 11 miles of depôt Monday night; had to lay up all yesterday in severe blizzard."、3 月 29 日 "every day we have been ready to start for our depôt 11 miles away"、"Since the 21st we have had a continuous gale from W.S.W. and S.W."）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：「18 キロ歩けば助かった」とは言わない。

### FACT-11
- **主張**：3 月 29 日、スコットの最後の日記「For God's sake look after our people.」。
- **出典**：S1、S3（"For God's sake look after our people."）
- **検証結果**：VERIFIED（WebFetch）。台本の訳「どうか、私たちの仲間を頼む」。

### FACT-12
- **主張**：1912 年 11 月、捜索隊がテントを見つけた。中にスコット・ウィルソン・バワーズ。そりには約 16 kg（35 ポンド）の岩石標本（グロッソプテリスの化石を含む）が残っていた。
- **出典**：ChatGPT の報告（1913 年刊行版の第 2 巻 "Inside the tent were the bodies of Captain Scott, Doctor Wilson, and Lieutenant Bowers."、11 月 12 日）、S2（"The bodies are discovered seven months later."）、S6
- **検証結果**：PARTIALLY_VERIFIED（発見の日付と標本の重さは ChatGPT の報告と検索の抜粋。資料で 11 月 10 日・30 ポンドとするものもある）→ 台本は「その年の11月」「約16キロ」。

## 言わないこと

- 「スコットが無能だったから全滅した」「アムンセンがずるをした」「オーツは自殺した」
- 「18 キロ歩けば助かった」「燃料缶の漏れ（または犬ぞり隊）のせいで全滅した」
- 「遺体は今も海に向かって動いている」（UNVERIFIED）
- 日付の細かい数字（アムンセンの到達日・南極点の日付は資料で 1 日ずれる）
