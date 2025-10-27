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
    statistics_rulesets JSON,
    `groups` JSON,
    team JSON
);

select * from osu_users

CREATE TABLE IF NOT EXISTS user_beatmaps (
    user_id BIGINT NOT NULL,
    beatmap_id BIGINT NOT NULL,
    beatmapset_id BIGINT,
    difficulty_rating DECIMAL(10,4),
    `mode` VARCHAR(32),
    `status` VARCHAR(32),
    artist VARCHAR(255),
    title VARCHAR(255),
    favourite_count INT,
    play_count INT,
    genre_id INT,
    
    PRIMARY KEY (user_id, beatmap_id),
    CONSTRAINT fk_user_beatmaps_user FOREIGN KEY (user_id) REFERENCES osu_users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_scores (
    score_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    beatmap_id BIGINT NOT NULL,
    started_at DATETIME,
    ended_at DATETIME,
    accuracy DECIMAL(6,5),
    `rank` VARCHAR(8),
    has_replay TINYINT(1) DEFAULT 0,
    is_perfect_combo TINYINT(1) DEFAULT 0,
    total_score BIGINT,
    max_combo INT,
    statistics_ok INT,
    statistics_meh INT,
    statistics_great INT,
    statistics_ignore_hit INT,
    statistics_ignore_miss INT,
    statistics_large_tick_hit INT,
    statistics_slider_tail_hit INT,
    statistics_miss INT,
    statistics_good INT,
    statistics_perfect INT,
    statistics_small_tick_miss INT,
    statistics_small_tick_hit INT,
    statistics_large_tick_miss INT,
    statistics_small_bonus INT,
    statistics_large_bonus INT,
    statistics_combo_break INT,
    statistics_legacy_combo_increase INT,
    
    CONSTRAINT fk_user_scores_user FOREIGN KEY (user_id) REFERENCES osu_users(user_id) ON DELETE CASCADE
);

