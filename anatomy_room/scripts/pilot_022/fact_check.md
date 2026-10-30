# pilot_022：事実確認リスト（マーシャルとウォレン、ピロリ菌、1979〜2005 年）

調査日：2026-10-30（ユーザーの PC のセッション）。確認方法の定義は `docs/FACT_CHECK_POLICY.md`。

**確認の流れ**：ChatGPT の報告（`gpt_fact_check_prompt.md` への回答）を下書きにし、Claude が主な出典に当たり直した。NobelPrize.org（講演 PDF・プレスリリース）は Claude の WebFetch が 403 で本文を取得できなかった。

## 物語の核

- **困難**：当時、潰瘍の原因はストレスや生活習慣と考えられていた（S2）。菌がなかなか育たなかった（S1）。学会に送った要旨は採用されなかったとされる（S1）。菌が見つかるだけでは原因とは言えない。
- **本人たちがしたこと**：ウォレンが胃の組織にらせん形の菌を見つけた（S1）。培養に成功した（1982 年、S1・S2）。マーシャルは 1984 年、自分で菌を飲み、内視鏡と生検で胃の炎症を確かめ、治療した（S1）。
- **結末**：除菌で潰瘍が治り再発が減ることが示され、1994 年に NIH の会議が除菌を勧めた（S4）。2005 年にノーベル賞（S2）。

## 出典

| ID | 資料 | URL | 確認方法 |
|---|---|---|---|
| S1 | 「History of chronic gastritis: How our perceptions have changed」World Journal of Gastroenterology（医学史のレビュー） | https://pmc.ncbi.nlm.nih.gov/articles/PMC11036504/ | **Claude が WebFetch で本文を確認** |
| S2 | ノーベル賞 2005 年 生理学・医学賞（プレスリリース・受賞者のページ） | https://www.nobelprize.org/prizes/medicine/2005/press-release/ | 検索の抜粋のみ（Claude の WebFetch は 403）＋ChatGPT の報告 |
| S3 | Marshall, Nobel Lecture「Helicobacter Connections」（2005） | https://www.nobelprize.org/uploads/2018/06/marshall-lecture.pdf | ChatGPT の報告（検索の抜粋）のみ。Claude は 403 で未確認 |
| S4 | NIH Consensus Development Conference「Helicobacter pylori in peptic ulcer disease」1994 | PubMed 7920747・8007082 | ChatGPT の報告（書誌） |
| S5 | Warren & Marshall, The Lancet 1983;1:1273–1275／Marshall & Warren, The Lancet 1984;1:1311–1315／Marshall ほか, Med J Aust 1985;142:436–439 | PubMed 6134060・6145023 | ChatGPT の報告（書誌）。本文は未確認 |

## 事実確認リスト

### FACT-00（オープニング）
- **主張**：胃潰瘍の大きな原因は、細菌（ピロリ菌）だった。
- **出典**：S2（"for their discovery of the bacterium Helicobacter pylori and its role in gastritis and peptic ulcer disease"）、S4
- **検証結果**：VERIFIED（授賞理由は検索の抜粋で複数一致）
- **注意点**：「すべての胃潰瘍」とは言わない（解熱鎮痛薬などによる潰瘍もある）→「大きな原因」。

### FACT-01
- **主張**：1984 年、マーシャルは培養した菌を自分で飲んだ。
- **出典**：S1（"intentionally infected himself with Campylobacter pyloridis"、1984 年）、S3
- **検証結果**：VERIFIED（WebFetch）

### FACT-02
- **主張**：当時、潰瘍の原因はストレスや胃酸・生活習慣と考えられていた。強い酸の胃に細菌が住みついて病気を起こす、という考えは広く認められていなかった。
- **出典**：S2（"stress and lifestyle were considered the major causes of peptic ulcer disease"、検索の抜粋）、ChatGPT の報告（IARC：胃のらせん形の菌は 1899 年に報告がある）
- **検証結果**：PARTIALLY_VERIFIED
- **注意点**：「胃に細菌は 1 匹もいないと思われていた」「誰も信じなかった」とは言わない。「マーシャルが最初に胃の細菌を見つけた」とも言わない。

### FACT-03
- **主張**：1979 年ごろ、パースの病理医ウォレンが、胃の組織にらせん形の細菌を見つけた。
- **出典**：S1（Warren, a pathologist in Perth … "during a routine histologic examination"）、S2
- **検証結果**：VERIFIED（WebFetch）

### FACT-04
- **主張**：若い医師マーシャルが加わり、菌を育てようとしたが、なかなか育たなかった。
- **出典**：S1、ChatGPT の報告（NCBI Bookshelf、マーシャルは 1951 年生まれ）
- **検証結果**：PARTIALLY_VERIFIED

### FACT-05
- **主張**：1982 年、イースターの連休で培養皿が長く置かれ、菌が育っていたとされる。
- **出典**：S1（"This event occurred by chance, when cultures were left in the thermostat over the long Easter weekend." "bacterial colonies appeared on the 5th day after biopsy."）
- **検証結果**：PARTIALLY_VERIFIED（レビューの記述。一次資料は未確認）→ 台本は「とされる」、日数は言わない。

### FACT-06
- **主張**：学会に送った発表の要旨は採用されなかったとされる（1982 年）。
- **出典**：S1（"submitted a summary detailing his observations to the Australian Gastroenterological Association" … "where he was categorically rejected"）
- **検証結果**：PARTIALLY_VERIFIED（レビューの記述）→「とされる」。年は台本で言わない。

### FACT-07
- **主張**：飲んだあと 3 日間は何も起きず、数日後に激しい吐き気と嘔吐。検査（内視鏡と生検）で胃の炎症と菌が確かめられた。
- **出典**：S1（"on the 7th day he woke up with severe nausea and vomiting" "on the 10th day he underwent a repeat endoscopy and biopsy, which showed massive inflammation"）、S3（ChatGPT の報告："For the next three days I had no symptoms" "On about the fifth to the eighth day I awoke very nauseated"）
- **検証結果**：PARTIALLY_VERIFIED（症状の日は資料で「7 日目」「5〜8 日目ごろ」と幅がある）→ 台本は「数日後」。
- **注意点**：「胃潰瘍になった」とは言わない（胃炎）。**まねしないよう画面に注意書き**。

### FACT-08
- **主張**：その後、菌を除くと潰瘍が再発しにくくなることが患者の研究で示され、1994 年、米国国立衛生研究所（NIH）の会議が、感染した潰瘍の患者に除菌を勧めた。
- **出典**：S4
- **検証結果**：PARTIALLY_VERIFIED（ChatGPT の報告。書誌は PubMed）

### FACT-09
- **主張**：2005 年、2 人はノーベル生理学・医学賞を受賞した。
- **出典**：S2
- **検証結果**：VERIFIED（検索の抜粋で複数一致）

### FACT-10
- **主張**：いま、ピロリ菌による胃潰瘍は、薬で菌を除いて治せる。
- **出典**：S2（"peptic ulcer disease is no longer a chronic, frequently disabling condition, but a disease that can be cured by a short regimen of antibiotics and acid secretion inhibitors"、検索の抜粋）
- **検証結果**：VERIFIED（検索の抜粋）

## 言わないこと

- 「マーシャルが初めて胃の細菌（ピロリ菌）を見つけた」／「誰も信じなかった」
- 「胃潰瘍はすべてピロリ菌が原因」／「自己実験で胃潰瘍になった」／「自己実験だけで証明された」
- 「イースターで 5 日間放置したら」（日数）／「ブタで失敗した」（未確認）／「妻にも黙って」（未確認）
- 「感染者の半分が胃がんになる」
