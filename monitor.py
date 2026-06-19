import os
import subprocess
import yaml
from playwright.sync_api import sync_playwright
from state import load_state, save_state, should_notify, increment, make_slot_key
from notify import notify_turno


def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def login(page):
    page.goto("https://portal.dim.com.ar/")
    page.wait_for_load_state("networkidle")
    page.fill('[name="nro_documento"]', os.environ["PORTAL_DNI"])
    page.fill('[name="password"]', os.environ["PORTAL_PASSWORD"])
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    if page.url.startswith("https://portal.dim.com.ar/") and page.query_selector('[name="nro_documento"]'):
        raise RuntimeError(f"Login failed — still on login page: {page.url}")


def get_available_turnos(page, especialidades):
    """
    Retorna lista de dicts: [{especialidad, medico, fecha, hora}, ...]
    Completar con selectores reales de PORTAL_NOTES.md.
    """
    turnos = []

    # === COMPLETAR CON SELECTORES DE PORTAL_NOTES.md ===
    #
    # Patrón general (ajustar nombres de selectores):
    #
    # # Navegar a sección de turnos
    # page.click('[selector del link/botón de turnos]')
    # page.wait_for_load_state("networkidle")
    #
    # for especialidad in especialidades:
    #     # Seleccionar especialidad
    #     page.select_option('[selector dropdown especialidad]', label=especialidad)
    #     # o: page.click(f'text={especialidad}')
    #     page.wait_for_load_state("networkidle")
    #
    #     # Iterar turnos disponibles
    #     items = page.query_selector_all('[selector de cada fila/card de turno]')
    #     for item in items:
    #         medico = item.query_selector('[selector médico]').inner_text().strip()
    #         fecha = item.query_selector('[selector fecha]').inner_text().strip()
    #         hora = item.query_selector('[selector hora]').inner_text().strip()
    #         turnos.append({
    #             "especialidad": especialidad,
    #             "medico": medico,
    #             "fecha": fecha,
    #             "hora": hora,
    #         })
    #
    # =====================================================

    return turnos


def commit_state():
    subprocess.run(["git", "config", "user.email", "bot@github.com"], check=False)
    subprocess.run(["git", "config", "user.name", "turno-monitor[bot]"], check=False)
    subprocess.run(["git", "add", "last_seen.json"], check=False)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if result.returncode != 0:
        subprocess.run(["git", "commit", "-m", "chore: actualizar estado turnos"], check=False)
        subprocess.run(["git", "push"], check=False)


def main():
    config = load_config()
    state = load_state()
    especialidades = [e.lower() for e in config.get("especialidades", [])]
    max_per_day = config["notificaciones"]["max_por_turno_por_dia"]
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")

    turnos = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            login(page)
            turnos = get_available_turnos(page, especialidades)
        finally:
            browser.close()

    for turno in turnos:
        key = make_slot_key(
            turno["especialidad"],
            turno.get("medico", ""),
            turno["fecha"],
            turno["hora"],
        )
        if should_notify(state, key, max_per_day):
            notify_turno(turno, config, gmail_pass, tg_token)
            state = increment(state, key)

    save_state(state)

    if os.environ.get("CI"):
        commit_state()


if __name__ == "__main__":
    main()
