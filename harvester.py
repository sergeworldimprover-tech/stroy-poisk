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

# УБИРАЕМ ОШИБКИ SSL (ВАЖНО ДЛЯ WINDOWS 7)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGETS_FILE = Path("targets.json")
OUTPUT_FILE = Path("FINAL_DATABASE.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

logger = logging.getLogger("harvester")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


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

    text = text.replace("\xa0", " ").replace(",", ".")
    digits = re.sub(r"\D", "", text)

    return int(digits) if digits else None


def parse_with_selectors(html, vendor_name, selectors):
    soup = BeautifulSoup(html, "html.parser")

    rows = soup.select(selectors.get("row", ""))
    items = []

    for row in rows:
        name_el = row.select_one(selectors.get("name", ""))
        price_el = row.select_one(selectors.get("price", ""))

        if not name_el or not price_el:
            continue

        name = name_el.get_text(strip=True)
        price = normalize_price(price_el.get_text(strip=True))

        if not name or price is None:
            continue

        items.append({
            "name": name,
            "price": price,
            "vendor": vendor_name
        })

    return items


def polite_sleep():
    time.sleep(random.uniform(1, 3))


def run_harvester():
    setup_logging()

    try:
        with open(TARGETS_FILE, "r", encoding="utf-8-sig") as f:
            targets = json.load(f)
    except Exception as e:
        logger.error(f"Ошибка чтения targets.json: {e}")
        return

    session = build_session()
    final_db = []

    for key, info in targets.items():
        vendor = info.get("name", key)
        url = info.get("url")

        logger.info(f"Запрос: {vendor}")

        try:
            # 🔥 ВОТ ТУТ ГЛАВНОЕ ИСПРАВЛЕНИЕ (SSL OFF)
            response = session.get(url, headers=HEADERS, timeout=20, verify=False)

            if response.status_code != 200:
                logger.warning(f"{vendor} вернул {response.status_code}")
                continue

            response.encoding = "utf-8"

            items = parse_with_selectors(
                response.text,
                vendor,
                info.get("selectors", {})
            )

            logger.info(f"Найдено: {len(items)} товаров")

            final_db.extend(items)

        except Exception as e:
            logger.error(f"Ошибка {vendor}: {e}")

        polite_sleep()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_db, f, ensure_ascii=False, indent=2)

    logger.info(f"Готово. Всего товаров: {len(final_db)}")


if __name__ == "__main__":
    run_harvester()
