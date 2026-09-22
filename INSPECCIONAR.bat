@echo off
if "%PORTAL_DNI%"=="" set /p PORTAL_DNI=DNI del portal DIM:
if "%PORTAL_PASSWORD%"=="" set /p PORTAL_PASSWORD=Contraseña del portal DIM:
python "%~dp0inspect_portal.py"
pause
