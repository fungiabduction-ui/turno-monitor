# turno-monitor — Monitor de Turnos DIM

Monitorea el portal de Obra Social DIM (portal.dim.com.ar) buscando turnos disponibles y envía notificaciones por email y Telegram.

## Cómo funciona

1. **GitHub Actions** corre `monitor.py` cada 10 minutos (cron `*/10 * * * *`)
2. El script abre el portal con Playwright (Chromium headless), hace login y navega hasta los turnos de las especialidades configuradas
3. Si encuentra un turno nuevo, manda mail y/o Telegram
4. El estado (qué slots ya se notificaron) se guarda en `last_seen.json` commiteado al repo

## Navegación en el portal

El wizard del buscador tiene estos pasos:
1. Click `button.ptur-buscadorTurnos-btnOpc:has-text("Consulta médica")`
2. Click `button.ptur-buscadorTurnos-btnOpc:has-text("Para mi")`
3. Esperar con `wait_for_function` hasta que carguen los botones de especialidad (el portal muestra un spinner)
4. Click en la especialidad (ej. "Endocrinología") usando normalización NFD para ignorar tildes
5. Click `button.ptur-consulta-botonSiguiente`
6. Leer tarjetas buscando botones "Confirmar" y extraer datos del médico, fecha, hora, sucursal

**Nota:** Después de "Para mi" aparecen beneficiarios del plan (ej. "Testa Pascual Domingo", "Li Gotti Ariana") como opciones alternativas — NO son un paso de selección, "Para mi" ya queda seleccionado.

## Login

- Botón de submit: `button.ptur-buttonLogin` (no es `type="submit"`)
- Hay un botón "ojo" (`ptur-loginBox-show-hideBtn`) antes del botón de login — no clickear ese
- Se usa `wait_for_selector('[name="nro_documento"]', state="detached")` para detectar login exitoso

## Archivos

| Archivo | Rol |
|---|---|
| `monitor.py` | Orquestador principal: login, scraping, notificaciones, estado |
| `state.py` | Deduplicación: `make_slot_key`, `should_notify`, `increment` |
| `notify.py` | Email (Gmail SMTP SSL 465) y Telegram |
| `config.yaml` | Especialidades, destinatarios, límite de notificaciones |
| `last_seen.json` | Estado persistente commiteado al repo |
| `configurar.html` | Panel web (GitHub Pages) para editar config sin tocar código |
| `probar_monitor.py` | Test local con navegador visible (no envía mails) |
| `.github/workflows/check-turnos.yml` | Workflow con concurrency guard y permisos de write |

## Configuración

Editar `config.yaml` o usar el panel en GitHub Pages (`configurar.html`):

```yaml
especialidades:
  - endocrinologia          # normalizado sin tildes, minúsculas
notificaciones:
  max_por_turno_por_dia: 6  # cuántas veces notificar el mismo slot por día
  gmail_sender: fungiabduction@gmail.com
  emails:
    - jonatantesta@msn.com
  telegram_chat_ids:
    - "CHAT_ID"
```

## Secrets en GitHub

| Secret | Valor |
|---|---|
| `PORTAL_DNI` | DNI del afiliado |
| `PORTAL_PASSWORD` | Contraseña del portal |
| `GMAIL_APP_PASSWORD` | App Password de Gmail (no la contraseña normal) |
| `TELEGRAM_BOT_TOKEN` | Token del bot (opcional) |

## Deduplicación

- La key de un slot es `{especialidad}|{medico}|{fecha}|{hora}` (minúsculas, `|` como separador)
- El estado se reinicia automáticamente al día siguiente (las keys incluyen la fecha del día)
- Si el mismo turno sigue disponible en la próxima corrida, se notifica de nuevo hasta `max_por_turno_por_dia` veces

## Headless en CI

Se necesitan estos flags en el launch de Chromium para evitar detección:
- `--disable-blink-features=AutomationControlled`
- `--no-sandbox`, `--disable-setuid-sandbox`
- User agent: Chrome real de Windows
- `navigator.webdriver` sobreescrito a `undefined` via `add_init_script`

## Probar localmente

```bat
INSTALAR_Y_PROBAR.bat   # instala deps y corre probar_monitor.py (navegador visible)
```

Requiere tener `PORTAL_DNI` y `PORTAL_PASSWORD` como variables de entorno o seteados en el .bat.
