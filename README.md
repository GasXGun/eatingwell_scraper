好的！為您準備了一份專業、結構清晰的 $\text{README.md}$ 檔案內容，您可以直接複製並貼到 $\text{GitHub}$ 專案中使用。

這份文件涵蓋了環境建置、操作指南，以及目前爬蟲專案的成果和核心功能。

-----

## 📄 README.md 內容

```markdown
# 🍜 EatingWell Quick & Easy 食譜爬蟲專案 (Recipe Scraper)

## 🌟 專案簡介

此專案是使用 Python 實作的網頁爬蟲程式，專門用於抓取 [EatingWell 網站](https://www.eatingwell.com) 中 **"Quick & Easy Healthy Recipes"** 分類下的所有食譜資料。

它採用**遞歸爬取 (Recursive Scraping)** 策略，確保能從文章列表頁面 (例如「20 Anti-Inflammatory Meals...」) 中，深度提取所有內嵌的單一食譜連結，最終建構出一個結構化的 JSON 資料庫 ($\text{Dictionary}$)。

## 💻 環境建置 (Setup)

本專案使用 Python 虛擬環境 (`venv`) 隔離依賴，建議使用 $\text{Visual Studio Code (VS Code)}$ 進行開發與執行。

### 1. 建立專案結構

請先建立以下資料夾與檔案結構：

```

eatingwell\_scraper/
├── .venv/              \# 虛擬環境資料夾 (執行指令後自動生成)
├── data/               \# 數據輸出資料夾 (爬蟲結果存放處)
├── scraper.py          \# 爬蟲核心程式碼
└── requirements.txt    \# 依賴函式庫清單

````

### 2. 安裝依賴項目

在 VS Code 內開啟終端機 (Terminal)，並執行以下步驟：

#### A. 建立並啟用虛擬環境

```bash
# 建立虛擬環境
python -m venv .venv
# 啟用虛擬環境 (Windows)
.venv\Scripts\activate
# 啟用虛擬環境 (macOS/Linux)
# source .venv/bin/activate
````

#### B. 撰寫 requirements.txt

請在 `requirements.txt` 檔案中加入以下內容：

```text
requests
beautifulsoup4
pandas
```

#### C. 安裝函式庫

在**虛擬環境已啟用**的狀態下，執行以下指令：

```bash
pip install -r requirements.txt
```

-----

## 🚀 如何操作 (Usage)

所有核心邏輯都包含在 `scraper.py` 中。

### 1\. 執行爬蟲程式

在啟用的虛擬環境 (`(.venv)`) 中，直接運行 `scraper.py`：

```bash
python scraper.py
```

  * **執行時間：** 由於程式會遞歸追蹤連結，整個過程可能需要 **5 - 10 分鐘** (包含禮貌性延遲)。
  * **進度顯示：** 程式運行時會顯示進度 (`--- 處理進度 X/Y ---`)，並提示是否找到嵌套連結。

### 2\. 爬蟲輸出結果

執行成功後，所有食譜數據將儲存到 `data/` 資料夾中：

  * **檔案名稱：** `eatingwell_quick_easy_recipes_full.json`
  * **數據量：** 預期收集到約 **460 份**食譜。

### 3\. 如何分析數據 (使用 Pandas)

建議您將數據載入到 Pandas DataFrame 進行查詢，這比直接操作 JSON 字典更高效。

```python
# 載入 Pandas 進行數據分析
import pandas as pd
import json

file_path = 'data/eatingwell_quick_easy_recipes_full.json'

with open(file_path, 'r', encoding='utf-8') as f:
    recipe_dict = json.load(f)

df = pd.DataFrame(recipe_dict).T.reset_index(names='Original_URL')

# 範例：尋找所有包含「salmon」的食譜
salmon_recipes = df[df['Ingredients'].apply(
    lambda x: any('salmon' in item.lower() for item in x)
)]

print(f"找到 {len(salmon_recipes)} 份鮭魚食譜。")
print(salmon_recipes[['Title', 'Total_Time_Raw']].head())

# 範例：將結果匯出成 CSV
salmon_recipes.to_csv('data/salmon_recipes_filtered.csv', index=False, encoding='utf-8')
```

-----

## 🎯 爬蟲功能與數據成果 (Features & Data)

### 1\. 爬蟲核心功能

  * **目標鎖定：** 精準抓取 EatingWell 的 `/quick-easy/` 分類下的內容。
  * **遞歸抓取 (BFS)：** 程式能識別並追蹤文章列表頁面 (e.g., 包含 20 份食譜的合集文章)，確保不遺漏任何隱藏在第二層的單一食譜。
  * **智能數據提取：** 優先使用 **JSON-LD 結構化數據** (Schema.org) 提取食譜詳情，確保數據準確度與穩定性。
  * **智能過濾機制：** 自動排除所有非單一食譜的網頁 (如：文章列表、廣告頁面)，只儲存具備完整食材和步驟的食譜。

### 2\. Dictionary 資料庫結構 (JSON Output)

最終的 JSON 檔案是以食譜 URL 為鍵的字典。每個 Value 包含以下欄位：

| 欄位名稱 | 數據類型 | 說明 |
| :--- | :--- | :--- |
| **URL** | String | 該食譜的完整網址 (作為唯一識別碼) |
| **Title** | String | 食譜名稱 |
| **Description** | String | 食譜簡介 |
| **Ingredients** | List [String] | 食材列表 (每一項為一個字串) |
| **Instructions** | List [String] | 烹飪步驟 (每一步驟為一個字串) |
| **Total\_Time\_Raw** | String | 總烹飪時間 (ISO 8601 格式，如 $\text{PT20M}$) |

### 3\. 目前成果總結

本次爬取已成功收集 **460 份** 來自 EatingWell Quick & Easy 分類的單一食譜數據。

```
```