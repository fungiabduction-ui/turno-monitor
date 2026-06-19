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
    page.screenshot(path="debug_01_loaded.png")

    page.fill('[name="nro_documento"]', os.environ["PORTAL_DNI"])
    page.fill('[name="password"]', os.environ["PORTAL_PASSWORD"])
    page.wait_for_timeout(1000)
    page.screenshot(path="debug_02_filled.png")

    buttons = page.evaluate('''
        () => [...document.querySelectorAll("button")].map(b => ({
            text: b.innerText.trim(),
            cls: b.className,
            h: b.offsetHeight,
            w: b.offsetWidth
        }))
    ''')
    print(f"[login] buttons on page: {buttons}")

    page.locator('button.ptur-buttonLogin').click()
    page.wait_for_timeout(2000)
    page.screenshot(path="debug_03_after_click.png")
    print(f"[login] URL after click: {page.url}")

    # Wait for login form to disappear (means login succeeded)
    try:
        page.wait_for_selector('[name="nro_documento"]', state="detached", timeout=30000)
    except Exception:
        page.screenshot(path="debug_04_timeout.png")
        raise RuntimeError("Login fallido — el portal no respondió o las credenciales son incorrectas")


def get_available_turnos(page, especialidades):
    turnos = []

    page.click('button.ptur-buscadorTurnos-btnOpc:has-text("Consulta médica")')
    page.wait_for_load_state("networkidle")

    page.click('button.ptur-buscadorTurnos-btnOpc:has-text("Para mi")')
    page.wait_for_load_state("networkidle")

    for especialidad in especialidades:
        # Click specialty button matching normalized name (handles accents/case)
        clicked = page.evaluate(f'''
            () => {{
                const norm = s => s.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").trim();
                for (const btn of document.querySelectorAll("button.ptur-buscadorTurnos-btnOpc")) {{
                    if (norm(btn.innerText) === "{especialidad}") {{ btn.click(); return true; }}
                }}
                return false;
            }}
        ''')
        if not clicked:
            print(f"[monitor] Especialidad '{especialidad}' no encontrada en el portal")
            continue

        page.wait_for_load_state("networkidle")
        page.click('button.ptur-consulta-botonSiguiente')
        page.wait_for_load_state("networkidle")

        slots = page.evaluate('''
            () => {
                const results = [];
                document.querySelectorAll("button").forEach(btn => {
                    if (btn.innerText.trim() !== "Confirmar") return;
                    let el = btn;
                    for (let i = 0; i < 6; i++) el = el.parentElement;
                    const doctorEl = el.querySelector("[class*=rb16m]");
                    const timeEl   = el.querySelector("[class*=rb16t]");
                    const dateEl   = timeEl ? timeEl.previousElementSibling : null;
                    const ps       = el.querySelectorAll("p");
                    const addrEl   = el.querySelector("a[href]");
                    results.push({
                        medico:       doctorEl ? doctorEl.innerText.trim() : "",
                        fecha:        dateEl   ? dateEl.innerText.trim()   : "",
                        hora:         timeEl   ? timeEl.innerText.trim()   : "",
                        especialidad: ps[0]    ? ps[0].innerText.trim()    : "",
                        sucursal:     ps[1]    ? ps[1].innerText.trim()    : "",
                        direccion:    addrEl   ? addrEl.innerText.trim()   : "",
                    });
                });
                return results;
            }
        ''')

        for slot in slots:
            if slot["medico"]:
                slot["especialidad"] = slot["especialidad"] or especialidad
                turnos.append(slot)

        if len(especialidades) > 1:
            page.go_back()
            page.go_back()
            page.wait_for_load_state("networkidle")

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
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        try:
            login(page)
            turnos = get_available_turnos(page, especialidades)
        finally:
            context.close()
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
