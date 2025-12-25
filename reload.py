# reload.py

import threading
import time
from queue import Queue
import msvcrt
import random
import argparse
import requests
from datetime import datetime, timedelta
import math
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config.config import URL, PROXY_FILE, LOG_FILE, DEFAULT_POST_DATA
from utils.helpers import load_proxies, get_random_proxy, get_random_headers, log

# ไฟล์ต่าง ๆ
GOOD_PROXY_FILE = "good_proxies.txt"
SEARCH_FILE = "search.txt"

def test_proxies(proxy_list, test_url="https://www.google.com", timeout=8):
    """ทดสอบ proxy ทีละตัว แล้วเจอ GOOD บันทึกลงไฟล์ทันที (realtime)"""
    good_count = 0
    total = len(proxy_list)
    print(f"กำลังทดสอบ {total:,} proxy ... (timeout {timeout}s)")
    print(f"เจอ GOOD จะบันทึกลง {GOOD_PROXY_FILE} ทันที")
    print("กด Ctrl+C เพื่อหยุด – ตัวที่ผ่านแล้วจะยังคงถูกบันทึกไว้\n")

    # สร้างไฟล์ใหม่พร้อม header
    with open(GOOD_PROXY_FILE, "w", encoding="utf-8") as f:
        f.write(f"# Good proxies - tested on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        for i, proxy_raw in enumerate(proxy_list, 1):
            proxy_url = f"socks5h://{proxy_raw}"
            proxies = {"http": proxy_url, "https": proxy_url}
            try:
                r = requests.get(test_url, proxies=proxies, timeout=timeout, verify=False)
                if r.status_code == 200:
                    with open(GOOD_PROXY_FILE, "a", encoding="utf-8") as f:
                        f.write(proxy_raw + "\n")
                    good_count += 1
                    print(f"[{i}/{total}] ✅ GOOD ({good_count}) → {proxy_raw}")
                else:
                    print(f"[{i}/{total}] ❌ BAD: {proxy_raw} (status {r.status_code})")
            except Exception as e:
                short_err = str(e).split('\n')[0][:50]
                print(f"[{i}/{total}] ❌ BAD: {proxy_raw} ({short_err})")
    except KeyboardInterrupt:
        print("\n\n⚠️ หยุดโดยผู้ใช้ – บันทึก proxy ที่ผ่านแล้วเรียบร้อย")

    print(f"\n🎉 เสร็จสิ้น: พบ proxy ที่ดี {good_count:,} ตัว → บันทึกใน {GOOD_PROXY_FILE}")

# ------------------ Argument Parser ------------------
parser = argparse.ArgumentParser(description="Reload script - เวอร์ชันสมบูรณ์สุด 2025")
parser.add_argument("method", nargs="?", default="get", choices=["get", "post", "head", "options", "put", "delete"],
                    help="HTTP method (default: get)")
parser.add_argument("--data", type=str, default=None, help="POST/PUT data เช่น key1=val1,key2=val2")
parser.add_argument("-n", "--total", type=int, help="จำนวน request ทั้งหมด (จำเป็นถ้าไม่ใช้ --test-proxies)")
parser.add_argument("-t", "--threads", type=int, default=50, help="จำนวน threads (default: 50)")
parser.add_argument("--proxy-file", type=str, default=PROXY_FILE, help="ไฟล์ proxy ที่จะใช้")
parser.add_argument("--test-proxies", action="store_true", help="โหมดทดสอบ proxy เท่านั้น")
parser.add_argument("--no-proxy", action="store_true", help="ไม่ใช้ proxy เลย")
args = parser.parse_args()

# ------------------ ตรวจสอบ argument ------------------
if args.test_proxies:
    if args.total is not None:
        parser.error("--test-proxies ไม่ต้องใช้ -n/--total")
    if args.no_proxy:
        parser.error("--test-proxies ไม่รองรับ --no-proxy")
else:
    if args.total is None or args.total <= 0:
        parser.error("-n/--total เป็นตัวเลือกบังคับเมื่อไม่ใช้ --test-proxies")

METHOD = args.method.upper()
USE_PROXY = not args.no_proxy

# ------------------ โหมดทดสอบ proxy ------------------
if args.test_proxies:
    print("=== โหมดทดสอบ proxy ===")
    all_proxies = load_proxies(PROXY_FILE)
    if not all_proxies:
        print("ไม่พบ proxy ในไฟล์ socks5.txt")
        exit(1)
    test_proxies(all_proxies)
    exit(0)

# ------------------ โหลด keyword สำหรับ POST ------------------
search_keywords = []
if os.path.exists(SEARCH_FILE):
    try:
        with open(SEARCH_FILE, "r", encoding="utf-8") as f:
            search_keywords = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        print(f"โหลด keyword จาก {SEARCH_FILE} สำเร็จ: {len(search_keywords)} คำ")
    except Exception as e:
        print(f"อ่าน {SEARCH_FILE} ไม่ได้: {e}")

# ------------------ จัดการ POST data ------------------
POST_DATA = None
if METHOD in ["POST", "PUT"]:
    if args.data:
        POST_DATA = dict(item.split("=") for item in args.data.split(","))
        print(f"ใช้ data คงที่: {POST_DATA}")
    elif search_keywords:
        POST_DATA = None  # จะสุ่มใน worker
        print("จะสุ่ม keyword จาก search.txt ทุก request")
    else:
        POST_DATA = {}
        print("ไม่มี search.txt และไม่มี --data → ส่ง POST ว่าง")

# ------------------ จัดการ Proxy ------------------
if USE_PROXY:
    selected_file = args.proxy_file
    if selected_file == GOOD_PROXY_FILE and not os.path.exists(GOOD_PROXY_FILE):
        print(f"ไม่พบ {GOOD_PROXY_FILE}")
        answer = input("ต้องการทดสอบ proxy ใหม่ก่อนไหม? (y/n): ").strip().lower()
        if answer == 'y':
            all_proxies = load_proxies(PROXY_FILE)
            test_proxies(all_proxies)
            selected_file = GOOD_PROXY_FILE

    PROXIES_LIST = load_proxies(selected_file)
    print(f"ใช้ proxy จาก: {selected_file} ({len(PROXIES_LIST):,} ตัว)")
else:
    PROXIES_LIST = []
    print("🚀 ไม่ใช้ proxy – รันตรงจาก IP ของคุณ")

TOTAL_REQUESTS = args.total
NUM_THREADS = args.threads

print(f"🎯 เป้าหมาย: {TOTAL_REQUESTS:,} request | {NUM_THREADS} threads | Method: {METHOD}")

# ------------------ Worker & Progress ------------------
task_queue = Queue()
stop_event = threading.Event()
sent_counter = 0
success_counter = 0
counter_lock = threading.Lock()
start_time = time.time()

def worker(thread_id):
    global sent_counter, success_counter
    session = requests.Session()
    
    while not stop_event.is_set():
        try:
            task_queue.get(timeout=1)
        except:
            continue
        
        proxies = get_random_proxy(PROXIES_LIST) if USE_PROXY else None
        proxy_str = proxies['https'] if proxies else "Direct (No Proxy)"
        headers = get_random_headers()
        
        # จัดการ POST data แบบสุ่ม
        post_data = {}
        if METHOD in ["POST", "PUT"]:
            if args.data:
                post_data = POST_DATA.copy()
            elif search_keywords:
                random_keyword = random.choice(search_keywords)
                post_data = {"search": random_keyword}  # แก้ชื่อ key ถ้าเว็บใช้ชื่ออื่น เช่น "q"
            else:
                post_data = POST_DATA.copy()

        try:
            r = session.request(
                METHOD,
                URL,
                headers=headers,
                proxies=proxies,
                data=post_data,
                timeout=10 if USE_PROXY else 20,
                verify=False
            )

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            size = len(r.text) if hasattr(r, 'text') else "N/A"
            used_data = post_data if METHOD in ["POST", "PUT"] else "N/A"
            log(f"[T{thread_id}] [{now}] {METHOD} {r.status_code} Size={size} Data={used_data} Proxy: {proxy_str}", LOG_FILE)

            with counter_lock:
                sent_counter += 1
                if r.status_code in [200, 301, 302]:
                    success_counter += 1
                if sent_counter >= TOTAL_REQUESTS:
                    stop_event.set()

        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ProxyError):
            pass
        except Exception as e:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            error_msg = str(e).split('\n')[0]
            log(f"[T{thread_id}] [{now}] ERROR: {error_msg} Proxy: {proxy_str}", LOG_FILE)

        finally:
            time.sleep(random.uniform(0.1, 0.8))
            with counter_lock:
                sent_counter += 1
                if sent_counter >= TOTAL_REQUESTS:
                    stop_event.set()
            task_queue.task_done()

def print_progress():
    while not stop_event.is_set():
        with counter_lock:
            elapsed = time.time() - start_time
            speed = sent_counter / elapsed if elapsed > 0 else 0
            percent = (sent_counter / TOTAL_REQUESTS) * 100 if TOTAL_REQUESTS > 0 else 0
            print(f"\rProgress: {sent_counter:,}/{TOTAL_REQUESTS:,} ({percent:.1f}%) | Success: {success_counter:,} | Speed: {speed:.1f} req/s", end="")
        time.sleep(0.5)
    print()

def main():
    tasks_per_thread = math.ceil(TOTAL_REQUESTS / NUM_THREADS)
    print(f"แต่ละ thread ส่ง ≈ {tasks_per_thread:,} request")
    print("⚡ Timeout 10 วินาที – ข้าม proxy ตายเร็วสุด")

    workers = [threading.Thread(target=worker, args=(i+1,), daemon=True) for i in range(NUM_THREADS)]
    for w in workers:
        w.start()

    total_tasks = 0
    for i in range(NUM_THREADS):
        tasks_for_this = min(tasks_per_thread, TOTAL_REQUESTS - total_tasks)
        for _ in range(tasks_for_this):
            task_queue.put("reload")
            total_tasks += 1
        if total_tasks >= TOTAL_REQUESTS:
            break

    print(f"แจก task เรียบร้อย ({total_tasks:,} task) – เริ่มส่ง!")

    progress_thread = threading.Thread(target=print_progress, daemon=True)
    progress_thread.start()

    while not stop_event.is_set() and sent_counter < TOTAL_REQUESTS:
        if msvcrt.kbhit() and msvcrt.getch().lower() == b'q':
            print("\n❌ ยกเลิกโดยผู้ใช้")
            stop_event.set()
            break
        time.sleep(0.1)

    for w in workers:
        w.join()

    elapsed = time.time() - start_time
    speed = sent_counter / elapsed if elapsed > 0 else 0
    print(f"\n✅ เสร็จสิ้น: ส่ง {sent_counter:,} request (Success: {success_counter:,}) ใน {timedelta(seconds=int(elapsed))} | เฉลี่ย {speed:.1f} req/s")

if __name__ == "__main__":
    main()