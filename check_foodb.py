import pandas as pd
import os

# 設定資料夾路徑
base_path = './foodb_2020_04_07_csv'

def check_foodb_files(folder):
    files = {
        "Food": "Food.csv",
        "Nutrient": "Nutrient.csv",
        "Content": "Content.csv"
    }
    
    for key, filename in files.items():
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            print(f"\n{'='*20} 檢查 {key} ({filename}) {'='*20}")
            # nrows=5 確保不會讀取太慢
            df = pd.read_csv(path, nrows=5)
            print(f"欄位列表：\n{df.columns.tolist()}")
            print("\n前幾筆數據樣貌：")
            print(df.head(3))
        else:
            print(f"\n❌ 錯誤：找不到 {filename}")

if __name__ == "__main__":
    check_foodb_files(base_path)