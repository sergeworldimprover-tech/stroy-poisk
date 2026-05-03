import requests
from bs4 import BeautifulSoup
import re


def normalize_price(text):
    digits = re.sub(r"\D", "", text)
    return int(digits) if digits else None


def parse_betonsamara(target):
    url = target.get("url")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")

    items = []

    # ищем все строки таблицы
    rows = soup.select("table tr")

    for row in rows:
        cols = row.find_all("td")

        if len(cols) < 2:
            continue

        name = cols[0].get_text(strip=True)
        price = normalize_price(cols[1].get_text())

        if not name or not price:
            continue

        items.append({
            "name": name,
            "price": price,
            "vendor": target.get("name")
        })

    return items