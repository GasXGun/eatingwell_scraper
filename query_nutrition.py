import json
import os
import time
from deep_translator import GoogleTranslator
from thefuzz import process

# 設定路徑
FILE_PATH = 'data/recipes_with_nutrition.json'

def load_recipes():
    """載入分析後的食譜數據"""
    if not os.path.exists(FILE_PATH):
        print(f"錯誤：找不到檔案 {FILE_PATH}，請先執行 main_converter.py")
        return None
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def safe_translate(translator, text):
    """安全翻譯：若失敗則回傳原文，避免程式中斷"""
    if not text or text == "無描述":
        return text
    try:
        # 增加微小延遲，防止請求過快被 Google 暫時封鎖
        time.sleep(0.3)
        result = translator.translate(text)
        return result if result else text
    except Exception:
        # 如果翻譯發生錯誤（如網路問題），直接回傳英文原文
        return text

def smart_query():
    recipes_data = load_recipes()
    if not recipes_data:
        return

    # 初始化翻譯器：中翻英、英翻繁中
    to_en = GoogleTranslator(source='auto', target='en')
    to_zh = GoogleTranslator(source='auto', target='zh-TW')
    
    print("\n" + "="*50)
    print("食譜-營養素搜尋系統")
    print("系統說明：輸入中文關鍵字，將自動檢索並翻譯食譜細節")
    print("="*50)

    while True:
        user_input = input("\n請輸入搜尋關鍵字 (或輸入 q 離開): ").strip()
        if user_input.lower() == 'q':
            break
        if not user_input:
            continue

        try:
            # 1. 翻譯搜尋詞並優化關鍵字
            query_en = to_en.translate(user_input)
            synonyms = {"milkshake": "smoothie", "10分鐘": "10-minute", "雞肉": "chicken", "肌肉": "protein"}
            search_key = synonyms.get(user_input, query_en)
            print(f"系統搜尋中... ({search_key})")

            # 2. 獲取所有標題並進行模糊比對
            titles = [data['Title'] for data in recipes_data.values()]
            # limit=5 代表回傳前 5 名最相關的結果
            matches = process.extract(search_key, titles, limit=2)

            found_count = 0
            for match in matches:
                # 處理 thefuzz 不同版本的回傳格式 (2個或3個值)
                title = match[0]
                score = match[1]
                
                # 相關度超過 40 分才顯示
                if score >= 40:
                    found_count += 1
                    # 找回對應的完整食譜資料
                    recipe = next(v for v in recipes_data.values() if v['Title'] == title)
                    
                    print("\n" + "-" * 50)
                    
                    # 3. 執行內容翻譯 (安全模式)
                    zh_title = safe_translate(to_zh, title.replace('&amp;', '&'))
                    zh_desc = safe_translate(to_zh, recipe.get('Description', '無描述'))
                    
                    print(f"標題: {zh_title} (相關度: {score}%)")
                    print(f"描述: {zh_desc}")
                    print(f"原文連結: {recipe['URL']}")
                    
                    # 4. 輸出營養素 (標註預估一人份)
                    nut = recipe.get('Nutrition_Analysis', {})
                    print(f"\n營養成分 (預估為一人份):")
                    print(f"熱量: {nut.get('Energy',0):.1f} kcal | 蛋白質: {nut.get('Protein',0):.1f}g | 脂肪: {nut.get('Fat',0):.1f}g | 碳水: {nut.get('Carbohydrate',0):.1f}g")

                    # 5. 輸出食材 (標註預估一人份)
                    print("\n所需食材 (預估為一人份):")
                    ing_raw = "\n".join(recipe.get('Ingredients', []))
                    zh_ing = safe_translate(to_zh, ing_raw)
                    print(zh_ing)

                    # 6. 輸出烹飪步驟
                    print("\n烹飪步驟:")
                    inst_raw = "\n".join(recipe.get('Instructions', []))
                    zh_inst = safe_translate(to_zh, inst_raw)
                    print(zh_inst)
                    
                    print("-" * 50)
            
            if found_count == 0:
                print("找不到相關食譜，建議縮短關鍵字再試一次。")
            else:
                print(f"\n搜尋完畢，共顯示 {found_count} 個最相關結果。")

        except Exception as e:
            print(f"執行搜尋時發生錯誤: {e}")

if __name__ == "__main__":
    smart_query()