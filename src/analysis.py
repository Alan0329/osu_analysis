
# %%
from __future__ import annotations
from pathlib import Path
import mysql.connector
import statsmodels.api as sm
from scipy import stats
import seaborn as sns
from statsmodels.stats.multicomp import pairwise_tukeyhsd

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
sql = """
with diff as (
	select *, datediff(last_visit, join_date) as diff_day	
	from osu_users
)
select 
	user_type,
	sum(is_supporter = 1),
	ROUND(SUM(is_supporter)*1.0/COUNT(*), 4) AS supporter_ratio
from (
	select *, if(diff_day <= 7, "early_churn_users", if(diff_day > 30, "retained_users", "trial_users")) as user_type 
	from diff
) as dd
group by user_type;
"""

df = pd.read_sql(sql, engine)


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
        avg(max_combo * 1.0 / (stat_perfect + stat_great + stat_good + stat_ok + stat_meh + stat_miss)) as combo_rate
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
	combo_rate
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
# 假設 1：表現會影響留存
# 可以代表「表現」的指標：平均分數、score、miss_rate、combo_rate
perfomance_df = (
    df
    .dropna()
    .groupby("user_type", as_index=False)
    .agg({
        "avg_accuracy": "mean",
        "avg_score": "mean",
        "avg_miss_rate": "mean",
        "combo_rate": "mean"
    })
    .sort_values(by="avg_accuracy", ascending=True)
)
perfomance_df

# 結果
# early_churned users 平均準確率、分數最低、miss rate 皆最高；perfect combo 最低
 

# %%
# 細部遊玩的指標：平均的 great、ok、meh、miss
perfomance_df = (
    df
    .dropna()
    .groupby("user_type", as_index=False)
    .agg({
        "avg_stat_great": "mean",
        "avg_stat_ok": "mean",
        "avg_stat_meh": "mean",
        "avg_stat_miss": "mean"
    })
    .sort_values(by="avg_stat_great", ascending=True)
)
perfomance_df

# 結果
# early_churned users great、ok 最低；meh、miss 最高

# 綜合以上可能解釋：
    # 1. 玩越久，表現會越好
    # 2. 剛完，表現差。留下來的可能性就更低
        # - 命中率 (Accuracy)：明顯上升（0.74 → 0.78），顯示留得久的玩家在遊戲表現上更穩定。
        # - 平均得分 (Score)：穩定上升（約 上升70K），顯示他們持續投入遊玩、表現更佳。
        # - 錯誤率 (Miss Rate)：持續下降（0.078 → 0.060），挫折感可能下降。
        # - 完美連擊率 (Perfect Combo)：Trial 時期最高（0.531），Retained 微降（0.526），可能代表進入熟練期後挑戰更高難度譜面。
    


# %%
def run_anova(col):
    # 以 avg_accuracy 為例
    result = stats.f_oneway(
        df[df['user_type'] == 'early_churn_users'][col],
        df[df['user_type'] == 'trial_users'][col],
        df[df['user_type'] == 'retained_users'][col]
    )
    print(col, result)

run_anova(col='avg_accuracy')
run_anova(col='avg_score')
run_anova(col='avg_miss_rate')
run_anova(col='combo_rate')
run_anova(col='avg_stat_great')
run_anova(col='avg_stat_ok')
run_anova(col='avg_stat_meh')
run_anova(col='avg_stat_miss')

# acc、score、miss_score、great
# 三群命中率顯著不同。留得越久，命中率越高。
# 留存時間越長，平均分數越高，投入程度可能更深。
# 流失者錯誤率高，表示早期挫折感強。
# 命中「great」比例明顯差異，與技術表現一致。

# %%
def run_post_hoc_test(col):
    tukey = pairwise_tukeyhsd(
        endog=df[col], 
        groups=df['user_type'], 
        alpha=0.05
    )
    print(col)
    print(tukey)

run_post_hoc_test(col='avg_accuracy')
run_post_hoc_test(col='avg_score')
run_post_hoc_test(col='avg_miss_rate')
run_post_hoc_test(col='avg_stat_great')

# 
# 準確度：玩家若能在前 7～30 天內達到約 0.77 以上命中率，就有高機率進入留存階段。這代表「初期準確度提昇」是留存轉換的關鍵門檻。
# 分數：玩家若能在試玩期內持續達到較高得分(270K→320K)，也許以300K為目標，表示投入時間與學習曲線提升，留存機率更高。
# 錯誤率：高錯誤率的玩家容易在七天內離開。換句話說，**「降低初期挫折」**比提升高階挑戰更能改善留存。
# hit great：留存者不只是命中多，而是「命中品質」高。遊戲內若能強化「Great」命中的回饋感，可能促進成就感與持續動機。

# %%
sql = """
select *
from user_beatmaps
where beatmap_id is not null;
"""

df = pd.read_sql(sql, engine)

# %%
# 假設2：beatmap 類（難度等）：早期流失者玩的 beatmap，會與他是否留存有關
play_map_df = (
    df
    .groupby("user_type", as_index=False)
    .agg({
        "difficulty_rating": "mean",
        "favourite_count": "mean",
        "play_count": "mean",
    })
)
play_map_df

# 難度明顯提升
    # 若新手長期只接觸低難度內容，可能因缺乏刺激而流失 
    # 早期引導推薦可採「熱門→個人化」兩階段策略：
        # 7天內推薦熱門譜面（降低學習門檻）；
        # 7天後轉為依命中率推薦中階挑戰譜。 
# 譜面變冷門、遊玩次數變冷門
    # 短期玩家傾向玩「熱門或高人氣」內容。
    # 「個人化挑戰與深度投入」才是留存動力


# %%
run_anova(col='difficulty_rating')
run_anova(col='favourite_count')
run_anova(col='play_count')


# %%
run_post_hoc_test(col='difficulty_rating')
run_post_hoc_test(col='favourite_count')
run_post_hoc_test(col='play_count')
# 洞察： 玩家留存與「挑戰曲線」強烈相關。 從 Early → Trial → Retained，難度階層上升顯著。 顯示玩家在找到「適合自己挑戰強度」後，會更容易長期留在遊戲中。
# 洞察： Retained 玩家偏好冷門譜面。 反之，新手與試玩者更常追隨社群熱門（高收藏數）內容。 留存者逐漸形成「個人化偏好」，而非被社群潮流驅動。

# %%
