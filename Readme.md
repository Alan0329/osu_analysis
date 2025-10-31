[中文版]()

# 專案情境 
osu 是一款在 Windows 平台上的節奏音樂遊戲，在 2007 年由 peppy 與開發夥伴推出因其免費、豐富的遊玩模式與可自己設計譜面而受社群推崇主要包含四種模式：「osu!」、「osu!taiko」、「osu!CatchtheBeat」以及「osu!mania」「osu!」模式隨著節奏，用鼠標點擊譜面上的圈圈、拖曳滑條和旋轉轉盤，為最早開發的模式，也是最主要的玩法；「su!Taiko」模式需要隨著節奏，根據螢幕的指示，在適當的時機敲擊；「osu!CatchTheBeat」模式需要操作角色接住從天而降的水果；「osu!mania」模式遊玩時會有音符或滑條從螢幕上方不同位置落下，玩家需要在特定時間按下或按住對應鍵

osu 的營運資金來源大多為玩家的捐款以及 osu!store 的周邊商品銷售因此 supporter（贊助者）變多，對於團隊才有經營下去的動力本專案假設我為該團隊的資料分析師，為 osu 團隊提供建議，目標是提出用於優化遊玩體驗並提升團隊經營的動力

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
    * 監控：建制儀表板追蹤「遊玩與留存 metric」，驗證策略成效

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

## 假設一：表現面（Early → Trial → Retained）：
### 1) 整體表現指標 
|user_type|	平均 accuracy|	平均 miss_rate|	combo_rate|	平均 score|
| -- | -- | -- | -- | -- |
|early_churn_users|	74.68%|	7.88%|	48.46%|	278177.8539|
|trial_users|	77.58%|	6.24%|	53.10%|	329033.7658|
|retained_users|	78.52%|	6.05%|	52.57%|	349591.75|

  * early churn users：平均 accuracy、combo rate、score 最低；miss rate 最高  
  * retained users 則跟 early churn users 相反

### 2) 命中品質（Great／OK／Meh／Miss）
| user_type         | 平均 great 數 |   平均 ok 數 |  平均 meh 數 | 平均 miss 數 |
| ----------------- | ---------: | --------: | --------: | --------: |
| early_churn_users | 145.496496 | 42.620968 | 13.059185 | 20.562129 |
| trial_users       | 168.824349 | 44.580404 | 11.897840 | 17.744256 |
| retained_users    | 193.991318 | 46.432895 | 12.176749 | 19.496928 |

* great：retained users 最高
* ok：early churn users 最低
* meh/miss：early churn users 皆最高

* 綜合以上
  1. 玩越久，表現會越好 
  2. 剛玩，表現差留下來的可能性就更低
  
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
  * 三群命中率顯著不同表現好 → 成就感高 → 留存高
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
1. 準確度：玩家若能在前 7～30 天內達到**約 0.77 以上命中率**，就有高機率進入留存階段，
2. 分數：玩家若能在試玩期內持續達到較高得分(270K→320K)，以 300K 為目標，留存機率更高
3. 錯誤率：高錯誤率的玩家容易在七天內離開，所以**「降低初期挫折」**比提升高階挑戰更能改善留存
4. hit great：留存者不只是命中多，而是「命中品質」高遊戲內若能強化「Great」命中的回饋感，可能促進成就感與持續動機



## 假設二：內容面（beatmap）：

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

1. 挑戰曲線是留存關鍵：不同皆端難度顯著上升玩家找到「合適的挑戰強度」，更容易長期留下
2. 從「熱門導入」到「個人化深化」：Retained 明顯傾向低收藏/少被玩的譜面，代表長期動機來自個人化風格養成，而非單純追隨社群熱門
3. 產品策略（兩段式推薦）：
   * 0–7 日（新手）：以熱門且易上手為主，快速建立成功體驗、降低挫折
   * 7–30 日（試用）：依玩家 accuracy / miss pattern 推薦中階難度；引導難度漸進提升
   * 30+ 日（留存）：持續供給高難度、偏冷門、貼個人風格的譜面，支撐長期動機；此階段再銜接 supporter 引導



## 結論
1. 新手期（0–7 日）
* 依表現推薦不同難度譜面：依前 3–5 局的 accuracy/miss pattern，自動推薦略低於玩家當前實力的譜面，確保能打出 acc ≥ 0.75 的成功體驗
* 即時回饋設計：放大 Great 命中的視覺/音效；對高 miss pattern（節奏偏差/長押不穩/連打失誤）給「可關閉、極短提示」
* 新手目標卡：設「7 日內達成 acc ≥ 0.77 或 score ≥ 300K」的任務，提供小獎勵

2. 試用期（7–30 日）
* 第 1 週仍以熱門作緩衝；隨 accuracy 穩定（~0.77）逐步推中階難度譜面（比常玩譜面 +0.1～0.2 難度）
* 中階挑戰任務：以 acc、miss_rate、Great 比例為主題的挑戰，避免只追分數
* 輕社群連結：推薦「相似表現玩家」常玩的曲目清單

3. 留存期（>30 日）
* 個人化曲目池：持續供給高難度、偏冷門且符合玩家歷史偏好的曲目，維持挑戰新鮮感
* 長期成就系統：建立可長期累積的非付費成就，在此基礎上再溫和引導 Supporter 升級（外觀、徽章、紀念物）



# 附錄：ERD、方法、限制、代碼連結

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

## 程式碼 / Tableau 儀表板連結：
  * [程式碼連結]([https://github.com/Alan0329/osu_analysis/tree/main])
  * [儀表板連結]