import pandas as pd

base_path = './foodb_2020_04_07_csv'

def shrink():
    print("正在讀取大型 Content.csv (這可能需要 1-2 分鐘)...")
    # 只讀取我們需要的欄位
    use_cols = ['food_id', 'source_id', 'source_type', 'standard_content']
    
    # 分塊讀取（Chunking）以節省記憶體
    chunks = pd.read_csv(f'{base_path}/Content.csv', usecols=use_cols, chunksize=100000)
    
    # 我們感興趣的營養素 ID (根據 FooDB 的 Nutrient.csv)
    # 1: Energy (kcal), 2: Protein, 5: Fat, 13: Carbohydrate (請根據你的 check_foodb.py 結果確認)
    target_nutrients = [1, 2, 3, 38]
    
    filtered_chunks = []
    for chunk in chunks:
        # 只保留 Nutrient 類型且是我們要的營養素
        filtered = chunk[(chunk['source_type'] == 'Nutrient') & (chunk['source_id'].isin(target_nutrients))]
        filtered_chunks.append(filtered)
        
    df_small = pd.concat(filtered_chunks)
    df_small.to_csv('simplified_content.csv', index=False)
    print("完成！瘦身版數據已儲存為 simplified_content.csv")

if __name__ == "__main__":
    shrink()