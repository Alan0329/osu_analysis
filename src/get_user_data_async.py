# %%
from __future__ import annotations

import asyncio
import json
import os
import time
import requests
from typing import List, Optional, Set
from pathlib import Path
import mysql.connector
from sqlalchemy import create_engine

import httpx
import pandas as pd
import requests
from dotenv import load_dotenv

# ===== 常數設定 =====
DATA_DIR = Path(__file__).parent.parent / "data"
RATE_LIMIT_PER_MINUTE = 1200
GROUP_SIZE = 50
MIN_SECONDS_PER_REQUEST = 60 / RATE_LIMIT_PER_MINUTE # 每次請求間隔秒數
MAX_PARALLEL_REQUESTS = 16 # 並行處理的群組上限（可依環境調整）

# ===== 載入環境變數 =====
load_dotenv()
CLIENT_ID = os.getenv("OSU_CLIENT_ID")
CLIENT_SECRET = os.getenv("OSU_CLIENT_SECRET")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")


# %%
def get_header_data_token():
    # 先拿到通行證（OAuth2 access token）
    osu_url = "https://osu.ppy.sh/oauth/token"
    my_headers = {
            "Accept":"application/json",
            "Content-Type":"application/x-www-form-urlencoded"
    }
    my_data = {
        "client_id":CLIENT_ID,
        "client_secret":CLIENT_SECRET,
        "grant_type":"client_credentials", # 用戶端認證 
        "scope":"public" # 只要讀公開資料、或不綁特定使用者：用戶端認證
    }

    resp = requests.post(
        osu_url,
        headers=my_headers,
        data=my_data
    )
    resp.raise_for_status()

    token = resp.json()["access_token"]

    token_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",

    }
    
    return token_headers

def url_builder(path: str) -> str:
    base_osu_api_url = "https://osu.ppy.sh/api/v2"
    final_url = f"{base_osu_api_url}/{path}"
    
    return final_url


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


def match_id_get_joindate(row):
    if os.path.exists(f"{DATA_DIR}/cleaned_first_last_ids.csv"):
        daily_first_last = pd.read_csv(f"{DATA_DIR}/cleaned_first_last_ids.csv")
    mask = daily_first_last.apply(lambda x: (row >= x['first_id']) & (row <= x['last_id']), axis=1)
    matched = daily_first_last[mask]

    return matched['join_day'].values[0]
    # return pd.to_datetime(matched['join_day'].values[0])

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    # 清理並選取需要的欄位
    clean_df = (
        df
        .assign(join_date=df['id'].map(match_id_get_joindate))
        .assign(statistics_rulesets=df['statistics_rulesets'].apply(lambda x: json.dumps(x) if isinstance(x, dict) else None))
        .assign(groups=df['groups'].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else None))
        .assign(team=df['team'].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else None))
        [[
            "id", "username", "country_code", 
            "join_date", "last_visit",
            "is_active", "is_bot", "is_deleted", "is_online", "is_supporter", 
            "statistics_rulesets", "groups", "team"
        ]]
        .rename(columns={
            "id": "user_id"
            }
        )
    )
    
    return clean_df

def _load_id_ranges() -> Optional[pd.DataFrame]:
    csv_path = DATA_DIR / "cleaned_first_last_ids.csv"
    if not csv_path.exists():
        return None
    return pd.read_csv(csv_path)

# %%
class TokenBucketLimiter:
    """控制每分鐘可執行的請求次數。
    - capacity: 桶容量（預設 = 每分鐘速率）。
    - rate_per_sec: 每秒補充的 token 數（= rate_per_minute / 60）。
    - acquire(): 取得 1 枚 token ，不足時等待足夠時間。
    """ 
    def __init__(self, rate_per_minute: int, capacity: Optional[float] = None) -> None:
        """
        :param rate_per_minute: 每分鐘允許的請求數。
        :param capacity: 桶容量，預設等於每分鐘速率。
        """
        self.rate_per_sec = rate_per_minute / 60.0
        self.capacity = float(capacity if capacity is not None else rate_per_minute)
        self._tokens = self.capacity
        self._updated_at = asyncio.get_running_loop().time()
        self._lock = asyncio.Lock()

    async def acquire(self, n: float = 1.0) -> None:
        # 同時間只允許一個協程在裡面操作 _tokens
        async with self._lock:
            while True:
                now = asyncio.get_running_loop().time()
                elapsed = now - self._updated_at
                # 補充 token 
                self._tokens = min(self.capacity, self._tokens + elapsed * self.rate_per_sec)
                self._updated_at = now

                if self._tokens >= n:
                    self._tokens -= n
                    return

                # 計算需要等待的時間
                deficit = n - self._tokens
                wait_s = deficit / self.rate_per_sec if self.rate_per_sec > 0 else 0.05
                await asyncio.sleep(wait_s)

async def load_existing_ids(engine) -> Set[int]:
    """非阻塞讀取既有 user_id。"""
    def _read_sql():
        try:
            return pd.read_sql("SELECT user_id FROM osu_users", engine)["user_id"].tolist()
        except Exception as exc:
            print(f"[ERROR] Unable to load existing IDs: {exc}")
        return []

    return set(await asyncio.to_thread(_read_sql))


async def write_dataframe(engine, save_df: pd.DataFrame) -> None:
    if save_df.empty:
        return

    def _to_sql():
        save_df.to_sql(
        name="osu_users",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=GROUP_SIZE,
        )

    await asyncio.to_thread(_to_sql)

async def fetch_group(
    client: httpx.AsyncClient,
    final_url: str,
    token_headers: dict,
    group: List[int],
    limiter: TokenBucketLimiter,
) -> dict:
    """抓取一組 50 IDs 的使用者資料；每次實際發送請求前都先 acquire()。"""
    while True:
        await limiter.acquire()  # 每個真正的 HTTP 請求都會扣一枚令牌
        try:
            resp = await client.get(url=final_url, headers=token_headers, params={"ids[]": group}, timeout=60)
        except httpx.RequestError as e:
            print(f"[WARN] Network error: {e}. Backing off 5s...")
            await asyncio.sleep(5)
            continue

        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            delay = 30.0
            if retry_after is not None:
                try:
                    delay = float(retry_after)
                except ValueError:
                    delay = 30.0
            print(f"[RATE LIMIT] 429 received. Sleeping {delay:.1f}s then retry...")
            await asyncio.sleep(delay)
            continue

        if resp.status_code == 401:
            resp.raise_for_status()  # 交由上層刷新 token

        resp.raise_for_status()
        return resp.json()

# %%

async def process_group(
    index: int,
    group: List[int],
    client: httpx.AsyncClient,
    final_url: str,
    token_headers_box: dict,
    engine,
    id_ranges: Optional[pd.DataFrame],
    limiter: TokenBucketLimiter,
    progress_lock: asyncio.Lock,
    counters: dict,
    parallel_sem: asyncio.Semaphore,
):
    async with parallel_sem:
        try:
            try:
                data = await fetch_group(client, final_url, token_headers_box["headers"], group, limiter)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    print("[AUTH] 401 unauthorized. Refreshing token and retrying once...")
                    token_headers_box["headers"] = await get_header_data_token(client)
                    data = await fetch_group(client, final_url, token_headers_box["headers"], group, limiter)
                else:
                    raise

            df = pd.DataFrame(data.get("users", []))
            save_df = clean_df(df, id_ranges)
            await write_dataframe(engine, save_df)
        finally:
            async with progress_lock:
                counters["processed_users"] += len(group)
                print(f"[進度] 已處理 {counters['processed_users']}/{counters['total_users']} 筆使用者資料 (第 {index}/{counters['total_groups']} 組)。")


async def main():
    async with httpx.AsyncClient(http2=True) as client:
        token_headers = get_header_data_token()
        token_headers_box = {"headers": token_headers}  # 可變容器，供刷新後共享
        final_url = url_builder(path="users")

        engine = create_db_engine(DATABASE_PASSWORD)
        existing_ids = await load_existing_ids(engine)

        # 設定要抓取的 ID 範圍
        id_start = 36776050
        id_end = 38533966
        ids = list(range(id_start, id_end + 1))
        remain_ids = [i for i in ids if i not in existing_ids]

        groups: List[List[int]] = [remain_ids[i:i + GROUP_SIZE] for i in range(0, len(remain_ids), GROUP_SIZE)]
        total_users = len(remain_ids)
        total_groups = len(groups)

        # 載入 join_day 對照表
        id_ranges = _load_id_ranges()

        # 建立限流器與同步元件
        limiter = TokenBucketLimiter(RATE_LIMIT_PER_MINUTE)
        progress_lock = asyncio.Lock()
        parallel_sem = asyncio.Semaphore(MAX_PARALLEL_REQUESTS)
        counters = {"processed_users": 0, "total_users": total_users, "total_groups": total_groups}

        tasks = [
            asyncio.create_task(
                process_group(
                    index=i,
                    group=g,
                    client=client,
                    final_url=final_url,
                    token_headers_box=token_headers_box,
                    engine=engine,
                    id_ranges=id_ranges,
                    limiter=limiter,
                    progress_lock=progress_lock,
                    counters=counters,
                    parallel_sem=parallel_sem,
                )
            )
            for i, g in enumerate(groups, start=1)
        ]

        # 等待全部完成
        await asyncio.gather(*tasks)
        print("[完成] 全部群組處理完成！")

# %%
# ---- 通用啟動入口（可在 CLI 或已運行的事件迴圈中呼叫）----
async_entry_task = None


def start():
    """在任意環境啟動 main()：
    - 若無事件迴圈：使用 asyncio.run(main())。
    - 若已有事件迴圈（如 Jupyter / IPython）：建立任務並回傳，供呼叫端 await。
    回傳：
    - 在已運行事件迴圈時，回傳 asyncio.Task 以便 await；否則回傳 None。
    """
    global async_entry_task
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # 沒有正在運行的事件迴圈，直接 run
        asyncio.run(main())
        return None
    else:
        # 已有事件迴圈（例如 Jupyter），建立任務並交由外部 await
        async_entry_task = loop.create_task(main())
        return async_entry_task


if __name__ == "__main__":
    start()


# %%
