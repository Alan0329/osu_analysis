# %%
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


def load_existing_ids(engine, select_type) -> set:
    if select_type == "new_users":
        where_clause = "datediff(last_visit, join_date) <= 7"
    elif select_type == "about_leave_users":
        where_clause = "datediff(last_visit, join_date) > 7 and datediff(last_visit, join_date) <= 30"
    elif select_type == "masters_users":
        where_clause = "datediff(last_visit, join_date) > 30"
    else:
        raise ValueError(f"Unknown select_type: {select_type}")
    
    select_query = f"""
    select user_id
    from osu_users
    where join_date >= '2025-04-01'
        and {where_clause};
    """

    try:
        existing_ids = pd.read_sql(select_query, engine)["user_id"].tolist()
    except Exception as exc:  # pragma: no cover - depends on DB availability
        print(f"[ERROR] Unable to load existing IDs: {exc}")
        return set()
    return set(existing_ids)

def clean_user_beatmaps_to_df(user_beatmaps, user_id, user_type):
    rows = []
    if user_beatmaps:
        for obj in user_beatmaps:
            row = {
                'user_id': user_id,
                'user_type': user_type,
                'beatmap_id': obj.beatmap_id,
                'beatmapset_id': obj._beatmap.beatmapset_id,
                'difficulty_rating': obj._beatmap.difficulty_rating,
                'mode': str(obj._beatmap.mode),
                'status': str(obj._beatmap.status),
                'artist': obj.beatmapset.artist,
                'title': obj.beatmapset.title,
                'favourite_count': obj.beatmapset.favourite_count,
                'play_count': obj.beatmapset.play_count,
            }
            rows.append(row)
    else:
        # 當無資料時，建立一筆 “空值” row，但保留 user_id、user_type
        rows.append({
            'user_id': user_id,
            'user_type': user_type,
            'beatmap_id': None,
            'beatmapset_id': None,
            'difficulty_rating': None,
            'mode': None,
            'status': None,
            'artist': None,
            'title': None,
            'favourite_count': None,
            'play_count': None,
        })
    df = pd.DataFrame(rows)
    return df



# %%
api = Ossapi(CLIENT_ID, CLIENT_SECRET)
user_beatmaps = api.user_beatmaps(user_id=36776050, type='most_played', limit=100)


# %%
engine = create_db_engine(DATABASE_PASSWORD)
new_users_id = load_existing_ids(engine, select_type="new_users")
mid_users_id = load_existing_ids(engine, select_type="about_leave_users")
masters_users_id = load_existing_ids(engine, select_type="masters_users")

# %%
random.seed(42) # 設定 seed
new_sample = random.sample(list(new_users_id), 500)
mid_sample = random.sample(list(mid_users_id), 500)
masters_sample = random.sample(list(masters_users_id), 500)


# %%
existing_ids = pd.read_sql("SELECT user_id FROM user_beatmaps", engine)["user_id"].tolist()
remain_ids = [i for i in masters_sample if i not in existing_ids]
total_users = len(remain_ids)
save_df = pd.DataFrame()


# %%
processed_users = 0
last_request_time = time.perf_counter() - MIN_SECONDS_PER_REQUEST

# %%
for user_type in ['new_users', 'about_leave_users', 'masters_users']:
    if user_type == 'new_users':
        sample_ids = new_sample
    elif user_type == 'about_leave_users':
        sample_ids = mid_sample
    elif user_type == 'masters_users':
        sample_ids = masters_sample

    existing_ids = set(pd.read_sql("SELECT user_id FROM user_beatmaps", engine)["user_id"].tolist())
    remain_ids = [i for i in sample_ids if i not in existing_ids]
    total_users = len(remain_ids)
    save_df = pd.DataFrame()

    processed_users = 0
    last_request_time = time.perf_counter() - MIN_SECONDS_PER_REQUEST

    for user_id in remain_ids:
        # 速率限制：確保每次請求間隔至少 MIN_SECONDS_PER_REQUEST 秒
        elapsed = time.perf_counter() - last_request_time
        if elapsed < MIN_SECONDS_PER_REQUEST:
            time.sleep(MIN_SECONDS_PER_REQUEST - elapsed)
        
        user_beatmaps = api.user_beatmaps(
            user_id=user_id, 
            type='most_played', 
            limit=100
        )
        save_df = clean_user_beatmaps_to_df(user_beatmaps, user_id, user_type)

        if not save_df.empty:
            save_df.to_sql(
                name="user_beatmaps",
                con=engine,
                if_exists="append",
                index=False,
                chunksize=len(save_df),
            )
            existing_ids.update(save_df["user_id"].tolist())
            processed_users += 1

        print(
            f"已處理 {processed_users}/{total_users} 筆使用者資料。"
        )



# %%
rows = []
for obj in user_beatmaps:
    row = {
        'user_id': user_id,
        'user_type': user_type,
        'beatmap_id': obj.beatmap_id,
        'beatmapset_id': obj._beatmap.beatmapset_id,
        'difficulty_rating': obj._beatmap.difficulty_rating,
        'mode': obj._beatmap.mode,
        'status': obj._beatmap.status,
        'artist': obj.beatmapset.artist,
        'title': obj.beatmapset.title,
        'favourite_count': obj.beatmapset.favourite_count,
        'play_count': obj.beatmapset.play_count,
    }
    rows.append(row)

df = pd.DataFrame(rows)

# %%
obj._beatmap.mode