# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')



# %%
from __future__ import annotations
from pathlib import Path
import mysql.connector
import statsmodels.api as sm
from scipy import stats
import seaborn as sns

from sqlalchemy import create_engine
import os
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "data"
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")

# %%
def create_db_engine(password: str):
    return create_engine(
        "mysql+mysqlconnector://{user}:{password}@{host}:{port}/{dbname}?charset=utf8mb4".format(
            user="root",
            password=password,
            host="localhost",
            port=3306,
            dbname="osudb",
        ),
        connect_args={"charset": "utf8mb4"},
        echo=False,
    )

engine = create_db_engine(DATABASE_PASSWORD)
# 假設你的資料已讀入：df
# df = pd.read_sql(sql, engine)  # 你已經做過
sql = """
with user_data as(
    select 
        user_id,
        country_code,
        datediff(last_visit, join_date) as days_since_join,
        is_supporter,
        statistics_rulesets
    from osu_users
    where join_date >= '2025-04-01'
        and is_bot = 0
        and is_deleted = 0
),
group_user_scores as(
    select 
        user_id, 
        count(*) as play_counts,
        avg(accuracy) as avg_accuracy,
        avg(total_score) as avg_score,
        avg(max_combo) as avg_combo,
        avg(stat_perfect) as avg_stat_perfect,
        avg(stat_great)   as avg_stat_great, 
        avg(stat_good)    as avg_stat_good,
        avg(stat_ok)      as avg_stat_ok,
        avg(stat_meh)     as avg_stat_meh,
        avg(stat_miss)    as avg_stat_miss,
        avg(stat_miss * 1.0 / (stat_perfect + stat_great + stat_good + stat_ok + stat_meh + stat_miss)) as avg_miss_rate,
        avg(max_combo * 1.0 / (stat_perfect + stat_great + stat_good + stat_ok + stat_meh + stat_miss)) as perfect_combo_rate
    from user_scores
    where beatmap_id is not NULL
    group by user_id 
)
select 
	group_user_scores.user_id,
	user_type,
	country_code,
	days_since_join,
	is_supporter,
	statistics_rulesets,
    play_counts,
	avg_accuracy,
	avg_score,
	avg_combo,
	avg_stat_perfect, -- osu!mania
	avg_stat_great, 
	avg_stat_good, -- osu!mania
	avg_stat_ok,
	avg_stat_meh,
	avg_stat_miss,
	avg_miss_rate,
	perfect_combo_rate
from group_user_scores
left join (
    select distinct user_id, user_type
    from user_beatmaps
) as user_type
on group_user_scores.user_id = user_type.user_id
left join user_data
on group_user_scores.user_id = user_data.user_id;
"""

df = (
    pd.read_sql(sql, engine)
    .dropna()
)
# %%
# --- 1. 初步檢查資料結構 ---
print("資料維度 (rows, cols):", df.shape)
print("欄位型別與缺值情況：")
print(df.info())

# 敘述統計
print("數值欄位簡要統計：")
print(df.describe().T)

# user_type 樣本數分佈
print("user_type 樣本數分佈：")
print(df['user_type'].value_counts(dropna=False))


# %%
# --- 2. 檢查資料分佈（單變量分析） ---
num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
print("數值欄位為：", num_cols)

for col in num_cols:
    plt.figure(figsize=(6,4))
    sns.histplot(df[col].dropna(), kde=True)
    plt.title(f'Histogram & KDE of {col}')
    plt.xlabel(col)
    plt.ylabel('Count')
    plt.tight_layout()
    plt.show()

# 若你想看偏態（skewness）與峰態（kurtosis）
skew_vals = df[num_cols].skew().sort_values(ascending=False)
kurt_vals = df[num_cols].kurt().sort_values(ascending=False)
print("數值欄位偏態：")
print(skew_vals)
print("數值欄位峰態：")
print(kurt_vals)

# %%
# --- 3. 分群比較（你的 user_type）— 單變量在群組間差異視覺化 ---
# 假設 user_type 欄位是分類欄位
cat_col = 'user_type'
for col in num_cols:
    plt.figure(figsize=(8,5))
    sns.boxplot(x=cat_col, y=col, data=df)
    plt.title(f'Boxplot of {col} by {cat_col}')
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.show()

# 或者：violinplot
for col in num_cols:
    plt.figure(figsize=(8,5))
    sns.violinplot(x=cat_col, y=col, data=df, inner="quartile")
    plt.title(f'Violinplot of {col} by {cat_col}')
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.show()

# %%
# --- 5. 變數間關係（雙變量 / 多變量） ---
# 相關係數矩陣（只對數值欄位）
corr = df[num_cols].corr()
plt.figure(figsize=(10,8))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", square=True)
plt.title('Correlation Matrix')
plt.tight_layout()
plt.show()

# %%
# 若想針對 user_type 做分群的相關性差異，可先分群再做矩陣
for grp in df[cat_col].unique():
    sub = df[df[cat_col]==grp]
    sub_corr = sub[num_cols].corr()
    plt.figure(figsize=(8,6))
    sns.heatmap(sub_corr, annot=False, cmap="coolwarm")
    plt.title(f'Corr Matrix for {grp}')
    plt.tight_layout()
    plt.show()

# %%
# 若有兩個你特別關注的欄位，例如 avg_accuracy vs avg_miss_rate
plt.figure(figsize=(6,5))
sns.scatterplot(x='avg_accuracy', y='avg_miss_rate', hue=cat_col, data=df)
plt.title('avg_accuracy vs avg_miss_rate by user_type')
plt.tight_layout()
plt.show()

# %%
# --- 6. 處理特殊情況：極端值（Outliers）／分佈偏態很大者 ---
# 你可用 IQR 方法來列出潛在極端值
for col in num_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    low  = Q1 - 1.5 * IQR
    high = Q3 + 1.5 * IQR
    outliers = df[(df[col] < low) | (df[col] > high)]
    print(f"欄位 {col} 潛在 outlier 數量：{outliers.shape[0]}")

# 如你發現某些欄位偏態很大（skewness 很高），你可做資料轉換
# 例如：
# df['log_avg_score'] = np.log1p(df['avg_score'])
# 然後再看新的分佈

# %%
# --- 7. 為檢定做準備（確保各群樣本量／變異情況） ---
print(df.groupby(cat_col)[num_cols].agg(['count','mean','std']).T)

# %%
# 確認每個 user_type 的樣本數是否夠多、變異是否為零
for grp in df[cat_col].unique():
    sub = df[df[cat_col] == grp]
    print(grp, "樣本數 = ", sub.shape[0])
