# utils/helpers.py

import random
from datetime import datetime
from config.config import USER_AGENTS, BASE_HEADERS

def load_proxies(proxy_file):
    try:
        with open(proxy_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        print(f"โหลด proxy สำเร็จ: {len(lines):,} ตัว (ไม่ตรวจ live – รันเร็วสุด)")
        return lines
    except FileNotFoundError:
        print(f"ไม่พบไฟล์ {proxy_file} ! ทำงานแบบไม่มี proxy")
        return []

def get_random_proxy(proxies_list):
    if not proxies_list:
        return None
    proxy_raw = random.choice(proxies_list)
    proxy_url = f"socks5h://{proxy_raw}"  # 'h' = resolve DNS ผ่าน proxy (ดีที่สุด)
    return {"http": proxy_url, "https": proxy_url}

def get_random_headers():
    headers = BASE_HEADERS.copy()
    headers['User-Agent'] = random.choice(USER_AGENTS)
    return headers

def log(msg, log_file):
    print(msg)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(msg + "\n")