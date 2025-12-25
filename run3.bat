@echo off
title Ultimate Reload Loop
color 0c

:loop
echo [รอบใหม่] HEAD ไม่ใช้ proxy
python reload.py head -n 150000 -t 300 --no-proxy

echo [รอบใหม่] GET ใช้ proxy ดี
python reload.py -n 80000 -t 120 --proxy-file good_proxies.txt

echo [รอบใหม่] OPTIONS อุ่นเครื่อง
python reload.py options -n 50000 -t 100

echo พัก 20 วินาที...
timeout /t 20 >nul

goto loop