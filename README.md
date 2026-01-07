# EatingWell Recipe Nutrition Analyzer

這個專案能自動抓取 EatingWell 食譜，並結合 **FooDB 資料庫** 進行食材解析與營養成分轉換（熱量、蛋白質、脂肪、碳水、纖維等）。

##  檔案功能說明

| 檔案名稱 | 功能描述 |
| :--- | :--- |
| **`scraper.py`** | **爬蟲核心**。負責抓取食譜標題、食材、步驟及時間，輸出原始 JSON。 |
| **`query.py`** | **查詢工具**。用於在終端機快速篩選已下載的食譜（如：找 10 分鐘內的奶昔）。 |
| **`shrink_data.py`** | **數據瘦身器**。將 700MB+ 的 FooDB `Content.csv` 提取出關鍵營養素，生成輕量化的 `simplified_content.csv`。 |
| **`nutrition_engine.py`** | **計算引擎**。處理食譜單位（cup, tbsp, oz）到公克 (g) 的轉換邏輯。 |
| **`main_converter.py`** | **核心轉換程式**。串接所有組件，執行模糊比對 (Fuzzy Match) 並產出最終營養報表。 |

##  執行流程

1. **環境準備**：執行 `pip install pandas thefuzz python-Levenshtein requests beautifulsoup4`。
2. **獲取食譜**：執行 `python scraper.py` 產出食譜 JSON。
3. **處理數據庫**：確保 FooDB CSV 檔案在路徑下，執行 `python shrink_data.py`。
4. **生成營養報告**：執行 `python main_converter.py`。

##  數據處理邏輯 (Workflow)
1. **食材解析**：利用 Regex 抽離數量、單位與名稱。
2. **重量換算**：將英制單位依密度換算為公制單位 (g)。
3. **食材比對**：使用 Levenshtein 距離演算法將食譜食材與 FooDB 食物名稱進行模糊匹配。
4. **單位修正**：自動偵測並修正 FooDB 中不統一的單位（如 kJ 轉 kcal, mg 轉 g）。