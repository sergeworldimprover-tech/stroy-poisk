import requests
from bs4 import BeautifulSoup
import json

def run_harvester():
    try:
        with open('targets.json', 'r', encoding='utf-8-sig') as f:
            targets = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка конфига: {e}")
        return

    final_db = []
    # Максимально "человеческие" заголовки
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://metal-market.ru/'
    }

    for key, info in targets.items():
        print(f"📡 Попытка прорыва: {info['name']}...")
        try:
            # Создаем сессию, чтобы сайт "запомнил" нас
            session = requests.Session()
            res = session.get(info['url'], headers=headers, timeout=20)
            res.encoding = 'utf-8'
            
            if res.status_code != 200:
                print(f"⚠️ Ошибка доступа: {res.status_code}")
                continue

            soup = BeautifulSoup(res.text, 'html.parser')
            # Ищем все строки таблицы
            items = soup.find_all('tr', class_='item_row')
            
            count = 0
            for item in items:
                try:
                    name_el = item.select_one('td.name')
                    price_el = item.select_one('td.price')
                    
                    if name_el and price_el:
                        name = name_el.get_text(strip=True)
                        price_text = price_el.get_text(strip=True)
                        
                        # Оставляем только цифры
                        clean_price = "".join(filter(str.isdigit, price_text))
                        
                        if name and clean_price:
                            final_db.append({
                                "name": name,
                                "price": int(clean_price),
                                "vendor": info['name']
                            })
                            count += 1
                except: continue
            
            print(f"✅ Успех! Собрано позиций: {count}")
            
        except Exception as e:
            print(f"⚠️ Ошибка на {info['name']}: {e}")

    with open('FINAL_DATABASE.json', 'w', encoding='utf-8') as f:
        json.dump(final_db, f, ensure_ascii=False, indent=2)
    print(f"\n💎 База обновлена! Всего товаров: {len(final_db)}")

if __name__ == "__main__":
    run_harvester()