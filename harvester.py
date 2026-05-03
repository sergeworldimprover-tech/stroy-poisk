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

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGETS_FILE = Path("targets.json")
OUTPUT_FILE = Path("FINAL_DATABASE.json")

HEADERS = {
"User-Agent": "Mozilla/5.0"
}

def build_session():
session = requests.Session()
retry = Retry(total=3, backoff_factor=1)
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

```
items = []

for row in rows:
    try:
        name = row.select_one(selectors["name"]).get_text(strip=True)
        price = normalize_price(row.select_one(selectors["price"]).get_text())

        if name and price:
            items.append({
                "name": name,
                "price": price,
                "vendor": vendor,
                "delivery_price_per_m3": delivery_price
            })
    except:
        continue

return items
```

def run():
with open(TARGETS_FILE, "r", encoding="utf-8-sig") as f:
targets = json.load(f)

```
session = build_session()
final_db = []

for key, info in targets.items():
    print(f"\n📡 Парсим: {info['name']}")

    try:
        r = session.get(info["url"], headers=HEADERS, timeout=20, verify=False)

        if r.status_code != 200:
            print("Ошибка:", r.status_code)
            continue

        items = parse(
            r.text,
            info["selectors"],
            info["name"],
            info.get("meta", {}).get("delivery_price_per_m3")
        )

        print("✅ Найдено:", len(items))
        final_db.extend(items)

    except Exception as e:
        print("❌ Ошибка:", e)

    time.sleep(random.uniform(1, 2))

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_db, f, ensure_ascii=False, indent=2)

print("\n💎 Готово:", len(final_db))
```

if **name** == "**main**":
run()
