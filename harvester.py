import importlib
import json
import logging
import random
import re
import time
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TARGETS_FILE = Path("targets.json")
OUTPUT_FILE = Path("FINAL_DATABASE.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

logger = logging.getLogger("harvester")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def build_session():
    session = requests.Session()

    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def normalize_price(price_text):
    if not price_text:
        return None

    text = price_text.replace("\xa0", " ").replace(",", ".")
    digits = re.sub(r"\D", "", text)

    return int(digits) if digits else None


def parse_with_selectors(html, vendor_name, selectors, delivery_price):
    soup = BeautifulSoup(html, "html.parser")

    rows = soup.select(selectors.get("row", "tr"))

    items = []

    for row in rows:
        try:
            name_el = row.select_one(selectors.get("name"))
            price_el = row.select_one(selectors.get("price"))

            if not name_el or not price_el:
                continue

            name = name_el.get_text(strip=True)
            price = normalize_price(price_el.get_text(strip=True))

            if not name or price is None:
                continue

            items.append({
                "name": name,
                "price": price,
                "vendor": vendor_name,
                "delivery_price_per_m3": delivery_price
            })

        except:
            continue

    return items


def polite_sleep():
    delay = random.uniform(1, 3)
    print(f"⏳ Пауза {round(delay, 2)} сек...")
    time.sleep(delay)


def run_harvester():
    setup_logging()

    try:
        with open(TARGETS_FILE, "r", encoding="utf-8-sig") as f:
            targets = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка чтения targets.json: {e}")
        return

    session = build_session()
    final_db = []

    for key, info in targets.items():
        vendor_name = info.get("name", key)
        url = info.get("url")
        selectors = info.get("selectors", {})
        delivery_price = info.get("meta", {}).get("delivery_price_per_m3")

        print(f"\n📡 Парсим: {vendor_name}")

        try:
            if not url:
                print("⚠️ Нет URL")
                continue

            response = session.get(url, headers=HEADERS, timeout=20)

            if response.status_code != 200:
                print(f"⚠️ Ошибка доступа: {response.status_code}")
                continue

            response.encoding = response.encoding or "utf-8"

            items = parse_with_selectors(
                html=response.text,
                vendor_name=vendor_name,
                selectors=selectors,
                delivery_price=delivery_price
            )

            print(f"✅ Найдено товаров: {len(items)}")

            final_db.extend(items)

        except Exception as e:
            print(f"❌ Ошибка: {e}")

        finally:
            polite_sleep()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_db, f, ensure_ascii=False, indent=2)

    print(f"\n💎 Готово! Всего товаров: {len(final_db)}")


if __name__ == "__main__":
    run_harvester()
