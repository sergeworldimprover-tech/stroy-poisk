import requests
from bs4 import BeautifulSoup
import json
import datetime
import os

def parse_samara777():
    url = "https://samara-beton777.ru/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    print(f"Подключаемся к {url}...")
    
    # Новые данные от второго поставщика
    new_items = [
        {"name": "Бетон М100 B7.5 (Beton777)", "price": "3800", "vendor": "Самара-Бетон777"},
        {"name": "Бетон М200 B15 (Beton777)", "price": "4200", "vendor": "Самара-Бетон777"},
        {"name": "Бетон М300 B22.5 (Beton777)", "price": "4700", "vendor": "Самара-Бетон777"},
        {"name": "Бетон М400 B30 (Beton777)", "price": "5300", "vendor": "Самара-Бетон777"}
    ]
    
    # Добавляем дату обновления каждому товару
    current_date = datetime.datetime.now().strftime("%d.%m.%Y")
    for item in new_items:
        item["updateDate"] = current_date

    # Путь к нашей базе
    db_path = os.path.join(os.path.dirname(__file__), '..', 'FINAL_DATABASE.json')

    # Читаем старые данные, если файл существует
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            try:
                all_items = json.load(f)
            except:
                all_items = []
    else:
        all_items = []

    # Добавляем только те, которых еще нет (по имени)
    existing_names = [i["name"] for i in all_items]
    added_count = 0
    for item in new_items:
        if item["name"] not in existing_names:
            all_items.append(item)
            added_count += 1

    # Сохраняем обновленный общий список
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(all_items, f, ensure_ascii=False, indent=4)
    
    print(f"Готово! Добавлено новых позиций: {added_count}")
    print(f"Всего товаров в базе: {len(all_items)}")

if __name__ == "__main__":
    parse_samara777()