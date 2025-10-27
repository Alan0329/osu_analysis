# --- bootstrap: auto-install required packages into a local folder (_deps) ---
from __future__ import annotations
import sys, subprocess, importlib, os
from pathlib import Path

# 1) 需要的套件（左：pip 套件名；右：對應 import 名稱，用於檢查是否已存在）
REQUIRED = {
    "requests": "requests",
    "mysql-connector-python": "mysql.connector",   # pip 套件名與 import 名不同
    "SQLAlchemy": "sqlalchemy",
    "pandas": "pandas",
    "python-dotenv": "dotenv",
}

# 2) 將安裝目標指向專案內的本地資料夾，避免動到全域環境
ROOT = Path(__file__).resolve().parent
TARGET_DIR = ROOT / "_deps"
os.makedirs(TARGET_DIR, exist_ok=True)

# 3) 先把 _deps 放進 sys.path，確保後續可被 import
if str(TARGET_DIR) not in sys.path:
    sys.path.insert(0, str(TARGET_DIR))

def ensure_packages():
    """檢查缺少的套件並用目前這個 Python 執行檔安裝到 _deps。"""
    missing = []
    for pip_name, import_name in REQUIRED.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pip_name)

    if not missing:
        return

    # 使用目前執行中的 Python 解譯器來呼叫 pip，避免版本/環境錯配
    cmd = [
        sys.executable, "-m", "pip", "install",
        "--disable-pip-version-check",
        "--no-input",
        f"--target={str(TARGET_DIR)}",
        *missing,
    ]
    # 靜默一點輸出；如果要看細節可移除 --quiet
    cmd.insert(4, "--quiet")

    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print("[bootstrap] pip 安裝失敗，命令：", " ".join(cmd))
        raise

    # 安裝後重新載入路徑與模組
    import site
    site.addsitedir(str(TARGET_DIR))
    for pip_name, import_name in REQUIRED.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            print(f"[bootstrap] 仍無法匯入：{import_name}（對應 pip: {pip_name}）")
            raise

ensure_packages()
# %%
from __future__ import annotations

import json
import os
import time
import requests
from pathlib import Path
from typing import Deque, Iterable, Iterator, List, Optional
import mysql.connector
from sqlalchemy import create_engine

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
        existing_ids = pd.read_sql("SELECT user_id FROM osu_users", engine)["user_id"].tolist()
    except Exception as exc:  # pragma: no cover - depends on DB availability
        print(f"[ERROR] Unable to load existing IDs: {exc}")
        return set()
    return set(existing_ids)

def wait_for_rate_limit(
    rate_window: Deque[tuple[float, int]],
    processed_in_window: int,
    batch_size: int,
    rate_limit: int = RATE_LIMIT_PER_MINUTE,
    window_seconds: int = 60,
) -> int:
    """Ensure we do not exceed the rate limit before sending the next request."""
    while True:
        now = time.monotonic()
        while rate_window and now - rate_window[0][0] >= window_seconds:
            _, count = rate_window.popleft()
            processed_in_window -= count

        if processed_in_window + batch_size <= rate_limit:
            rate_window.append((now, batch_size))
            return processed_in_window + batch_size

        oldest_timestamp, _ = rate_window[0]
        sleep_time = max(window_seconds - (now - oldest_timestamp), 0.05)
        time.sleep(sleep_time)

# %%
token_headers = get_header_data_token()
final_url = url_builder(path="users")

engine = create_db_engine(DATABASE_PASSWORD)
existing_ids = load_existing_ids(engine)

# %%
id_start = 36776050
id_end = 38533966
ids = list(range(36776050, 38533967))  # 注意 range 的終點要加 1
remain_ids = [i for i in ids if i not in existing_ids]
groups = [remain_ids[i: i+50] for i in range(0, len(remain_ids), 50)]
total_users = len(ids)

# %%
processed_users = 0
last_request_time = time.perf_counter() - MIN_SECONDS_PER_REQUEST


# %%
for index, group in enumerate(groups, start=1):
    # 速率限制：確保每次請求間隔至少 MIN_SECONDS_PER_REQUEST 秒
    elapsed = time.perf_counter() - last_request_time
    if elapsed < MIN_SECONDS_PER_REQUEST:
        time.sleep(MIN_SECONDS_PER_REQUEST - elapsed)

    while True:
        params = {
        "ids[]": group  # 取第一組來測試
        }

        resp = requests.get(
            url=final_url,
            headers=token_headers, 
            params=params
        )

        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")

            if retry_after is None:
                # 官方沒給 retry_after 就保守地等待一整分鐘。
                time.sleep(30)
            else:
                # 有提供 retry_after 就用對方建議的秒數等待。
                try:
                    time.sleep(float(retry_after))
                except ValueError:
                    time.sleep(30)
            continue

        break

    
    resp.raise_for_status()

    df = pd.DataFrame(resp.json()["users"])
    save_df = clean_df(df)
    if not save_df.empty:
        save_df.to_sql(
            name="osu_users",
            con=engine,
            if_exists="append",
            index=False,
            chunksize=GROUP_SIZE,
        )
        existing_ids.update(save_df["user_id"].tolist())

    processed_users += len(group)
    print(
        f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 已處理 {processed_users}/{total_users} 筆使用者資料 (第 {index}/{len(groups)} 組)。"
    )



# %%
connection = mysql.connector.connect(
        host='localhost',
        port=3306,
        database='osudb',
        user='root',
        password=DATABASE_PASSWORD,
        charset="utf8mb4", 
        collation="utf8mb4_0900_ai_ci"
)
# %%
cursor = connection.cursor()
cursor.execute('SELECT * FROM osu_users;')
record = cursor.fetchone()
print(record)

# %%
cursor.close()
connection.close()

# %%
# 假設 engine 已經建立
import pandas as pd
from sqlalchemy import text



# 再寫入
to_insert_df.to_sql(name='osu_users', con=engine, if_exists='append', index=False, chunksize=50)

