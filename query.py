import requests
from bs4 import BeautifulSoup
import json
import time
import os

# 設定 HTTP 請求標頭 (模擬瀏覽器)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
# 基礎 URL
BASE_URL = 'https://www.eatingwell.com'
# Quick & Easy 頁面的固定路徑
RECIPES_BASE_PATH = '/recipes/18258/cooking-methods-styles/quick-easy/'

# --- 輔助函式: 取得食譜連結 ---

def get_all_recipe_links(max_pages=5):
    """從 Quick & Easy 分頁頁面爬取初始連結。"""
    all_links = set()
    
    # 設置最大分頁數，以便抓取更多 Quick & Easy 列表的連結
    for page_num in range(1, max_pages + 1):
        list_url = f"{BASE_URL}{RECIPES_BASE_PATH}?page={page_num}"
        # print(f"-> 正在爬取 Quick & Easy 分頁 (Page {page_num}): {list_url}")
        
        try:
            response = requests.get(list_url, headers=HEADERS, timeout=10)
            response.raise_for_status() 
            soup = BeautifulSoup(response.text, 'html.parser')
            
            recipe_card_links = soup.select('a.mntl-document-card') 
            
            if not recipe_card_links and page_num == 1:
                 # 這裡可能需要調整 max_pages 的值
                 pass
            elif not recipe_card_links:
                 break

            for link_tag in recipe_card_links:
                if 'href' in link_tag.attrs:
                    raw_url = link_tag['href'].split('?')[0] 

                    if not raw_url.startswith('http'):
                        full_url = BASE_URL + raw_url
                    else:
                        full_url = raw_url
                        
                    all_links.add(full_url)
            
            time.sleep(1) 

        except requests.exceptions.RequestException:
            break
            
    return list(all_links)

# --- 核心函式: 爬取單個頁面資料 (包含食譜提取和嵌套連結查找) ---

def scrape_page_content(page_url):
    """
    1. 嘗試提取單一食譜 (JSON-LD 優先)。
    2. 如果失敗，則嘗試提取頁面中所有嵌套的 'View Recipe' 連結。
    
    :return: (dict or None, list) -> (食譜數據, 嵌套連結列表)
    """
    
    try:
        response = requests.get(page_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- 1. 嘗試從 JSON-LD 提取單一食譜 ---
        schema_script = soup.find('script', {'type': 'application/ld+json'})
        if schema_script:
            try:
                data = json.loads(schema_script.text)
                data_list = data if isinstance(data, list) else [data]
                
                for item in data_list:
                    item_type = item.get("@type", [])
                    if (isinstance(item_type, list) and 'Recipe' in item_type) or (item_type == "Recipe"):
                        
                        ingredients = item.get("recipeIngredient", [])
                        # 檢查：只有當成功提取到成分時，才認為這是有效的食譜數據
                        if ingredients and len(ingredients) > 0:
                            # 提取所有核心數據
                            title = item.get("name", "N/A")
                            description = item.get("description", "N/A")
                            instructions_raw = item.get("recipeInstructions", [])
                            total_time = item.get("totalTime", "N/A")
                            
                            instructions = []
                            if isinstance(instructions_raw, list):
                                for step in instructions_raw:
                                    if isinstance(step, dict) and step.get("text"):
                                        instructions.append(step["text"].strip())
                                    elif isinstance(step, str):
                                        instructions.append(step.strip())
                            
                            print(f"   ✅ JSON-LD 提取成功。Title: {title}")
                            return {
                                "URL": page_url,
                                "Title": title,
                                "Description": description,
                                "Ingredients": ingredients,
                                "Instructions": instructions,
                                "Total_Time_Raw": total_time 
                            }, [] # 成功提取食譜，不返回新的嵌套連結

            except json.JSONDecodeError:
                # print("   ❌ 錯誤: 無法解析 JSON-LD 腳本。")
                pass

        # --- 2. 如果不是單一食譜，嘗試提取所有嵌套的 'View Recipe' 連結 ---
        
        # 該選擇器針對 ListScTemplate 頁面中的 "View Recipe" 按鈕
        nested_links = soup.select('.mntl-sc-block-universal-featured-link--button a.mntl-sc-block-universal-featured-link__link')
        new_links = set()
        
        if nested_links:
            # 這是文章列表頁面，提取所有內嵌的食譜連結
            # 提取文章標題作為識別
            article_title_tag = soup.select_one('h1.article-heading') 
            article_title = article_title_tag.text.strip() if article_title_tag else "N/A Article"

            print(f"   🔎 發現文章列表頁面: {article_title}")
            for link_tag in nested_links:
                if 'href' in link_tag.attrs:
                    raw_url = link_tag['href'].split('?')[0]
                    
                    if not raw_url.startswith('http'):
                        full_url = BASE_URL + raw_url
                    else:
                        full_url = raw_url
                    
                    new_links.add(full_url)
            
            print(f"   🔗 提取到 {len(new_links)} 個嵌套食譜連結。")
            return None, list(new_links) # 返回空數據和新的連結列表

        # --- 3. 如果既不是食譜也不是文章列表 (結構不匹配或空頁面) ---
        
        # print("   ❌ 提取失敗: 非食譜/非文章列表。")
        return None, []

    except requests.exceptions.RequestException as e:
        # print(f"   ❌ 提取 {page_url} 時發生請求錯誤: {e}")
        return None, []
    except Exception as e:
        # print(f"   ❌ 提取 {page_url} 時發生嚴重錯誤: {e}")
        return None, []

# --- 主程式執行 ---

def main():
    # 設置初始爬取分頁數量 (為確保廣度，我們多抓幾頁的初始連結)
    MAX_INITIAL_PAGES = 5 
    
    if not os.path.exists('data'):
        os.makedirs('data')
        
    # 1. 取得所有初始連結 (包含單一食譜和文章列表)
    initial_links = get_all_recipe_links(max_pages=MAX_INITIAL_PAGES)
    
    # 2. 初始化待處理隊列和已處理集合
    # 使用 set 儲存 URL，避免重複爬取
    queue = initial_links
    visited_urls = set(initial_links)
    all_recipes_dict = {}
    
    total_processed = 0
    total_queued = len(queue)
    
    # 3. 廣度優先爬取循環
    while queue:
        url = queue.pop(0)
        total_processed += 1
        
        print(f"\n--- 處理進度 {total_processed}/{total_queued} (待處理: {len(queue)}) ---")
        
        # 進行網頁提取
        recipe, nested_links = scrape_page_content(url)
        
        if recipe:
            # 成功提取單一食譜，存儲
            all_recipes_dict[url] = recipe
        
        if nested_links:
            # 發現新的嵌套連結，將其加入隊列
            for link in nested_links:
                if link not in visited_urls:
                    visited_urls.add(link)
                    queue.append(link)
                    total_queued += 1 # 更新總計數
        
        # 禮貌延遲
        time.sleep(1 + (total_processed % 5) * 0.2) 

    # 4. 儲存結果到 JSON 檔案
    output_filename = 'data/eatingwell_quick_easy_recipes_full.json' 
    
    if all_recipes_dict:
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(all_recipes_dict, f, ensure_ascii=False, indent=4)
            print(f"\n🎉 爬蟲任務完成！共收集 {len(all_recipes_dict)} 份食譜。")
            print(f"資料已儲存到 {output_filename}")
        except Exception as e:
            print(f"\n❌ 儲存檔案時發生錯誤: {e}")
    else:
         print("\n❌ 爬蟲完成，但沒有成功提取任何食譜資料。")

if __name__ == '__main__':
    main()