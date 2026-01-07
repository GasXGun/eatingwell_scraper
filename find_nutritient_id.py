import pandas as pd

# 載入 Nutrient.csv
path = './foodb_2020_04_07_csv/Nutrient.csv'
nutrients = pd.read_csv(path)

# 定義我們想找的關鍵字
search_list = [
    'Fiber', 'Water', 'Moisture', 'Sugar',      # 纖維、水分、糖
    'Vitamin A', 'Vitamin C', 'Vitamin D', 'Vitamin E', 'Vitamin B-12', 'Vitamin B-6', # 維生素
    'Sodium', 'Calcium', 'Iron', 'Potassium', 'Magnesium', 'Zinc' # 礦物質
]

# 執行搜尋
pattern = '|'.join(search_list)
found = nutrients[nutrients['name'].str.contains(pattern, case=False, na=False)]

print("==== 找到的營養素 ID 清單 ====")
print(found[['id', 'name']].to_string(index=False))