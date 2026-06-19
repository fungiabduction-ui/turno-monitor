import os
from pathlib import Path
from playwright.sync_api import sync_playwright

Path("screenshots").mkdir(exist_ok=True)


def main():
    dni = os.environ.get("PORTAL_DNI")
    password = os.environ.get("PORTAL_PASSWORD")
    if not dni or not password:
        print("Error: Set PORTAL_DNI and PORTAL_PASSWORD environment variables first.")
        print("  Windows: $env:PORTAL_DNI='32771311'; $env:PORTAL_PASSWORD='32771311'")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=800)
        page = browser.new_page()

        print("→ Abriendo portal...")
        page.goto("https://portal.dim.com.ar/")
        page.wait_for_load_state("networkidle")
        page.screenshot(path="screenshots/01_login_page.png")

        print("→ Completando login...")
        page.fill('[name="nro_documento"]', dni)
        page.fill('[name="password"]', password)
        page.screenshot(path="screenshots/02_filled.png")

        page.press('[name="password"]', 'Enter')
        page.wait_for_load_state("networkidle")
        page.screenshot(path="screenshots/03_post_login.png")

        print("\n→ Links disponibles post-login:")
        for link in page.query_selector_all("a"):
            print(f"  text={link.inner_text().strip()!r}  href={link.get_attribute('href')!r}")

        print("\n→ Botones disponibles post-login:")
        for btn in page.query_selector_all("button"):
            print(f"  text={btn.inner_text().strip()!r}")

        input("\nNavegá manualmente hasta la sección de turnos y presioná Enter...")
        page.screenshot(path="screenshots/04_turnos_page.png")

        print("\n→ HTML de la página de turnos (primeros 8000 chars):")
        print(page.content()[:8000])

        browser.close()

    print("\nScreenshots guardados en screenshots/")
    print("Documentá los selectores en PORTAL_NOTES.md")


if __name__ == "__main__":
    main()
