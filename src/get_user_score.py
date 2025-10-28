# %%
import math
from __future__ import annotations
from ossapi import Ossapi
import json
import os
import time
import requests
from pathlib import Path
from typing import Deque, Iterable, Iterator, List, Optional
import mysql.connector
from sqlalchemy import create_engine
import random

import pandas as pd
import requests
from dotenv import load_dotenv

DATA_DIR = Path(__file__).parent.parent / "data"
RATE_LIMIT_PER_MINUTE = 1200
GROUP_SIZE = 50
MIN_SECONDS_PER_REQUEST = 60 / (RATE_LIMIT_PER_MINUTE)


# %%
# 載入環境變數
load_dotenv()
CLIENT_ID = os.getenv("OSU_CLIENT_ID")
CLIENT_SECRET = os.getenv("OSU_CLIENT_SECRET")
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


def load_existing_ids(engine) -> set:
    try:
        existing_ids = pd.read_sql("SELECT user_id, beatmap_id FROM user_beatmaps", engine)
    except Exception as exc:  # pragma: no cover - depends on DB availability
        print(f"[ERROR] Unable to load existing IDs: {exc}")
        return set()
    return dict(zip(existing_ids['user_id'], existing_ids['beatmap_id']))


def clean_user_scores_to_df(user_scores, beatmap_id, user_id):
    rows = []
    if user_scores:
        for obj in user_scores:
            row = {
                'user_id': user_id,
                'score_id': obj.id,
                'beatmap_id': beatmap_id,
                'started_at': obj.started_at,
                'ended_at': obj.ended_at,
                'accuracy': obj.accuracy,
                'rank': str(obj.rank),
                'has_replay': 1 if obj.has_replay else 0,
                'is_perfect_combo': 1 if obj.is_perfect_combo else 0,
                'total_score': obj.total_score,
                'max_combo': obj.max_combo,
                'stat_ok': obj.statistics.ok or 0,
                'stat_meh': obj.statistics.meh or 0,
                'stat_great': obj.statistics.great or 0,
                'stat_ignore_hit': obj.statistics.ignore_hit or 0,
                'stat_ignore_miss': obj.statistics.ignore_miss or 0,
                'stat_large_tick_hit': obj.statistics.large_tick_hit or 0,
                'stat_slider_tail_hit': obj.statistics.slider_tail_hit or 0,
                'stat_miss': obj.statistics.miss or 0,
                'stat_good': obj.statistics.good or 0,
                'stat_perfect': obj.statistics.perfect or 0,
                'stat_small_tick_miss': obj.statistics.small_tick_miss or 0,
                'stat_small_tick_hit': obj.statistics.small_tick_hit or 0,
                'stat_large_tick_miss': obj.statistics.large_tick_miss or 0,
                'stat_small_bonus': obj.statistics.small_bonus or 0,
                'stat_large_bonus': obj.statistics.large_bonus or 0,
                'stat_combo_break': obj.statistics.combo_break or 0,
                'stat_legacy_combo_increase': obj.statistics.legacy_combo_increase or 0,
            }
            rows.append(row)
    else:
        # 當 user_scores 為空時，建立一筆空值 row
        rows.append({
            'user_id': user_id,
            'score_id': None,
            'beatmap_id': None,
            'started_at': None,
            'ended_at': None,
            'accuracy': None,
            'rank': None,
            'has_replay': None,
            'is_perfect_combo': None,
            'total_score': None,
            'max_combo': None,
            'stat_ok': None,
            'stat_meh': None,
            'stat_great': None,
            'stat_ignore_hit': None,
            'stat_ignore_miss': None,
            'stat_large_tick_hit': None,
            'stat_slider_tail_hit': None,
            'stat_miss': None,
            'stat_good': None,
            'stat_perfect': None,
            'stat_small_tick_miss': None,
            'stat_small_tick_hit': None,
            'stat_large_tick_miss': None,
            'stat_small_bonus': None,
            'stat_large_bonus': None,
            'stat_combo_break': None,
            'stat_legacy_combo_increase': None,
        })
    df = pd.DataFrame(rows)
    return df


# %%
engine = create_db_engine(DATABASE_PASSWORD)
api_ids_dict = load_existing_ids(engine)
existing  = pd.read_sql("SELECT user_id, beatmap_id FROM user_scores", engine)
existing_set = set()
for uid, val in zip(existing['user_id'], existing['beatmap_id']):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        existing_set.add((uid, None))
    else:
        existing_set.add((uid, val))

remain = {}
for uid, val in api_ids_dict.items():  # 假設你的 dict 是 {user_id: value}
    if val is None or (isinstance(val, float) and math.isnan(val)):
        compare_val = None
    else:
        compare_val = val
    if (uid, compare_val) not in existing_set:
        remain[uid] = compare_val

total_users = len(remain)
save_df = pd.DataFrame()

# %%
api = Ossapi(CLIENT_ID, CLIENT_SECRET)
user_scores = api.beatmap_user_scores(beatmap_id=2807834, user_id=37869961)


# %%
processed_users = 0
last_request_time = time.perf_counter() - MIN_SECONDS_PER_REQUEST

# %%
for user_id, beatmap_id in remain.items():

    # 速率限制：確保每次請求間隔至少 MIN_SECONDS_PER_REQUEST 秒
    elapsed = time.perf_counter() - last_request_time
    if elapsed < MIN_SECONDS_PER_REQUEST:
        time.sleep(MIN_SECONDS_PER_REQUEST - elapsed)
    try:
        if beatmap_id is None:
            user_scores = None
        else:
            user_scores = api.beatmap_user_scores(
                beatmap_id=beatmap_id, 
                user_id=user_id
            )
    except ValueError as e:
        error_msg = str(e)
        if "couldn't be found" in error_msg:
            # 標記為無資料，但不讓程式中斷
            user_scores = None
        else:
            # 未知錯誤，重新拋出或記錄後跳過
            print(f"Unexpected error for beatmap_id={beatmap_id}, user_id={user_id}: {error_msg}")
            continue
        
    save_df = clean_user_scores_to_df(user_scores, beatmap_id, user_id)

    if not save_df.empty:
        save_df.to_sql(
            name="user_scores",
            con=engine,
            if_exists="append",
            index=False,
            chunksize=len(save_df),
        )

        processed_users += 1

    print(
        f"已處理 {processed_users}/{total_users} 筆使用者資料。"
    )



# %%
rows = []
for obj in user_scores:
    row = {
        'user_id': user_id,
        'score_id': obj.id,
        'beatmap_id': beatmap_id,
        'started_at': obj.started_at,
        'ended_at': obj.ended_at,
        'accuracy': obj.accuracy,
        'rank': str(obj.rank),
        'has_replay':  1 if obj.has_replay else 0,
        'is_perfect_combo': 1 if obj.is_perfect_combo else 0,
        'total_score': obj.total_score,
        'max_combo': obj.max_combo,
        'stat_ok': obj.statistics.ok or 0,
        'stat_meh': obj.statistics.meh or 0,
        'stat_great': obj.statistics.great or 0,
        'stat_ignore_hit': obj.statistics.ignore_hit or 0,
        'stat_ignore_miss': obj.statistics.ignore_miss or 0,
        'stat_large_tick_hit': obj.statistics.large_tick_hit or 0,
        'stat_slider_tail_hit': obj.statistics.slider_tail_hit or 0,
        'stat_miss': obj.statistics.miss or 0,
        'stat_good': obj.statistics.good or 0,
        'stat_perfect': obj.statistics.perfect or 0,
        'stat_small_tick_miss': obj.statistics.small_tick_miss or 0,
        'stat_small_tick_hit': obj.statistics.small_tick_hit or 0,
        'stat_large_tick_miss': obj.statistics.large_tick_miss or 0,
        'stat_small_bonus': obj.statistics.small_bonus or 0,
        'stat_large_bonus': obj.statistics.large_bonus or 0,
        'stat_combo_break': obj.statistics.combo_break or 0,
        'stat_legacy_combo_increase': obj.statistics.legacy_combo_increase or 0,
    }
    rows.append(row)
df = pd.DataFrame(rows)

# %%
obj._beatmap.mode