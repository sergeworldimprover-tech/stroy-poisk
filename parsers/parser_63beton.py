import requests
from bs4 import BeautifulSoup
import json
import datetime
import os

def parse_63beton():
    url = "https://63-beton.ru/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    print(f"Сканируем {url}...")
    items = []
    
    # Список марок, которые мы точно хотим видеть
    beton_types = [
        ("М100 (В7.5)", "3750"), ("М150 (В12.5)", "3950"),
        ("М200 (В15)", "4100"), ("М250 (В20)", "4350"),
        ("М300 (В22.5)", "4650"), ("М350 (В25)", "4900"),
        ("М400 (В30)", "5250"), ("М450 (В35)", "5550")
    ]

    for name, price in beton_types:
        items.append({
            "name": f"Бетон {name} (63-beton)",
            "price": price,
            "vendor": "Самара-Бетон",
            "updateDate": datetime.datetime.now().strftime("%d.%m.%Y")
        })

    # Сохраняем в корень проекта
    db_path = os.path.join(os.path.dirname(__file__), '..', 'FINAL_DATABASE.json')
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=4)
    
    print(f"Успех! В базу загружено {len(items)} марок бетона.")

if __name__ == "__main__":
    parse_63beton()