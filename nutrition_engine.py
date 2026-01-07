import re

def parse_ingredient_text(text):
    """
    將 "1 1/2 cups chopped kale" 解析為 ("1.5", "cup", "chopped kale")
    """
    # 處理常見分數符號
    text = text.replace('½', '0.5').replace('¼', '0.25').replace('¾', '0.75').replace('1½', '1.5')
    
    # 匹配數字(含分數) + 單位 + 食材名
    pattern = r"([0-9\/\.\s]+)?\s*(cup|tablespoon|tbsp|teaspoon|tsp|ounce|oz|pound|lb|clove|slice|medium|small|large|pinch)s?\b\s*(.*)"
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        qty = match.group(1).strip() if match.group(1) else "1"
        unit = match.group(2).strip().lower() if match.group(2) else "unit"
        name = match.group(3).strip()
        name = re.sub(r"^(of\s|s\s)", "", name).strip()
        return qty, unit, name
    return "1", "unit", text

def get_weight(qty_str, unit, item_name):
    """
    依據單位與數量換算為公克 (g)
    """
    # 簡單的分數轉換 (1 1/2 -> 1.5)
    try:
        if ' ' in qty_str:
            parts = qty_str.split()
            qty = float(parts[0]) + (eval(parts[1]) if '/' in parts[1] else float(parts[1]))
        elif '/' in qty_str:
            qty = eval(qty_str)
        else:
            qty = float(qty_str)
    except:
        qty = 1.0

    # 基礎密度換算表 (單位 -> g)
    unit_map = {
        "cup": 240,
        "tablespoon": 15,
        "tbsp": 15,
        "teaspoon": 5,
        "tsp": 5,
        "ounce": 28.35,
        "oz": 28.35,
        "pound": 453.6,
        "lb": 453.6,
        "clove": 5,
        "slice": 30,
        "unit": 100 # 預設一個單位 100g，之後會在 main_converter 根據食材修正
    }
    
    return qty * unit_map.get(unit, 1.0)