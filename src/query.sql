select *, datediff(last_visit, join_date) as diff_day	
from osu_users;

select count(*)
from user_scores;

select *
from user_beatmaps;

with user_data as(
	select 
		user_id,
		country_code,
		datediff(last_visit, join_date) as days_since_join,
		is_supporter,
		statistics_rulesets
	from osu_users
	where join_date >= "2025-04-01"
		and is_bot = 0
		and is_deleted = 0
),
 	group_user_scores as(
	select 
		user_id, 
		avg(accuracy) as avg_accuracy,
		avg(total_score) as avg_score,
		avg(max_combo) as avg_combo,
		avg(stat_perfect) as avg_stat_perfect, -- osu!mania
		avg(stat_great) as avg_stat_great, 
		avg(stat_good) as avg_stat_good, -- osu!mania
		avg(stat_ok) as avg_stat_ok,
		avg(stat_meh) as avg_stat_meh,
		avg(stat_miss) as avg_stat_miss,
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

select user_id, count(beatmap_id)
from user_beatmaps
group by user_id;


select 
	user_type,
	avg(difficulty_rating) as avg_difficult_rating,
	avg(favourite_count) as avg_fav_count,
	avg(play_count) as avg_play_count
from user_beatmaps
group by user_type;


select distinct user_id, user_type
from user_beatmaps;





select 
	user_id, 
	avg(accuracy) as avg_accuracy,
	avg(total_score) as avg_score,
	avg(max_combo) as avg_combo,
	avg(stat_perfect) as avg_stat_perfect, -- osu!mania
	avg(stat_great) as avg_stat_great, 
	avg(stat_good) as avg_stat_good, -- osu!mania
	avg(stat_ok) as avg_stat_ok,
	avg(stat_meh) as avg_stat_meh,
	avg(stat_miss) as avg_stat_miss,
	avg(stat_miss * 1.0 / (stat_perfect + stat_great + stat_good + stat_ok + stat_meh + stat_miss)) as avg_miss_rate,
	avg(max_combo * 1.0 / (stat_perfect + stat_great + stat_good + stat_ok + stat_meh + stat_miss)) as perfect_combo_rate
from user_scores
where beatmap_id is not NULL
group by user_id; 


select *
from user_scores;

