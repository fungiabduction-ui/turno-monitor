@echo off
echo Instalando dependencias...
python -m pip install pyyaml requests playwright --quiet
python -m playwright install chromium

if "%PORTAL_DNI%"=="" set /p PORTAL_DNI=DNI del portal DIM:
if "%PORTAL_PASSWORD%"=="" set /p PORTAL_PASSWORD=Contraseña del portal DIM:

echo.
echo Probando monitor...
python "%~dp0probar_monitor.py" > "%~dp0resultado.txt" 2>&1
echo.
echo Listo. Abriendo resultado...
notepad "%~dp0resultado.txt"
