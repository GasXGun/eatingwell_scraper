import re

def get_weight(quantity_str, unit, food_name):
    """
    將食譜中的數量與單位轉換為『克 (g)』
    """
    # 1. 處理分數 (例如 1 1/2 -> 1.5)
    try:
        if '/' in quantity_str:
            parts = quantity_str.split()
            res = 0.0
            for p in parts:
                if '/' in p:
                    num, den = p.split('/')
                    res += float(num) / float(den)
                else:
                    res += float(p)
            qty = res
        else:
            qty = float(quantity_str)
    except:
        qty = 1.0 # 預設為 1

    # 2. 單位換算表 (以克為基準)
    unit_map = {
        'cup': 240,
        'tablespoon': 15, 'tbsp': 15,
        'teaspoon': 5, 'tsp': 5,
        'ounce': 28.35, 'oz': 28.35,
        'pound': 453.6, 'lb': 453.6,
        'clove': 5, # 蒜瓣預設
        'medium': 150, # 假設一個中型蔬果 150g
        'small': 100,
        'large': 250
    }
    
    unit = str(unit).lower().strip('s') if unit else 'unit'
    
    # 3. 簡單密度調整 (未來可擴充)
    multiplier = 1.0
    if 'oil' in food_name.lower():
        multiplier = 0.92 # 油比水輕
    
    base_weight = unit_map.get(unit, 1.0)
    return qty * base_weight * multiplier

# 測試
# print(get_weight("1 1/2", "tablespoons", "olive oil"))