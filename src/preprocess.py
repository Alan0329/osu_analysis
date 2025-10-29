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


# %%
# 你的 SQL 語句
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

df = pd.read_sql(sql, engine)

# %%
# 假設：表現會影響留存
# 表現：平均分數、score、miss_rate、combo_rate
perfomance_df = (
    df
    .groupby("user_type", as_index=False)
    .agg({
        "avg_accuracy": "mean",
        "avg_score": "mean",
        "avg_miss_rate": "mean",
        "perfect_combo_rate": "mean"
    })
    .sort_values(by="avg_accuracy", ascending=True)
)
perfomance_df

# trial users 平均準確率、分數最高、miss rate 最低
# early_churned users 平均 perfect_combo_rate 最高

df.user_type.value_counts()

# %%
# 以 avg_accuracy 為例
stats.f_oneway(
    df[df['user_type'] == 'early_churn_users']['avg_score'],
    df[df['user_type'] == 'trial_users']['avg_score'],
    df[df['user_type'] == 'retained_users']['avg_score']
)

# %%
df['user_type_code'] = df['user_type'].map({
    'new_users': 0,
    'about_leave_users': 1,
    'masters_users': 2
})


df[['user_type_code', 'avg_score', 'avg_accuracy', 'avg_miss_rate', 'perfect_combo_rate']].corr(method='spearman')

# %%

X = df[['avg_score', 'avg_accuracy', 'avg_miss_rate', 'perfect_combo_rate']]
y = df['user_type_code']  # 順序型
X = sm.add_constant(X)
model = sm.OLS(y, X).fit()
print(model.summary())

# %%
sns.boxplot(x='user_type', y='perfect_combo_rate', data=df)

# %%
diversity_df = (
    df
    .groupby("user_type", as_index=False)
    .agg({
        "avg_accuracy": "mean",
        "avg_score": "mean",
        "avg_miss_rate": "mean",
        "perfect_combo_rate": "mean"
    })
    .sort_values(by="avg_accuracy", ascending=True)
)
diversity_df

