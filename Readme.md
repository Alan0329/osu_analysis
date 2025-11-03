[中文版點此](https://github.com/Alan0329/osu_analysis?tab=readme-ov-file#%E5%B0%88%E6%A1%88%E6%83%85%E5%A2%83)

# Project Context
osu! is a rhythm game for Windows released in 2007 by peppy and collaborators. Its free-to-play model, rich variety of gameplay modes, and user-created beatmaps have earned it strong community support. The four primary modes are “osu!”, “osu!taiko,” “osu!CatchTheBeat,” and “osu!mania.” In “osu!”, players follow the rhythm by clicking circles, dragging sliders, and spinning spinners—the earliest and most central mode. “osu!taiko” requires timed hits according to on-screen prompts. In “osu!CatchTheBeat,” players control a character to catch falling fruit. In “osu!mania,” notes and sliders fall from different lanes at the top of the screen, and players must press or hold the corresponding keys at the right time.

Most operating funds for osu! come from player donations and merchandise sales via the osu!store. Growing the number of supporters (donors) is therefore essential to sustaining the team. In this project, I assume the role of the team’s data analyst and provide recommendations to the osu! team, with the goal of improving gameplay experience and strengthening the team’s motivation to operate and grow.

* **North Star Metric: Growth in the number and share of Supporters**
* **Key Question: How can we increase the number of Supporters?**

# Summary & Actionable Insights
1. Player segmentation by days since join:  
   * Early (< 7), Trial (7–30), Retained (> 30)  
2. Supporter status correlates with retention; it cannot be “forced in the novice phase.  
   * Share rises with retention time (Early ≈ 0% → Trial 0.06% → Retained 0.26%).  
3. Set **user retention** as the drive metric and analyze two levers:  
   * Performance (score/accuracy, etc.)
   * Content (difficulty/popularity, etc.)  
4. Results:  
   * Performance: retention is strongly tied to early performance.  
   * Content: retained users prefer higher difficulty and rely less on “popular” maps.  
5. Actionable moves:
   * **Newcomers (< 7 days):** reduce frustration and create quick wins (focus: score, error rate, accuracy, feedback for Great hits) to promote Early → Trial.
   * **Trial (7–30 days):** start recommending more challenging, personalized maps to drive Trial → Retained.
   * **Retained (30+ days):** keep supplying higher-difficulty, less mainstream but personalized content; add non-monetized “long-term achievements,” then nudge upgrades to Supporter.

# Analysis
Player segmentation (by days since join)
|     Range | Suggested Segment Name | Description                                         |
| --------: | ---------------------- | --------------------------------------------------- |
|  < 7 days | Early Churn Users      | Leave within seven days; emphasizes “quick exit.”   |
| 7–30 days | Trial Users            | Trial phase; temporarily retained but not stable.   |
| > 30 days | Retained Users         | Stable active cohort (still playing after 30 days). |

## 1. Relationship between Supporter status and retention

![alt text](<data/Supporter 比例圖_Eng.png>)

* The proportion of Supporters increases with retention time.  
  → Supporter status is the result of retention, not something to push in the early phase.
* Therefore, treat user retention as the **drive metric**: keep newcomers first, then convert to Supporter.  
  → The main sub-question becomes: **How do we make early churners more likely to stay?**  
* Two hypotheses:  
  1. **Performance** (score, combo, etc.): Early performance correlates with whether users stay.  
  2. **Beatmap** (difficulty, etc.): Maps played early on relate to whether users stay.  

## Hypothesis 1: Performance (Early → Trial → Retained)

### 1) Overall performance metrics

| user_type         | Average accuracy | Average miss rate | Combo rate | Average score |
| ----------------- | ---------------: | ----------------: | ---------: | ------------: |
| early_churn_users |           74.68% |             7.88% |     48.46% |    278,177.85 |
| trial_users       |           77.58% |             6.24% |     53.10% |    329,033.77 |
| retained_users    |           78.52% |             6.05% |     52.57% |    349,591.75 |

* Early churn users: lowest average accuracy/combo/score; highest miss rate.
* Retained users show the opposite pattern.

### 2) Hit quality (Great/OK/Meh/Miss)

| user_type         | Avg. Great | Avg. OK | Avg. Meh | Avg. Miss |
| ----------------- | ---------: | ------: | -------: | --------: |
| early_churn_users |   145.4965 | 42.6210 |  13.0592 |   20.5621 |
| trial_users       |   168.8243 | 44.5804 |  11.8978 |   17.7443 |
| retained_users    |   193.9913 | 46.4329 |  12.1767 |   19.4969 |

* Great: highest for retained users.
* OK: lowest for early churn users.
* Meh/Miss: highest for early churn users.

**In sum:**
1. The longer players stick around, the better they perform.
2. If early performance is poor, the likelihood of staying drops.

#### Do these apparent differences hold statistically? One-way ANOVA

| Metric         |  p-value | Significant (α = 0.05) |
| -------------- | -------: | :--------------------: |
| avg_accuracy   |  0.00134 |            ✅           |
| avg_score      | 0.000112 |            ✅           |
| avg_miss_rate  |  0.00427 |            ✅           |
| combo_rate     |   0.4244 |            ❌           |
| avg_stat_great | 0.000180 |            ✅           |
| avg_stat_ok    |   0.4500 |            ❌           |
| avg_stat_meh   |   0.6504 |            ❌           |
| avg_stat_miss  |   0.6973 |            ❌           |
> Note: significance at p < 0.05.

* Significant differences: accuracy, score, miss rate, Great.
  * Accuracy differs across groups: better performance → stronger sense of achievement → higher retention.
  * Longer retention associates with higher average scores, suggesting deeper engagement.
  * Early churners’ higher error rates point to stronger early frustration.
  * “Great” hits differ markedly and align with overall skill.

#### Which pairs differ? Tukey HSD

##### 1) Accuracy (avg_accuracy)
| Significant pairs | Mean diff (group2 − group1) | Conclusion                                    |
| ----------------- | --------------------------: | --------------------------------------------- |
| early → retained  |                 **+0.0384** | **Retained significantly higher than early.** |
| early → trial     |                 **+0.0290** | **Trial significantly higher than early.**    |
> **Early churn users lowest; trial and retained are similar**: after the novice phase, accuracy gaps narrow.

##### 2) Score (avg_score)
| Significant pairs | Mean diff (group2 − group1) | Conclusion                                    |
| ----------------- | --------------------------: | --------------------------------------------- |
| early → retained  |                 **+71,414** | **Retained significantly higher than early.** |
| early → trial     |                 **+50,856** | **Trial significantly higher than early.**    |
> **Early churn users’ scores are significantly lower**; differences between trial and retained are not significant.

##### 3) Miss rate (avg_miss_rate)
| Significant pairs | Mean diff (group2 − group1) | Conclusion                                   |
| ----------------- | --------------------------: | -------------------------------------------- |
| early → retained  |                 **−0.0183** | **Retained significantly lower than early.** |
| early → trial     |                 **−0.0164** | **Trial significantly lower than early.**    |
> **Early churn users have a significantly higher miss rate**; trial vs. retained is not significant.

##### 4) Great hits (avg_stat_great)
| Significant pairs | Mean diff (group2 − group1) | Conclusion                                    |
| ----------------- | --------------------------: | --------------------------------------------- |
| early → retained  |                  **+48.49** | **Retained significantly higher than early.** |
| trial → retained  |                  **−25.17** | **Retained significantly higher than trial.** |
> **Great hits: retained > trial > early churn.**

* Core gaps lie between early churners and the other two groups: early churners show notably lower accuracy/score and higher miss rates.
* Trial vs. retained show few significant differences: after clearing the novice phase, performance gaps shrink. The next lens is **content difficulty/personalized recommendations**.

### Hypothesis 1 Summary
1. **Accuracy:** Hitting ~0.77 accuracy within the first 7–30 days strongly predicts moving into the retained stage.
2. **Score:** Consistently reaching higher scores during the trial phase (270K → 320K; target ~300K) increases the chance of retention.
3. **Miss rate:** Players with high miss rates tend to leave within seven days. **Reducing early frustration** does more for retention than pushing advanced challenges.
4. **Great hits:** Retained players don’t just hit more—they hit **better**. Amplifying feedback for **Great** hits may boost achievement and motivation.

## Hypothesis 2: Content (beatmaps)

### 1) Content metrics (Early → Trial → Retained)
| user_type         | difficulty_rating | favourite_count |    play_count |
| ----------------- | ----------------: | --------------: | ------------: |
| early_churn_users |            2.6016 |      3,944.2247 |     9,650,914 |
| trial_users       |            2.9030 |      4,029.2165 |     8,798,438 |
| retained_users    |            3.2584 |      3,086.3565 |     6,873,808 |

* **Difficulty:** rises from Early → Trial → Retained.
* **Popularity (favorites/plays):** Retained users engage with **less** popular maps—more niche and personalized.

### 2) ANOVA (α = 0.05)

| Metric            |  p-value | Significant |
| ----------------- | -------: | :---------: |
| difficulty_rating | 7.90e−22 |      ✅      |
| favourite_count   | 3.49e−25 |      ✅      |
| play_count        | 3.28e−18 |      ✅      |

> All three differ significantly across groups.

### 3) Tukey HSD (significant pairs only)

#### **difficulty_rating**

| Significant pairs | Mean diff (group2 − group1) | Conclusion                                    |
| ----------------- | --------------------------: | --------------------------------------------- |
| early → retained  |                 **+0.6568** | **Retained significantly higher than early.** |
| early → trial     |                 **+0.3014** | **Trial significantly higher than early.**    |
| trial → retained  |                 **+0.3554** | **Retained significantly higher than trial.** |

#### **favourite_count**

| Significant pairs | Mean diff (group2 − group1) | Conclusion                                                                  |
| ----------------- | --------------------------: | --------------------------------------------------------------------------- |
| early → retained  |                 **−857.87** | **Retained significantly lower than early** (less dependent on popularity). |
| trial → retained  |                 **−942.86** | **Retained significantly lower than trial.**                                |

#### **play_count**

| Significant pairs | Mean diff (group2 − group1) | Conclusion                                                     |
| ----------------- | --------------------------: | -------------------------------------------------------------- |
| early → retained  |              **−2,777,106** | **Retained significantly lower than early** (less mainstream). |
| trial → retained  |              **+1,924,630** | **Trial significantly higher than retained.**                  |

> Early → Trial is **not significant** for favourite_count and play_count (p > 0.05).

### Hypothesis 2 Conclusions
1. **Challenge curve drives retention:** Difficulty increases across segments; finding the “right challenge level” supports long-term play.
2. **From popular onboarding to personalized depth:** Retained users clearly lean toward lower-favorite/less-played maps, suggesting long-term motivation is built on personal style rather than chasing what’s trending.
3. **Product strategy (two-stage funnel):**
   * **Days 0–7 (Newcomers):** prioritize popular, easy-to-pick-up maps to build quick wins and reduce frustration.
   * **Days 7–30 (Trial):** recommend mid-tier difficulty based on each player’s accuracy/miss pattern; gradually ramp up difficulty.
   * **30+ days (Retained):** keep supplying high-difficulty, less mainstream, and personally aligned content to sustain long-term motivation; introduce Supporter prompts at this stage.

# Conclusions

1. **Newcomers (0–7 days)**
   * **Difficulty-fitting recommendations:** Use accuracy/miss patterns from the first 3–5 plays to auto-recommend maps slightly below current skill, ensuring acc ≥ 0.75 and quick success.
   * **Real-time feedback:** Emphasize visual/audio feedback for **Great** hits
   * **Newcomer goal card:** “Achieve acc ≥ 0.77 or score ≥ 300K within 7 days” with small rewards.

2. **Trial (7–30 days)**
   * Keep some popular maps as a buffer in week 1; as accuracy stabilizes (~0.77), gradually push mid-tier difficulty (e.g., +0.1–0.2 over commonly played maps).
   * **Mid-tier challenge missions:** Focus on acc, miss rate, and Great ratio rather than raw score alone.
   * **Lightweight social features:** Recommend beatmaps commonly played by “similar-performance players.”

3. **Retained (> 30 days)**
   * **Personalized pool:** Continue serving high-difficulty, less mainstream maps aligned with historical preferences to maintain novelty.
   * **Long-term achievement system:** Allow non-monetized, accumulative achievements; on that foundation, gently guide Supporter upgrades (cosmetics, badges, commemoratives).

# Appendix: ERD, Methods, Limitations

## ERD

![alt text](<data/OSU Database ERD.png>)

## Methods

* Stratified sampling: 500 users per tier (< 7 / 7–30 / > 30) with join_date ≥ April 1, 2025; bots/deleted excluded.
* Tests: one-way ANOVA (Accuracy/Score/Miss, etc.), with Tukey HSD for pairwise comparisons; significant results as above.
* Metric definitions: Retained = days_since_join > 30; Trial = 7–30; Early = < 7.

## Limitations

* `last_visit` may be NULL (privacy/missing); mitigated via stratified sampling and proxy behavioral metrics, but representativeness should still be disclosed.
* Beatmap popularity is a site-wide metric and not a complete proxy for individual preference.
* Region/mode interactions not included; can be added in future work.




# 專案情境 
osu 是一款在 Windows 平台上的節奏音樂遊戲，在 2007 年由 peppy 與開發夥伴推出因其免費、豐富的遊玩模式與可自己設計譜面而受社群推崇主要包含四種模式：「osu!」、「osu!taiko」、「osu!CatchtheBeat」以及「osu!mania」「osu!」模式隨著節奏，用鼠標點擊譜面上的圈圈、拖曳滑條和旋轉轉盤，為最早開發的模式，也是最主要的玩法；「su!Taiko」模式需要隨著節奏，根據螢幕的指示，在適當的時機敲擊；「osu!CatchTheBeat」模式需要操作角色接住從天而降的水果；「osu!mania」模式遊玩時會有音符或滑條從螢幕上方不同位置落下，玩家需要在特定時間按下或按住對應鍵。

osu 的營運資金來源大多為玩家的捐款以及 osu!store 的周邊商品銷售因此 supporter（贊助者）變多，對於團隊才有經營下去的動力本專案假設我為該團隊的資料分析師，為 osu 團隊提供建議，目標是提出用於優化遊玩體驗並提升團隊經營的動力。

* **北極星指標：Supporter 數量與占比成長**
* **關鍵問題：「如何讓 Supporter 數量增長」**

# 摘要與可行洞察
1. 玩家分群：依加入後天數分為  
    * Early（<7）、Trial（7–30）、Retained（>30）
2. Supporter 與留存相關，不是新手期就能硬推  
    * 占比隨留存時間上升（Early≈0% → Trial 0.06% → Retained 0.26%）
3. 把「用戶留存」設定為 drive metric，分析兩條路：  
    * 表現（score/accuracy）
    * 內容（難度／熱門度等）
4. 結果顯示：  
    * 表現面：留存與早期表現高度相關  
    * 內容面：留存者傾向更高難度、較不依賴熱門度的譜面
5. 可行洞察：  
    * 「新手期（< 7 天）」：降低挫折、創造快速成功經驗（主要改進：分數、錯誤率、準確度、great 命中回饋），讓 Early 有機會晉升 Trial  
    * 「Trail（7–30 天）」：開始推薦有難度、個人化的譜面來遊玩，提升 Trial → Retained 的轉換  
    * 「老手（30+ 天）」 ：持續推薦高難度、偏冷門，但個人化的內容；增加非付費也能累積的「長期成就」，穩定後再引導升級 Supporter 

# 分析過程
玩家分層（以加入後天數）

 |範圍|建議名稱|說明|  
 |  --  | --|--  |
 | <7 天 | Early Churn Users | 七天內就流失，強調「很快離開」|
 | 7–30 天 | Trial Users | 試用期，暫時留存但未穩定|
 | >30 天 | Retained Users | 穩定活躍群體（30日後仍在玩）|

## 1. Supporter 與留存關係

![alt text](<data/Supporter 比例圖.png>)

* Supporter 比例隨留存時間上升  
→ Supporter 是留存之後的成果，不是能在「早期」就能推動的行為

* 因此將用戶留存設為驅動指標（Drive Metric）：應先把新手留住，再談 Supporter  
→ 所以主要問題拆解為：「如何讓早期流失玩家更可能留下來？」  

* 進一步提出以下假設：  
  1. 表現類（score、combo 等）：早期流失者的遊玩表現，會與他是否留存有關  
  2. beatmap 類（難度等）：早期流失者玩的 beatmap，會與他是否留存有關

## 假設一：表現面（Early → Trial → Retained）
### 1) 整體表現指標 
|user_type|	平均 accuracy|	平均 miss_rate|	combo_rate|	平均 score|
| -- | -- | -- | -- | -- |
|early_churn_users|	74.68%|	7.88%|	48.46%|	278177.85|
|trial_users|	77.58%|	6.24%|	53.10%|	329033.77|
|retained_users|	78.52%|	6.05%|	52.57%|	349591.75|

  * early churn users：平均 accuracy、combo rate、score 最低；miss rate 最高  
  * retained users 則跟 early churn users 相反

### 2) 命中品質（Great／OK／Meh／Miss）
| user_type         | 平均 great 數 |   平均 ok 數 |  平均 meh 數 | 平均 miss 數 |
| ----------------- | ---------: | --------: | --------: | --------: |
| early_churn_users |   145.4965 | 42.6210 |  13.0592 |   20.5621 |
| trial_users       |   168.8243 | 44.5804 |  11.8978 |   17.7443 |
| retained_users    |   193.9913 | 46.4329 |  12.1767 |   19.4969 |

* great：retained users 最高
* ok：early churn users 最低
* meh/miss：early churn users 皆最高

* 綜合以上
  1. 玩越久，表現會越好 
  2. 剛玩，表現差，留下來的可能性就更低
  
#### 但看起來有差異，實際上真的有差異嗎？來進行 ANOVA 檢定

| 指標             |      p 值 | 顯著 (α=0.05) |
| -------------- | -------: | :---------: | 
| avg_accuracy   |  0.00134 |      ✅      | 
| avg_score      | 0.000112 |      ✅      | 
| avg_miss_rate  |  0.00427 |      ✅      | 
| combo_rate     |   0.4244 |      ❌      | 
| avg_stat_great | 0.000180 |      ✅      | 
| avg_stat_ok    |   0.4500 |      ❌      | 
| avg_stat_meh   |   0.6504 |      ❌      | 
| avg_stat_miss  |   0.6973 |      ❌      |
> 註：顯著性以 p<0.05 判定

* 有顯著差異：accuracy、score、miss rate、great  
  * 三群命中率顯著不同，表現好 → 成就感高 → 留存高
  * 留存時間越長，平均分數越高，投入程度可能更深
  * 流失者錯誤率高，表示早期挫折感強
  * 命中「great」比例明顯差異，與技術表現一致

#### 實際上差異，是哪兩群之間有差異，還是皆有差異呢？進行 Tukey HSD 檢定

#### 1) 命中率 avg_accuracy
| 顯著組合             | 平均差 (group2 − group1) | 結論                      |
| ---------------- | --------------------: | ----------------------- |
| early → retained  |           **+0.0384** | **retained  明顯高於 early ** |
| early → trial     |           **+0.0290** | **trial  明顯高於 early **    |

> **early churn users 最低；trial users 與 retained users 類似**：跨過新手期後，命中率差距趨緩

#### 2) 分數 avg_score
| 顯著組合             | 平均差 (group2 − group1) | 結論                      |
| ---------------- | --------------------: | ----------------------- |
| early → retained|           **+71,414** | **retained 明顯高於 early** |
| early → trial  |           **+50,856** | **trial 明顯高於 early churn users**    |
> **early churn users 分數顯著偏低**；trial users 與 retained users 差異不顯著

#### 3) 錯誤率 avg_miss_rate  
| 顯著組合   | 平均差 (group2 − group1) | 結論 |
| ---------------- | --------------------: | ----------------------- |
| early → retained |           **−0.0183** | **retained 明顯低於 early** |
| early → trial    |           **−0.0164** | **trial 明顯低於 early**           |
> **early churn users 錯誤率顯著較高**；trial users 與 retained users 差異不顯著

#### 4) 命中品質 avg_stat_great
| 顯著組合             | 平均差 (group2 − group1) | 結論                               |
| ---------------- | --------------------: | ----------------------- |  
| early → retained |            **+48.49** | **retained Great 數明顯高於 early**   |
| trial → retained |            **−25.17** | **retained 明顯高於 trial** |
> **Great 命中：retained users > trial users > early churn users**

* 核心差異都發生在 early churn users vs（trial users/retained users）：early churn users 的 accuracy/score 明顯較低、miss_rate 明顯較高
* Trial 與 Retained 多數指標無顯著差：代表跨過新手期後後，表現差距縮小；後續將以「內容難度/個人化推薦」來說明


### 假設一總結
1. 準確度：玩家若能在前 7～30 天內達到**約 0.77 以上命中率**，就有高機率進入留存階段
2. 分數：玩家若能在試玩期內持續達到較高得分(270K→320K)，以 300K 為目標，留存機率更高
3. 錯誤率：高錯誤率的玩家容易在七天內離開，所以「降低初期挫折」比提升高階挑戰更能改善留存
4. hit great：留存者不只是命中多，而是「命中品質」高遊戲內若能強化「Great」命中的回饋感，可能促進成就感與持續動機

## 假設二：內容面（beatmap）

### 1) 內容指標均值（Early → Trial → Retained）

| user_type         | difficulty_rating | favourite_count |    play_count |
| ----------------- | ----------------: | --------------: | ------------: |
| early_churn_users |            2.6016 |      3,944.2247 |     9,650,914 |
| trial_users       |            2.9030 |      4,029.2165 |     8,798,438 |
| retained_users    |        **3.2584** |  **3,086.3565** | **6,873,808** |

* 難度：Early → Trial → Retained，逐漸上升
* 熱門度（收藏/被玩次數）：Retained 反而較低，趨向冷門與個人化內容

### 2) ANOVA（α=0.05）

| 指標                |      p 值 |  顯著 |
| ----------------- | -------: | :-: |
| difficulty_rating | 7.90e-22 |  ✅  |
| favourite_count   | 3.49e-25 |  ✅  |
| play_count        | 3.28e-18 |  ✅  |

> 三項皆顯著：難度、收藏數、被玩次數在三群之間均存在顯著差異

### 3) Tukey HSD（僅列顯著組合）

#### **difficulty_rating**

| 顯著組合             | 平均差 (group2 − group1) | 結論                      |
| ---------------- | --------------------: | ----------------------- |
| early → retained |           **+0.6568** | **retained 明顯高於 early** |
| early → trial    |           **+0.3014** | **trial 明顯高於 early**    |
| trial → retained |           **+0.3554** | **retained 明顯高於 trial** |

#### **favourite_count**

| 顯著組合             | 平均差 (group2 − group1) | 結論                              |
| ---------------- | --------------------: | ------------------------------- |
| early → retained |           **−857.87** | **retained 明顯低於 early**（較不依賴熱門） |
| trial → retained |           **−942.86** | **retained 明顯低於 trial**         |

#### **play_count**

| 顯著組合             | 平均差 (group2 − group1) | 結論                            |
| ---------------- | --------------------: | ----------------------------- |
| early → retained |        **−2,777,106** | **retained 明顯低於 early**（偏非主流） |
| trial → retained |        **+1,924,630** | **trial 明顯高於 retained**       |
> early → trial 在 favourite_count、play_count **不顯著**（p>0.05）


### 假設二結論（行動化）

1. 挑戰曲線是留存關鍵：不同階段難度顯著上升，玩家找到「合適的挑戰強度」，更容易長期留下
2. 從熱門到個人化：Retained 明顯傾向低收藏/少被玩的譜面，代表長期動機來自個人化風格養成，而非單純追隨社群熱門
3. 產品策略（兩段式推薦）：
   * 0–7 日（新手）：以熱門且易上手為主，快速建立成功體驗、降低挫折
   * 7–30 日（試用）：依玩家 accuracy / miss pattern 推薦中階難度；引導難度漸進提升
   * 30+ 日（留存）：持續供給高難度、偏冷門、貼個人風格的譜面，支撐長期動機；此階段再銜接 supporter 引導



## 結論
1. 新手期（0–7 日）
    * 依表現推薦不同難度的譜面：依照新手遊玩的 accuracy/miss pattern，自動推薦略低於玩家當前實力的譜面，確保能打出 acc ≥ 0.75 的成功體驗
    * 即時回饋設計：放大 Great 命中的視覺/音效
    * 新手目標卡：設「7 日內達成 acc ≥ 0.77 或 score ≥ 300K」的任務，提供小獎勵

2. 試用期（7–30 日）
    * 第 1 週仍以熱門作緩衝；隨 accuracy 穩定（~0.77）逐步推中階難度譜面（例如：比常玩譜面 +0.1～0.2 難度）
    * 中階挑戰任務：以 acc、miss_rate、Great 比例為主題的挑戰，避免只在乎分數
    * 社群連結：推薦「相似表現玩家」常玩的譜面清單

3. 留存期（>30 日）
    * 個人化譜面：持續供給高難度、偏冷門且符合玩家歷史偏好的譜面，維持挑戰新鮮感
    * 長期成就系統：建立可長期累積的非付費成就，在此基礎上再溫和引導 Supporter 升級（外觀、徽章、紀念物）



# 附錄：ERD、方法、限制

## ERD
![alt text](<data/OSU Database ERD.png>)

## 方法
- 分層抽樣：<7 / 7–30 / >30 各 500 人（join_date ≥ 2025-04-01；排除 bot/deleted）
- 檢定：單因子 ANOVA（Accuracy/Score/Miss 等）、Tukey HSD 做兩兩比較；結果顯著如上
- 指標定義：Retained = days_since_join > 30；Trial = 7–30；Early = <7

## 限制
* `last_visit` 可能為 NULL（隱私/缺值），已以分層樣本與替代行為指標緩解；仍需在報告中揭露樣本代表性
* Beatmap 熱門度為全站指標，並非個人偏好完整代理
* 未納入地區/模式交互作用，後續可擴充
