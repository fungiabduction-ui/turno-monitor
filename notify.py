import smtplib
from email.mime.text import MIMEText
import requests

PORTAL_URL = "https://portal.dim.com.ar/"


def send_email(recipients, subject, body, sender, gmail_app_password):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, gmail_app_password)
        smtp.sendmail(sender, recipients, msg.as_string())


def send_telegram(chat_ids, message, bot_token):
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(
            url,
            json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            timeout=10,
        )
        if not response.ok:
            print(f"[notify] Telegram error for chat_id {chat_id}: {response.status_code} {response.text}")


def notify_turno(turno, config, gmail_app_password, telegram_bot_token):
    especialidad = turno["especialidad"]
    medico = turno.get("medico", "sin especificar")
    fecha = turno["fecha"]
    hora = turno["hora"]

    subject = f"[Turno disponible] {especialidad} — {fecha} {hora}"
    body = (
        f"Turno disponible: {especialidad}\n"
        f"Médico: {medico}\n"
        f"Fecha: {fecha} — {hora}\n\n"
        f"Reservar en: {PORTAL_URL}"
    )
    html_msg = (
        f"<b>[Turno disponible] {especialidad}</b>\n\n"
        f"Médico: {medico}\n"
        f"Fecha: {fecha} — {hora}\n\n"
        f"<a href='{PORTAL_URL}'>Reservar ahora</a>"
    )

    notif = config["notificaciones"]
    emails = notif.get("emails", [])
    chat_ids = notif.get("telegram_chat_ids", [])
    sender = notif.get("gmail_sender") or (emails[0] if emails else None)

    if emails and sender and gmail_app_password:
        try:
            send_email(emails, subject, body, sender, gmail_app_password)
        except Exception as e:
            print(f"[notify] Email error: {e}")

    if chat_ids and telegram_bot_token:
        try:
            send_telegram(chat_ids, html_msg, telegram_bot_token)
        except Exception as e:
            print(f"[notify] Telegram error: {e}")
