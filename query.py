import json
import pandas as pd
import os

# 檔案路徑 (確保您在專案根目錄執行)
file_path = 'data/eatingwell_quick_easy_recipes_full.json'

# 檢查檔案是否存在
if not os.path.exists(file_path):
    print(f"錯誤：找不到檔案 {file_path}。請確認檔案路徑是否正確。")
    exit()

# 載入 JSON 數據
with open(file_path, 'r', encoding='utf-8') as f:
    recipe_dict = json.load(f)

# 將巢狀 Dictionary 轉換為 Pandas DataFrame
# .T (轉置) 讓 URL 變成索引，再用 reset_index 轉換成欄位
df = pd.DataFrame(recipe_dict).T.reset_index(names='Original_URL')

# 轉換時間欄位 (PT5M -> 5M) 以便後續分析
# 確保 Total_Time_Raw 中的值是字串，並移除 "PT" (P, T)
df['Total_Time_Clean'] = df['Total_Time_Raw'].str.replace('PT', '', regex=False).str.replace('M', 'M', regex=False)

print("--- 成功載入 DataFrame ---")
print(f"總共收集到的食譜數量：{len(df)} 份")
print("數據前 5 筆：")
print(df[['Title', 'Total_Time_Raw', 'Total_Time_Clean']].head())

# 將 DataFrame 設置為全域變數，以便後續步驟使用
# -------------------------------------------------------------

## 步驟二：查詢範例 - 尋找特定數據 (請在下方區塊繼續運行)
# 範例查詢 1: 查詢各種 Total_Time_Raw 的食譜數量
time_distribution = df['Total_Time_Raw'].value_counts()
print("\n[查詢結果 1] 食譜總時間 (原始格式) 分佈：")
print(time_distribution)

# 範例查詢 2: 尋找所有包含「salmon」（鮭魚）的食譜
# 必須使用 .apply(lambda...) 因為 Ingredients 欄位是一個列表 (List)
salmon_recipes_df = df[df['Ingredients'].apply(
    lambda x: any('salmon' in item.lower() for item in x)
)]

print(f"\n[查詢結果 2] 包含 'salmon' 的食譜總數：{len(salmon_recipes_df)} 份")
print("前 5 筆包含 salmon 的食譜：")
print(salmon_recipes_df[['Title', 'Total_Time_Raw', 'Original_URL']].head())

# 範例查詢 3: 尋找同時包含「kale」和「pear」的食譜
kale_recipes_df = df[df['Ingredients'].apply(
    lambda x: all(keyword in str(x).lower() for keyword in ['kale', 'pear'])
)]

print(f"\n[查詢結果 3] 同時包含 'kale' 和 'pear' 的食譜總數：{len(kale_recipes_df)} 份")
print(kale_recipes_df[['Title', 'Total_Time_Raw', 'Original_URL']])

# 範例查詢 4: 尋找標題包含 'Smoothie' 且總時間不超過 10 分鐘 (PT10M) 的食譜
quick_smoothie_recipes = df[
    (df['Title'].str.contains('Smoothie', case=False, na=False)) & # 標題包含 Smoothie (不區分大小寫)
    (df['Total_Time_Raw'].isin(['PT5M', 'PT10M'])) # 時間是 5 分鐘或 10 分鐘
]

print(f"\n[查詢結果 4] 快速 (<= 10 分鐘) Smoothie 食譜總數：{len(quick_smoothie_recipes)} 份")
print(quick_smoothie_recipes[['Title', 'Total_Time_Raw', 'Original_URL']].head())
# -------------------------------------------------------------
# 範例查詢 4: 尋找標題包含 'Smoothie' 且總時間不超過 10 分鐘 (PT10M) 的食譜
quick_smoothie_recipes = df[
    (df['Title'].str.contains('Smoothie', case=False, na=False)) & # 標題包含 Smoothie (不區分大小寫)
    (df['Total_Time_Raw'].isin(['PT5M', 'PT10M'])) # 時間是 5 分鐘或 10 分鐘
]

print(f"\n[查詢結果 4] 快速 (<= 10 分鐘) Smoothie 食譜總數：{len(quick_smoothie_recipes)} 份")
print(quick_smoothie_recipes[['Title', 'Total_Time_Raw', 'Original_URL']].head())

# -------------------------------------------------------------
# 新的查詢範例：尋找所有包含「chickpea」的食譜
chickpea_recipes_df = df[df['Ingredients'].apply(
    lambda x: any('chickpea' in item.lower() for item in x)
)]

print(f"\n[新查詢結果] 包含 'chickpea' 的食譜總數：{len(chickpea_recipes_df)} 份")
print("前 10 筆包含 chickpea 的食譜：")
print(chickpea_recipes_df[['Title', 'Total_Time_Clean', 'Original_URL']].head(10))