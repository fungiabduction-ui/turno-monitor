@echo off
set PORTAL_DNI=32771311
set PORTAL_PASSWORD=32771311
set GMAIL_APP_PASSWORD=
set TELEGRAM_BOT_TOKEN=
python "%~dp0probar_monitor.py" > "%~dp0resultado.txt" 2>&1
echo Listo. Abriendo resultado...
notepad "%~dp0resultado.txt"
