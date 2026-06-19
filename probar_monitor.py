"""
Script de prueba: corre el monitor en modo visible para verificar que funciona.
No envía notificaciones ni modifica last_seen.json.
"""
import os
import yaml
from playwright.sync_api import sync_playwright
from monitor import login, get_available_turnos

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

especialidades = [e.lower() for e in config.get("especialidades", [])]

print(f"Buscando turnos para: {especialidades}")
print("Abriendo navegador...\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    page = browser.new_page()
    try:
        login(page)
        print("Login OK. Buscando turnos...")
        turnos = get_available_turnos(page, especialidades)
    finally:
        browser.close()

if not turnos:
    print("\nNo hay turnos disponibles en este momento.")
else:
    print(f"\n¡Se encontraron {len(turnos)} turno(s)!")
    for t in turnos:
        print(f"  - {t['especialidad']} | {t['medico']} | {t['fecha']} {t['hora']}")
