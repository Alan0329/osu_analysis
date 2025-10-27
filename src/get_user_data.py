# %%
import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
import mysql.connector


# %%
# 載入環境變數
load_dotenv()
CLIENT_ID = os.getenv("OSU_CLIENT_ID")
CLIENT_SECRET = os.getenv("OSU_CLIENT_SECRET")

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

# %%
base_osu_api_url = "https://osu.ppy.sh/api/v2"
user_id = 36776050
# mode: osu, taiko, fruits, mania
mode = "osu"
params = None
path = f"users/{user_id}/{mode}"
final_url = f"{base_osu_api_url}/{path}"

# %%
"""
TODO: 
要找到各個 id 的 join_date，只能用 users/{user_id}/{mode} 這個 endpoint
寫一個抽樣的程式，抽一個 id 去拿取他的 join_date
假設抽 1200 個 id，抽 10 次，因為 id 是按照 join_date 排序的，所以可以一次跳 1200 個 id
再來用抽出來的 id，去找出每個 id 的 join_date
"""
id_start = 36776050
id_end = 38533966
ids = list(range(36776050, 38533967))  # 注意 range 的終點要加 1


# %%
# # %%
# base_osu_api_url = "https://osu.ppy.sh/api/v2"
# path = f"users"
# final_url = f"{base_osu_api_url}/{path}"



# %%
id_start = 36776050
id_end = 38533966
ids = list(range(36776050, 38533967))  # 注意 range 的終點要加 1
groups = [ids[i: i+50] for i in range(0, len(ids), 50)]


# params = {
#     "ids[]": groups[0]  # 取第一組來測試
# }

# %%
resp = requests.get(
    url=final_url,
    headers=token_headers, 
    params=params
)


# %%

df = pd.DataFrame(resp.json()["users"])

# %%
save_df = (
    df[[
        "id", "username", "country_code", 
        "is_active", "is_bot", "is_deleted", "is_online", "is_supporter", 
        "last_visit", "statistics_rulesets",
        "groups", "team"
    ]]
)

"""
TODO: 
根據這個  columns
寫一個 SQL CREATE TABLE 指令
"""