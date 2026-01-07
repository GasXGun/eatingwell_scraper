import json
import pandas as pd
import re
import os
from thefuzz import process
import nutrition_engine

# --- 1. 精準校準表 (針對 FooDB 中數據最亂的基礎食材) ---
# 這些 ID 是經過篩選後，營養成分最接近「新鮮、天然」狀態的 ID
CALIBRATED_FOODS = {
    "egg": {"id": 122, "name": "Egg (whole, fresh, raw)"},
    "banana": {"id": 154, "name": "Banana (raw)"},
    "chicken": {"id": 507, "name": "Chicken (breast, raw)"},
    "olive oil": {"id": 659, "name": "Olive oil"},
    "honey": {"id": 328, "name": "Honey"},
    "yogurt": {"id": 103, "name": "Yogurt (plain)"}
}

TARGET_MAP = {38: 'Energy', 2: 'Protein', 1: 'Fat', 3: 'Carbohydrate'}

print("正在讀取數據庫 (這可能需要 30 秒)...")
foods_df = pd.read_csv('./foodb_2020_04_07_csv/Food.csv')
raw_content = pd.read_csv('simplified_content.csv')
content_df = raw_content.groupby(['food_id', 'source_id'])['standard_content'].mean().reset_index()

def get_accurate_food(name):
    name_lower = name.lower()
    # 優先檢查校準表
    for key, info in CALIBRATED_FOODS.items():
        if key in name_lower:
            return info['id'], info['name']
    
    # 否則執行模糊比對
    clean_name = re.sub(r'(chopped|sliced|grated|trimmed|thinly|pure|divided|chilled|frozen|medium|small|large)', '', name, flags=re.I).strip()
    match = process.extractOne(clean_name, foods_df['name'])
    f_id = foods_df[foods_df['name'] == match[0]]['id'].values[0]
    return f_id, match[0]

def analyze_recipes():
    recipe_path = 'data/eatingwell_quick_easy_recipes_full.json'
    with open(recipe_path, 'r', encoding='utf-8') as f:
        recipes_data = json.load(f)
    
    final_results = {}
    for url, data in recipes_data.items():
        print(f"正在分析: {data['Title']}")
        total_nut = {'Energy': 0.0, 'Protein': 0.0, 'Fat': 0.0, 'Carbohydrate': 0.0}
        
        for ing_text in data['Ingredients']:
            qty_str, unit, item_name = nutrition_engine.parse_ingredient_text(ing_text)
            weight = nutrition_engine.get_weight(qty_str, unit, item_name)
            
            # 修正一人份邏輯：如果 2 顆蛋算出來是 2 公斤，強制修正
            if "egg" in item_name.lower() and weight > 300: weight = 50 * float(eval(qty_str) if '/' in qty_str else qty_str)
            if "banana" in item_name.lower() and weight > 400: weight = 120 * float(qty_str)

            f_id, f_name = get_accurate_food(item_name)
            food_nutrients = content_df[content_df['food_id'] == f_id]
            
            for _, row in food_nutrients.iterrows():
                n_id = int(row['source_id'])
                if n_id in TARGET_MAP:
                    n_name = TARGET_MAP[n_id]
                    val = row['standard_content']
                    
                    # 單位校正 (防止 mg 被當成 g)
                    if n_name == 'Energy':
                        if val > 900: val /= 4.184
                    else:
                        if val > 100: val /= 1000
                    
                    total_nut[n_name] += (val * weight) / 100
        
        data['Nutrition_Analysis'] = total_nut
        final_results[url] = data

    with open('data/recipes_with_nutrition.json', 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=4, ensure_ascii=False)
    print("\n[完成] 數據精準化處理完畢！")

if __name__ == "__main__":
    analyze_recipes()