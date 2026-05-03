import json
import os

def add_target():
    print("--- ДОБАВЛЕНИЕ НОВОГО ЗАВОДА (МЕНЕДЖЕР) ---")
    key = input("Кодовое имя (на англ, например 'mayak'): ")
    name = input("Название завода (для отображения): ")
    url = input("Ссылка на прайс-лист: ")
    
    print("\n--- НАСТРОЙКА СЕЛЕКТОРОВ (BS4) ---")
    row_sel = input("Селектор строки товара (например, '.product-row'): ")
    name_sel = input("Селектор названия (внутри строки): ")
    price_sel = input("Селектор цены (внутри строки): ")

    # Загружаем с поддержкой utf-8-sig
    targets = {}
    if os.path.exists('targets.json'):
        try:
            with open('targets.json', 'r', encoding='utf-8-sig') as f:
                targets = json.load(f)
        except json.JSONDecodeError:
            targets = {}

    # Добавляем данные
    targets[key] = {
        "name": name,
        "url": url,
        "selectors": {
            "row": row_sel,
            "name": name_sel,
            "price": price_sel
        }
    }

    # Сохраняем всегда в чистом utf-8
    with open('targets.json', 'w', encoding='utf-8') as f:
        json.dump(targets, f, ensure_ascii=False, indent=4)
    
    print(f"\n✅ Завод '{name}' добавлен! Теперь запусти harvester.py")

if __name__ == "__main__":
    add_target()