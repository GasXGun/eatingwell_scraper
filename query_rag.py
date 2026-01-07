import chromadb
from chromadb.utils import embedding_functions
from deep_translator import GoogleTranslator
import json
import re
import time

# 1. 初始化資料庫與翻譯器
client = chromadb.PersistentClient(path="recipe_vector_db")
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_collection(name="recipes", embedding_function=emb_fn)

to_en = GoogleTranslator(source='auto', target='en')
to_zh = GoogleTranslator(source='auto', target='zh-TW')

# 載入原始詳細資料 (獲取食材與作法)
with open('data/recipes_with_nutrition.json', 'r', encoding='utf-8') as f:
    full_recipes = json.load(f)

def safe_translate(text):
    if not text: return ""
    try:
        time.sleep(0.3) # 避免 API 頻率限制
        return to_zh.translate(text)
    except:
        return text

def query_rag():
    print("\n" + "="*50)
    print("食譜-營養素智慧 RAG 搜尋系統 (完整資料版)")
    print("="*50)

    while True:
        user_input = input("\n請輸入搜尋內容 (或輸入 q 離開): ").strip()
        if user_input.lower() == 'q': break
        
        # 提取時間約束
        time_limit = None
        time_match = re.search(r'(\d+)\s*分鐘', user_input)
        if time_match:
            time_limit = int(time_match.group(1))
            search_text = user_input.replace(time_match.group(0), "").strip()
        else:
            search_text = user_input

        try:
            # 語義翻譯
            query_en = to_en.translate(search_text if search_text else "banana breakfast")
            print(f"🔍 系統理解意圖: {query_en}" + (f" | 限制: {time_limit} 分鐘內" if time_limit else ""))

            # Metadata 過濾
            where_filter = {"total_time": {"$lte": time_limit}} if time_limit else None

            results = collection.query(
                query_texts=[query_en],
                n_results=3,
                where=where_filter
            )

            if not results['ids'][0]:
                print("❌ 找不到符合條件的食譜。")
                continue

            for i in range(len(results['ids'][0])):
                recipe_url = results['ids'][0][i]
                recipe_data = full_recipes.get(recipe_url)
                
                if not recipe_data: continue

                print("\n" + "*" * 60)
                # 翻譯標題與描述
                zh_title = safe_translate(recipe_data['Title'])
                zh_desc = safe_translate(recipe_data.get('Description', '無描述'))
                
                print(f"標題: {zh_title}")
                print(f"描述: {zh_desc}")
                print(f"烹飪時間: {recipe_data.get('Total_Time_Raw', 'N/A').replace('PT', '').replace('M', ' 分鐘')}")
                
                # 營養成分 (一人份)
                nut = recipe_data.get('Nutrition_Analysis', {})
                print(f"\n[營養成分 - 預估一人份]")
                print(f"熱量: {nut.get('Energy',0):.1f} kcal | 蛋白質: {nut.get('Protein',0):.1f}g | 脂肪: {nut.get('Fat',0):.1f}g | 碳水: {nut.get('Carbohydrate',0):.1f}g")

                # 食材翻譯
                print(f"\n[所需食材 - 預估一人份]")
                ing_text = "\n".join(recipe_data.get('Ingredients', []))
                print(safe_translate(ing_text))

                # 作法翻譯
                print(f"\n[烹飪步驟]")
                inst_text = "\n".join(recipe_data.get('Instructions', []))
                print(safe_translate(inst_text))

                print(f"\n原文連結: {recipe_url}")
                print("*" * 60)

        except Exception as e:
            print(f"發生錯誤: {e}")

if __name__ == "__main__":
    query_rag()