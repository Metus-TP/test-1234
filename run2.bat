@echo off
title Reload Loop Light
color 0b
echo ยิง loop อัตโนมัติ - เวอร์ชันเบา

:loop
echo [%date% %time%] ยิง HEAD 50,000 ครั้ง
python reload.py head -n 50000 -t 150 --no-proxy

echo พัก 15 วินาที...
timeout /t 15 >nul

goto loop