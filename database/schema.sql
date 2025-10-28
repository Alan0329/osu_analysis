CREATE DATABASE IF NOT EXISTS osudb
	CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS osu_users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    country_code CHAR(2),
    join_date DATETIME,
    last_visit DATETIME,
    is_active BOOLEAN,
    is_bot BOOLEAN,
    is_deleted BOOLEAN,
    is_online BOOLEAN,
    is_supporter BOOLEAN,
    stat_rulesets JSON,
    `groups` JSON,
    team JSON
);

drop table user_beatmaps;
CREATE TABLE IF NOT EXISTS user_beatmaps (
	id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    user_type VARCHAR(32) NOT NULL,
    beatmap_id BIGINT,
    beatmapset_id BIGINT,
    difficulty_rating DECIMAL(10,4),
    `mode` VARCHAR(32),
    `status` VARCHAR(32),
    artist VARCHAR(255),
    title VARCHAR(255),
    favourite_count INT,
    play_count INT,
    genre_id INT
);

drop table user_scores;
CREATE TABLE IF NOT EXISTS user_scores (
	id BIGINT PRIMARY KEY AUTO_INCREMENT,
    score_id BIGINT,
    user_id BIGINT NOT NULL,
    beatmap_id BIGINT,
    started_at DATETIME,
    ended_at DATETIME,
    accuracy DECIMAL(6,5),
    `rank` VARCHAR(8),
    has_replay TINYINT(1) DEFAULT 0,
    is_perfect_combo TINYINT(1) DEFAULT 0,
    total_score BIGINT,
    max_combo INT,
    stat_ok INT,
    stat_meh INT,
    stat_great INT,
    stat_ignore_hit INT,
    stat_ignore_miss INT,
    stat_large_tick_hit INT,
    stat_slider_tail_hit INT,
    stat_miss INT,
    stat_good INT,
    stat_perfect INT,
    stat_small_tick_miss INT,
    stat_small_tick_hit INT,
    stat_large_tick_miss INT,
    stat_small_bonus INT,
    stat_large_bonus INT,
    stat_combo_break INT,
    stat_legacy_combo_increase INT
);

