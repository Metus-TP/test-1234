@echo off
title Reload Loop Auto - ยิงไม่หยุด!
color 0a
echo ==================================================
echo       RELOAD SCRIPT LOOP อัตโนมัติ
echo       ยิงไม่หยุดจนกว่าจะปิดหน้าต่างนี้
echo       กด Ctrl+C เพื่อหยุดชั่วคราว
echo ==================================================
echo.

:loop

echo [%date% %time%] เริ่มรอบใหม่ - ยิง HEAD ไม่ใช้ proxy (เร็ว + แรงสุด)
python reload.py head -n 100000 -t 250 --no-proxy
echo.

echo [%date% %time%] ยิง GET ใช้ proxy ที่ดี (โหลดภาพหนักจริง)
python reload.py -n 50000 -t 100 --proxy-file good_proxies.txt
echo.

echo [%date% %time%] พัก 10 วินาที ก่อนรอบถัดไป...
timeout /t 10 >nul

echo.
echo ==================================================
echo               รอบใหม่เริ่มแล้ว!
echo ==================================================
echo.

goto loop