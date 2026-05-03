import json
import random
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

# отключаем ошибки SSL (ВАЖНО для твоего сайта)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGETS_FILE = Path("targets.json")
OUTPUT_FILE = Path("FINAL_DATABASE.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def build_session():
    session = requests.Session()

    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def normalize_price(text):
    if not text:
        return None
    digits = re.sub(r"\D", "", text)
    return int(digits) if digits else None


def parse(html, selectors, vendor, delivery_price):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select(selectors["row"])

    items = []

    for row in rows:
        try:
            name_el = row.select_one(selectors["name"])
            price_el = row.select_one(selectors["price"])

            if not name_el or not price_el:
                continue

            name = name_el.get_text(strip=True)
            price = normalize_price(price_el.get_text())

            if not name or price is None:
                continue

            items.append({
                "name": name,
                "price": price,
                "vendor": vendor,
                "delivery_price_per_m3": delivery_price
            })
        except:
            continue

    return items


def run():
    try:
        with open(TARGETS_FILE, "r", encoding="utf-8-sig") as f:
            targets = json.load(f)
    except Exception as e:
        print("Ошибка targets.json:", e)
        return

    session = build_session()
    final_db = []

    for key, info in targets.items():
        print(f"\n📡 Парсим: {info['name']}")

        try:
            response = session.get(
                info["url"],
                headers=HEADERS,
                timeout=20,
                verify=False  # <-- ключевой фикс
            )

            if response.status_code != 200:
                print("Ошибка доступа:", response.status_code)
                continue

            items = parse(
                response.text,
                info["selectors"],
                info["name"],
                info.get("meta", {}).get("delivery_price_per_m3")
            )

            print(f"✅ Найдено: {len(items)}")
            final_db.extend(items)

        except Exception as e:
            print("Ошибка:", e)

        time.sleep(random.uniform(1, 3))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_db, f, ensure_ascii=False, indent=2)

    print(f"\n💎 Готово. Всего товаров: {len(final_db)}")


if __name__ == "__main__":
    run()
