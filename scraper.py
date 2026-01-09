import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re
from tqdm import tqdm

# 設定 HTTP 請求標頭
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
BASE_URL = 'https://www.eatingwell.com'
RECIPES_BASE_PATH = '/recipes/18258/cooking-methods-styles/quick-easy/'

def get_all_recipe_links(max_pages=10):
    """獲取初始分類清單"""
    all_links = set()
    print(f"🔍 正在掃描前 {max_pages} 頁分類清單...")
    for page_num in range(1, max_pages + 1):
        list_url = f"{BASE_URL}{RECIPES_BASE_PATH}?page={page_num}"
        try:
            response = requests.get(list_url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            # 支援 EatingWell 多種不同的卡片 CSS 類名
            recipe_card_links = soup.select('a.mntl-card-list-items, a.mntl-document-card, a.card') 
            for link_tag in recipe_card_links:
                href = link_tag.get('href', '').split('?')[0]
                if href:
                    all_links.add(href if href.startswith('http') else BASE_URL + href)
        except Exception: break
    return list(all_links)

def scrape_page_content(page_url):
    """深度解析頁面內容：包含 JSON-LD 備援、完整標籤掃描、份數校正"""
    try:
        response = requests.get(page_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- 1. 從 JSON-LD 獲取基礎數據 ---
        recipe_data = {}
        schema_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        for script in schema_scripts:
            try:
                data = json.loads(script.text)
                data_list = data if isinstance(data, list) else [data]
                for item in data_list:
                    obj_type = str(item.get("@type", ""))
                    if "Recipe" in obj_type:
                        recipe_data = {
                            "Title": item.get("name", "N/A"),
                            "Description": item.get("description", "N/A"),
                            "Ingredients": item.get("recipeIngredient", []),
                            "Instructions": [s.get("text", s) if isinstance(s, dict) else s for s in item.get("recipeInstructions", [])],
                            "Total_Time_Raw": item.get("totalTime", "N/A"),
                            "Servings": str(item.get("recipeYield", [""])[0]) if isinstance(item.get("recipeYield"), list) else str(item.get("recipeYield", ""))
                        }
                        # 先拿 JSON-LD 裡的營養素做底
                        if "nutrition" in item:
                            recipe_data["Official_Nutrition"] = {k: v for k, v in item["nutrition"].items() if v and k != "@type"}
                        break
            except: continue

        # 處理清單型文章（遞歸）
        nested = [a['href'] for a in soup.select('.mntl-sc-block-universal-featured-link--button a, .mntl-card-list-items')]
        if not recipe_data and nested: return "IS_LIST", nested
        if not recipe_data: return None, []

        # --- 2. 份數 (Servings) 補強 (處理 Cacio e Pepe 這種情況) ---
        if not recipe_data.get("Servings"):
            serv_node = soup.find('div', class_=re.compile(r'details__servings|recipe-details__servings'))
            if serv_node:
                val = serv_node.find('div', class_=re.compile(r'details__value|recipe-details__value'))
                if val: recipe_data["Servings"] = val.get_text(strip=True)

        # --- 3. 完整營養標籤 (Full Nutrition Label) 深度掃描 ---
        if "Official_Nutrition" not in recipe_data: recipe_data["Official_Nutrition"] = {}
        
        # 掃描 Full Label 表格
        full_table = soup.find('table', class_=re.compile(r'nutrition-facts-label__table'))
        if full_table:
            for row in full_table.find_all('tr'):
                # 抓 Calories
                if 'calories' in str(row.get('class', '')).lower():
                    spans = row.find_all('span')
                    if spans: recipe_data["Official_Nutrition"]["Calories"] = spans[-1].get_text(strip=True)
                
                # 抓詳細 TD (Sodium, Fiber, Vitamins...)
                tds = row.find_all('td')
                if tds:
                    raw_text = tds[0].get_text(" ", strip=True)
                    # 分離 "Sodium 764mg" -> "Sodium", "764mg"
                    match = re.match(r"^(.*?)\s*(\d+\.?\d*[a-zA-Zµg%]*)$", raw_text)
                    if match:
                        name, val = match.groups()
                        recipe_data["Official_Nutrition"][name.strip()] = val.strip()

        # 份數二次校正：如果還沒抓到，從標籤裡抓
        if not recipe_data.get("Servings"):
            label_servings = soup.find(class_=re.compile(r'nutrition-facts-label__servings'))
            if label_servings:
                recipe_data["Servings"] = label_servings.get_text(" ", strip=True).replace("Servings Per Recipe", "").strip()

        recipe_data["URL"] = page_url
        return recipe_data, []

    except Exception:
        return None, []

def main():
    output_file = 'data/eatingwell_quick_easy_recipes_full.json'
    if not os.path.exists('data'): os.makedirs('data')

    # 1. 斷點續傳：載入已抓取的資料
    all_recipes_dict = {}
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            all_recipes_dict = json.load(f)
        print(f"📂 載入現有資料庫：{len(all_recipes_dict)} 份食譜")

    # 2. 獲取連結並排除已爬取的
    initial_links = get_all_recipe_links(max_pages=5)
    queue = [l for l in initial_links if l not in all_recipes_dict]
    visited_urls = set(all_recipes_dict.keys()) | set(initial_links)

    print(f"🚀 開始爬取，剩餘目標：{len(queue)} 道 (將隨深度爬取增加)")
    pbar = tqdm(total=len(queue) + len(all_recipes_dict), initial=len(all_recipes_dict), desc="總進度", unit="道")

    try:
        while queue:
            url = queue.pop(0)
            recipe, nested = scrape_page_content(url)
            
            if recipe == "IS_LIST":
                for l in nested:
                    f_l = l if l.startswith('http') else BASE_URL + l
                    if f_l not in visited_urls:
                        visited_urls.add(f_l); queue.append(f_l)
                        pbar.total += 1 
            elif recipe:
                all_recipes_dict[url] = recipe
                # 每 20 份存檔一次
                if len(all_recipes_dict) % 20 == 0:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(all_recipes_dict, f, ensure_ascii=False, indent=4)
            
            pbar.update(1)
            time.sleep(0.8)

    except KeyboardInterrupt:
        print("\n🛑 手動停止，正在存檔...")
    finally:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_recipes_dict, f, ensure_ascii=False, indent=4)
        pbar.close()
        print(f"\n✨ 任務完成！資料庫總計：{len(all_recipes_dict)} 份食譜。")

if __name__ == '__main__':
    main()