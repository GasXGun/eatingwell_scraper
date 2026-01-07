import json
import pandas as pd
import re
import os
from thefuzz import process
import nutrition_engine

# --- 根據你的查詢結果設定 ID ---
TARGET_MAP = {
    38: 'Energy',
    2: 'Protein',
    1: 'Fat',
    3: 'Carbohydrate'
}

print("正在初始化數據庫 (讀取與清理)...")
FOOD_CSV = './foodb_2020_04_07_csv/Food.csv'
foods_df = pd.read_csv(FOOD_CSV)

# 重要修正：讀取時直接預處理，同食物同營養素只取平均值，避免數值爆炸
raw_content = pd.read_csv('simplified_content.csv')
content_df = raw_content.groupby(['food_id', 'source_id'])['standard_content'].mean().reset_index()

def parse_ingredient_text(text):
    # 處理特殊分數符號
    text = text.replace('1½', '1.5').replace('½', '0.5').replace('¼', '0.25').replace('¾', '0.75')
    pattern = r"([0-9\/\.\s]+)?\s*(cup|tablespoon|tbsp|teaspoon|tsp|ounce|oz|pound|lb|clove|slice|medium|small|large|pinch)s?\b\s*(.*)"
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        qty = match.group(1).strip() if match.group(1) else "1"
        unit = match.group(2).strip() if match.group(2) else "unit"
        name = match.group(3).strip()
        name = re.sub(r"^(of\s|s\s)", "", name).strip()
        return qty, unit, name
    return "1", "unit", text

def get_best_food_id(name):
    # 清理名稱提高比對度
    clean_name = re.sub(r'(chopped|sliced|grated|trimmed|thinly|pure|divided|chilled|frozen|medium|small|large|extra-virgin)', '', name, flags=re.I).strip()
    
    # 針對常出錯的食材進行「手動校正」
    manual_fixes = {
        "kale": "Kale",
        "date": "Date",
        "brussels sprout": "Brussel sprouts",
        "pear": "Pear"
    }
    for key, val in manual_fixes.items():
        if key in clean_name.lower():
            f_id = foods_df[foods_df['name'] == val]['id'].values[0]
            return f_id, val

    match = process.extractOne(clean_name, foods_df['name'])
    f_id = foods_df[foods_df['name'] == match[0]]['id'].values[0]
    return f_id, match[0]

def analyze_recipes():
    recipe_path = 'data/eatingwell_quick_easy_recipes_full.json'
    with open(recipe_path, 'r', encoding='utf-8') as f:
        recipes_data = json.load(f)
    
    final_results = {}
    
    # 已移除 [:2] 限制，將會跑完所有食譜
    for url, data in recipes_data.items():
        print(f"正在分析: {data['Title']}")
        total_nut = {'Energy': 0.0, 'Protein': 0.0, 'Fat': 0.0, 'Carbohydrate': 0.0}
        
        for ing_text in data['Ingredients']:
            qty_str, unit, item_name = parse_ingredient_text(ing_text)
            weight = nutrition_engine.get_weight(qty_str, unit, item_name)
            f_id, f_name = get_best_food_id(item_name)
            
            # 獲取平均營養價值
            food_nutrients = content_df[content_df['food_id'] == f_id]
            for _, row in food_nutrients.iterrows():
                n_id = int(row['source_id'])
                if n_id in TARGET_MAP:
                    n_name = TARGET_MAP[n_id]
                    val = row['standard_content']
                    
                    # 單位校正邏輯
                    if n_name == 'Energy':
                        if val > 800: val = val / 4.184 # kJ 轉 kcal
                    else:
                        if val > 100: val = val / 1000 # mg 轉 g
                    
                    total_nut[n_name] += (val * weight) / 100
        
        # 存儲結果
        data['Nutrition_Analysis'] = total_nut
        final_results[url] = data

    # 儲存回新的 JSON 檔案
    output_path = 'data/recipes_with_nutrition.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=4, ensure_ascii=False)
    
    print(f"\n恭喜！所有食譜分析完畢，結果已存至 {output_path}")

if __name__ == "__main__":
    analyze_recipes()