import logging
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

logger = logging.getLogger("harvester")
BETON_HTML_PATH = Path("beton.html")


def _normalize_price(raw_price: str) -> int | None:
    digits = re.sub(r"\D", "", raw_price or "")
    return int(digits) if digits else None


def parse_betonsamara(target: dict[str, Any]) -> list[dict[str, Any]]:
    vendor = target.get("name", "Бетон Самара")

    if not BETON_HTML_PATH.exists():
        logger.error("Файл %s не найден", BETON_HTML_PATH)
        return []

    html = BETON_HTML_PATH.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    items: list[dict[str, Any]] = []
    for tr in soup.select("table tr"):
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue

        name = tds[0].get_text(" ", strip=True)
        price_text = tds[1].get_text(" ", strip=True)

        if not name or "заказать" in name.lower():
            continue

        price = _normalize_price(price_text)
        if price is None:
            continue

        items.append(
            {
                "name": name,
                "price": price,
                "vendor": vendor,
                "delivery_price_per_m3": 700,
            }
        )

    logger.info("Собрано %s позиций с betonsamara", len(items))
    return items
