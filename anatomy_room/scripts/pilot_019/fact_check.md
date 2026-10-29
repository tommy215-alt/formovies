# pilot_019：事実確認リスト（ジョン・ハリソン——海の上で経度を知る時計）

調査日：2026-10-30（ユーザーの PC のセッション）。確認方法の定義は `docs/FACT_CHECK_POLICY.md`。

**確認の流れ**：ChatGPT の報告（`gpt_fact_check_prompt.md` への回答）を下書きにし、Claude が主な出典に当たり直した。WebFetch は本文を取得し、小さなモデルが質問に沿って抜き出す方法（全文を一字一句は読んでいない）。Historic England・ONS の旧 URL・米国議会図書館のページは WebFetch が 403／404 だった（下の表に記録）。

## 物語の核

- **困難**：海の上で経度（東西の位置）を確かめる実用的な方法がなく、1707 年のシリー諸島の海難では 1,300 人以上が亡くなった（S4）。時計で経度は求められるが、当時の時計は船の揺れと温度の変化で狂った（S1）。ハリソンは大工で、時計作りは独学（S1）。
- **本人がしたこと**：H1 で航海の試験に出て、船乗りが見誤った陸地を言い当てた（S1）。H2 に根本的な欠点を見つけ、H3 に 19 年かけた（S1）。**答えは H3 ではなく小さな時計にあると気づき、発想を変えて H4 を作った**（S2）。
- **何が変わったか**：ジャマイカへの約 2 か月の航海で H4 の遅れは約 5 秒（S5）。それでも委員会は 2 回目の試験を求め（S5・S1）、支払いは 1765 年の 1 万ポンドと 1773 年の議会の 8,750 ポンド。1714 年の経度法の賞金そのものは受け取っていない（S3）。
- **その後**：H4 の複製 K1 がクックの 2 回目の航海で使われた（S8）。

## 出典

| ID | 資料 | URL | 確認方法 |
|---|---|---|---|
| S1 | Royal Museums Greenwich「Longitude found – the story of Harrison's timekeepers」 | https://www.rmg.co.uk/stories/topics/harrisons-clocks-longitude-problem | **Claude が WebFetch で本文を確認** |
| S2 | Royal Museums Greenwich 収蔵品「H4」（ZAA0037） | https://www.rmg.co.uk/collections/objects/rmgc-object-79142 | **Claude が WebFetch で本文を確認** |
| S3 | ONS（英国国家統計局）David Bradbury「Valuing John Harrison's work – how much is that £20,000 longitude reward worth today?」2020-01-17 | https://blog.ons.gov.uk/2020/01/17/valuing-john-harrisons-work-how-much-is-that-20000-longitude-reward-worth-today/ | **Claude が WebFetch で本文を確認** |
| S4 | Royal Museums Greenwich 収蔵品「Sir Cloudesly Shovel in the Association with the Eagle, Rumney and the Firebrand, Lost on the Rocks of Scilly, October 22, 1707」（版画、1710 年ごろ） | https://www.rmg.co.uk/collections/objects/rmgc-object-140657 | **Claude が WebFetch で本文を確認** |
| S5 | Linda Hall Library「Scientist of the Day – John Harrison」 | https://www.lindahall.org/about/news/scientist-of-the-day/john-harrison | **Claude が WebFetch で本文を確認** |
| S6 | 経度法（1714 年）の条文 | （Wikipedia「Longitude Act」、RMG の転記 PDF。PDF は画像化されていて読めなかった） | 検索の抜粋のみ（ChatGPT も転記で確認） |
| S7 | Linda Hall Library「Cloudesley Shovell」、MacTutor「Scilly Isles」 | https://www.lindahall.org/about/news/scientist-of-the-day/cloudesley-shovell/ ・ https://mathshistory.st-andrews.ac.uk/Gaz/Scilly_Isles/ | 検索の抜粋のみ |
| S8 | K1 とクックの航海（Commons「K1 Chronometer at the Greenwich Observatory」の説明、Oxfordshire Blue Plaques「Larcum Kendall」、RMG 図書「Captain Cook's marine timekeepers: the Kendall watches」） | https://commons.wikimedia.org/wiki/File:K1_Chronometer_at_the_Greenwich_Observatory.jpg ほか | Commons の説明は WebFetch、ほかは検索の抜粋のみ |
| S9 | GPS.gov「GPS and Telling Time」 | （ChatGPT の報告による） | ChatGPT の報告のみ（広く知られた仕組み） |
| — | Historic England「How Did the Sinking of a Ship in 1707 Lead to the Invention of the Marine Chronometer?」 | historicengland.org.uk | WebFetch は 403。ChatGPT の報告のみ |

## 事実確認リスト

### FACT-01（冒頭）
- **主張**：1707 年 10 月 22 日の夜、ショヴェル提督の艦隊の軍艦 4 隻（Association・Eagle・Romney・Firebrand）がシリー諸島の岩で失われた。何日も悪天候で天体を観測できず、位置を実際より南だと見誤っていた。1,300 人以上が亡くなった。
- **出典**：S4（"Over 1300 men were lost, including Shovell, and only 26 were reported to have survived."／悪天候で観測ができず、推定した位置が実際より南だった。正確な原因は航海術・羅針盤・天候などで議論が続いている）、S7（少なくとも 1,400 人、2,000 人に及ぶともいわれる）
- **検証結果**：VERIFIED（S4 は WebFetch）。死者数は資料で幅がある → 台本は「1,300人以上」（S4 の下限。どの資料とも矛盾しない）。
- **注意点**：MacTutor は「誤りは経度より緯度だった」とする（S7）。**台本で「経度が分からなかったから沈んだ」と言わない**。「位置を見誤った」までにし、経度の話はその次の文で「海の上で位置を知るのは難しかった」とつなぐ。

### FACT-02
- **主張**：当時、緯度（南北）は太陽などの観測で求められたが、経度（東西）を海の上で確かめる実用的な方法はなかった。
- **出典**：S1、ChatGPT の報告（RMG「Time and Longitude gallery」）
- **検証結果**：PARTIALLY_VERIFIED。月距法など方法の研究はあった → 「方法がなかった」ではなく「**実用的な方法が、まだなかった**」。

### FACT-03
- **主張**：1714 年、イギリス議会が経度法で賞金を懸けた。最高 2 万ポンド（半度以内）。
- **出典**：S6（1 度以内 1 万ポンド、3 分の 2 度以内 1 万 5000 ポンド、半度以内 2 万ポンド）、S3（"Parliament had in 1714 offered a reward of £20,000"、検索の抜粋）
- **検証結果**：VERIFIED（S3 の本文と ChatGPT の転記で一致。条文の原本画像は未確認）
- **注意点**：いまの価値には換算しない（資料で 200 万〜800 万ポンドと幅がある）。

### FACT-04
- **主張**：地球は 1 時間に 15 度回るので、出発地の時刻を正確に持っていけば、その場所の時刻との差で経度が分かる。当時の時計は船の揺れや温度の変化で狂った。
- **出典**：S1、ChatGPT の報告（Historic England "motion and temperature could affect timepieces"）
- **検証結果**：VERIFIED（原理は計算で確か。時計の狂いは ChatGPT の報告と S1）

### FACT-05
- **主張**：ハリソンは大工で、時計作りは独学だった。
- **出典**：S1（"John Harrison was a carpenter by trade who was self-taught in clock making."）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：「字も読めない素人」「誰の助けもなかった」とは言わない（ロンドンの時計職人ジョージ・グラハムらの支援があった）。

### FACT-06
- **主張**：H1 の試験航海（1736 年、リスボン）の帰り、ハリソンは、船の士官たちがスタート岬だと思った陸地がリザード岬だと言い当てた。
- **出典**：S1（"As they neared England, Harrison announced that a headland the officers had thought was the Start was in fact the Lizard."）
- **検証結果**：VERIFIED（WebFetch。航海記録の原本は未確認）

### FACT-07
- **主張**：H2 は根本的な欠点が見つかり、試験に出なかった。H3 は 1740 年から 19 年かけた。
- **出典**：S1（"H2 never went to trial, because Harrison had discovered a fundamental flaw."／"Harrison began work on his third attempt, H3, in 1740, and would continue to work on it for 19 years."）
- **検証結果**：VERIFIED（WebFetch）

### FACT-08（決定的な瞬間）
- **主張**：ジェフリーズが作った懐中時計（1753 年）で、答えは H3 ではなく小さな時計にあると気づいた。H4 は 1759 年完成。文字盤の直径 102 mm、全体 165×124×28 mm、重さ 1.45 kg。
- **出典**：S2（"This went so well that Harrison began to realise that it pointed to the longitude solution" "not in H3 but in smaller watches."／"completed in 1759"／"Dial diameter: 102 mm;Overall: 165 mm x 124 mm x 28 mm x 1.45 kg"）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：ジェフリーズの時計の年は S1 が 1751〜52 年（注文）、S2 が 1753 年（完成）。台本では年を出さない。「手のひらに乗る」とは言わない（1.45 kg、16.5 cm）。

### FACT-09
- **主張**：1761 年、息子のウィリアムが H4 を持ってジャマイカへ。約 2 か月後の到着時、遅れは約 5 秒だった。
- **出典**：S5（"sailed for Jamaica in 1761, and when it arrived 2 months later, it was only 5 seconds slow"）。ほかの資料で 5.1 秒・81 日などの数字（検索の抜粋。日数は食い違う）
- **検証結果**：PARTIALLY_VERIFIED（S5 は WebFetch。試験記録の原本は未確認）
- **注意点**：台本は「約2か月」「わずか5秒ほど」。経度の誤差の数字は出さない。

### FACT-10
- **主張**：委員会は結果を全面的には認めず、2 回目の試験を求めた（1764 年、バルバドス）。
- **出典**：S5（"the Board claimed the result was a fluke and demanded a second trial."）、S1（"Harrison sailed with H4 in March 1764, arriving in May."）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：委員会やマスケリンを悪役にしない（大金を払う前に確かめるのには理由がある）。台本は「もう一度の試験を求めた」まで。

### FACT-11
- **主張**：1765 年に 1 万ポンド（H4 の原理を示したとき）。1773 年に議会から 8,750 ポンド。1714 年の経度法の賞金そのものは受け取っていない。
- **出典**：S3（"John Harrison never actually received the reward specified under the 1714 Act."／"£10,000 as an interim payment for his 'H4' chronometer in 1765."／"a special award of £8,750 by Parliament in 1773."）、S1（"The Board's recommendation was that parliament should award Harrison £10,000, when he demonstrated the principles of H4."）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：国王ジョージ 3 世の「味方をしよう」という発言は UNVERIFIED（S1 は "no doubt with the King's encouragement" まで）→ 台本で使わない。1773 年のハリソンは 79〜80 歳（1693 年生まれ）→ 台本は「80歳近い」。

### FACT-12
- **主張**：ハリソンは 1776 年 3 月 24 日に亡くなった。
- **出典**：S5（"Harrison died on his 83rd birthday, Mar. 24, 1776."）、ChatGPT の報告
- **検証結果**：PARTIALLY_VERIFIED。「誕生日に亡くなった」は暦（旧暦・新暦）が絡むので台本で使わない。

### FACT-13
- **主張**：ラーカム・ケンダルが H4 を写して作った K1 が、クックの 2 回目の航海（1772〜1775 年）で使われた。
- **出典**：S8（Commons の説明：K1 は 1766〜1769 年に作られた H4 の複製で、クックの 2 回目・3 回目の航海に使われた）、ChatGPT の報告（ANU Press の公開章）
- **検証結果**：PARTIALLY_VERIFIED（博物館・研究の本文は未確認だが、資料どうしは一致）
- **注意点**：クックの言葉（"our never-failing guide the Watch" など）は資料で文言が少しずつ違い、日誌の原本と未照合 → 台本で引用しない。

### FACT-14
- **主張**：H2・H3・H4 の実物は王立グリニッジ天文台に展示（H1 は保存修復中で、天文台には複製）。
- **出典**：S1（"You can come and see a replica of H1, and the original H2, H3 and H4 on display at the Royal Observatory Greenwich."）
- **検証結果**：VERIFIED（WebFetch）。台本では「いまも残っている」程度にする。

### FACT-15
- **主張**：GPS の衛星は原子時計を積み、正確な時刻で位置を計算している。
- **出典**：S9（"Each GPS satellite contains multiple atomic clocks"、ChatGPT の報告）
- **検証結果**：PARTIALLY_VERIFIED（ChatGPT の報告のみ。一般に広く知られた仕組み）
- **注意点**：「ハリソンと同じ仕組み」とは言わない。「正確な時計で位置を知る、という考え方がつながっている」まで。

## 言わないこと

- 「経度が分からなかったから 4 隻が沈んだ」（FACT-01）／「経度を測る方法はなかった」（FACT-02）
- 「ハリソンが 2 万ポンドの賞金を受け取った」（FACT-11）／「国王の一言で賞金を得た」
- 「マスケリンが不正をした・邪魔をした」（FACT-10）
- 「字も読めない素人」「手のひらに乗る時計」（FACT-05・08）
- 「誕生日に亡くなった」（FACT-12）／クックの言葉の直接の引用（FACT-13）
- 「GPS はハリソンと同じ仕組み」（FACT-15）
