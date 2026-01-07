import json
import os
import chromadb
from chromadb.utils import embedding_functions
from tqdm import tqdm
import re

# 1. 初始化 ChromaDB 本地資料夾
db_path = "recipe_vector_db"
client = chromadb.PersistentClient(path=db_path)
# 使用 all-MiniLM-L6-v2，這是一個在個人電腦跑起來極快且精準的模型
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection(name="recipes", embedding_function=emb_fn)

def build_index():
    json_path = 'data/recipes_with_nutrition.json'
    if not os.path.exists(json_path):
        print(f"錯誤：找不到 {json_path}，請先確認 main_converter.py 已跑過")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        recipes = json.load(f)
    
    print(f"正在建立 RAG 向量索引...")
    
    ids, documents, metadatas = [], [], []
    for url, data in tqdm(recipes.items()):
        # 語義整合：標題 + 描述 + 食材
        combined_text = f"Title: {data['Title']}\nDescription: {data['Description']}\nIngredients: {', '.join(data['Ingredients'])}"
        
        # 提取時間數字 (PT15M -> 15)
        raw_time = data.get('Total_Time_Raw', 'PT0M')
        time_val = 0
        if raw_time:
            digits = re.findall(r'\d+', str(raw_time))
            time_val = int(digits[0]) if digits else 0

        ids.append(url)
        documents.append(combined_text)
        metadatas.append({
            "title": data['Title'],
            "calories": float(data.get('Nutrition_Analysis', {}).get('Energy', 0)),
            "total_time": time_val
        })

    # 存入資料庫
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    print("\n✅ RAG 向量索引建立完成！")

if __name__ == "__main__":
    build_index()