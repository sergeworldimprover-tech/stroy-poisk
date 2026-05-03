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


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def normalize_price(price_text: str) -> int | None:
    if not price_text:
        return None

    normalized = price_text.replace("\xa0", " ").replace(",", ".")
    match = re.search(r"\d+(?:[\s.]\d{3})*(?:\.\d+)?", normalized)
    if not match:
        return None

    number = match.group(0).replace(" ", "")
    number = number.split(".")[0]
    digits = re.sub(r"\D", "", number)
    return int(digits) if digits else None


def parse_with_selectors(html: str, vendor_name: str, selectors: dict[str, str]) -> list[dict[str, Any]]:
    row_selector = selectors.get("row")
    name_selector = selectors.get("name")
    price_selector = selectors.get("price")

    if not all((row_selector, name_selector, price_selector)):
        logger.warning("Пропускаю %s: не заданы row/name/price селекторы", vendor_name)
        return []

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select(row_selector)

    items: list[dict[str, Any]] = []
    for row in rows:
        name_el = row.select_one(name_selector)
        price_el = row.select_one(price_selector)
        if not name_el or not price_el:
            continue

        name = name_el.get_text(strip=True)
        price = normalize_price(price_el.get_text(" ", strip=True))
        if not name or price is None:
            continue

        items.append({"name": name, "price": price, "vendor": vendor_name})

    return items


def run_custom_parser(parser_path: str, target: dict[str, Any]) -> list[dict[str, Any]]:
    module_name, _, function_name = parser_path.partition(":")
    module = importlib.import_module(f"parsers.{module_name}")

    callable_name = function_name or f"parse_{module_name.replace('parser_', '')}"
    parser_func = getattr(module, callable_name)

    result = parser_func(target) if parser_func.__code__.co_argcount else parser_func()
    if result is None:
        logger.warning(
            "Кастомный парсер '%s' не вернул данные (None). Использую пустой список.", parser_path
        )
        return []
    if not isinstance(result, list):
        raise TypeError(f"Кастомный парсер '{parser_path}' должен вернуть list, получено: {type(result)}")
    return result


def polite_sleep() -> None:
    delay = random.uniform(1, 3)
    logger.info("Пауза %.2f сек. между запросами", delay)
    time.sleep(delay)


def load_targets() -> dict[str, Any]:
    with TARGETS_FILE.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def run_harvester() -> None:
    setup_logging()

    try:
        targets = load_targets()
    except Exception as exc:
        logger.error("Ошибка чтения targets.json: %s", exc)
        return

    session = build_session()
    final_db: list[dict[str, Any]] = []

    for key, info in targets.items():
        vendor_name = info.get("name", key)
        url = info.get("url")

        logger.info("Старт парсинга: %s", vendor_name)

        try:
            parser_path = info.get("parser")
            if parser_path:
                items = run_custom_parser(parser_path, info)
                logger.info("Кастомный парсер %s: собрано %s позиций", parser_path, len(items))
            else:
                if not url:
                    logger.warning("Пропускаю %s: не задан url", vendor_name)
                    continue

                response = session.get(url, headers=HEADERS, timeout=20)
                if response.status_code != 200:
                    logger.warning("%s вернул статус %s", vendor_name, response.status_code)
                    continue

                response.encoding = response.encoding or "utf-8"
                items = parse_with_selectors(
                    html=response.text,
                    vendor_name=vendor_name,
                    selectors=info.get("selectors", {}),
                )
                logger.info("Универсальный парсер: собрано %s позиций", len(items))

            final_db.extend(items)

        except Exception as exc:
            logger.exception("Ошибка при обработке %s: %s", vendor_name, exc)
        finally:
            polite_sleep()

    OUTPUT_FILE.write_text(json.dumps(final_db, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Готово. Всего товаров: %s", len(final_db))


if __name__ == "__main__":
    run_harvester()
