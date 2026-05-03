import requests

def hard_test():
    # Мы пробуем зайти на Google по его прямому IP
    url = "http://8.8.8.8" 
    print(f"📡 Пробуем прямое попадание по IP (8.8.8.8)...")
    try:
        res = requests.get(url, timeout=5)
        print(f"✅ Связь есть! Статус: {res.status_code}")
        print("Значит, интернет работает, но сломаны Имена (DNS).")
    except Exception as e:
        print(f"❌ Даже по IP не пускает. Ошибка: {e}")
        print("Проверь, не включен ли у тебя VPN или прокси в системе.")

if __name__ == "__main__":
    hard_test()