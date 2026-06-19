from unittest.mock import patch, MagicMock
import notify

CONFIG = {
    "notificaciones": {
        "gmail_sender": "sender@gmail.com",
        "emails": ["a@example.com", "b@example.com"],
        "telegram_chat_ids": ["111", "222"],
    }
}

TURNO = {
    "especialidad": "endocrinologia",
    "medico": "Dra. López",
    "fecha": "2026-06-25",
    "hora": "10:30",
}


def test_send_email_conecta_smtp_ssl():
    with patch("notify.smtplib.SMTP_SSL") as mock_ssl:
        ctx = MagicMock()
        mock_ssl.return_value.__enter__ = lambda s: ctx
        mock_ssl.return_value.__exit__ = MagicMock(return_value=False)
        notify.send_email(
            recipients=["a@example.com"],
            subject="test",
            body="cuerpo",
            sender="sender@gmail.com",
            gmail_app_password="fake_pass",
        )
        mock_ssl.assert_called_once_with("smtp.gmail.com", 465)
        ctx.login.assert_called_once_with("sender@gmail.com", "fake_pass")


def test_send_telegram_envia_a_cada_chat_id():
    with patch("notify.requests.post") as mock_post:
        notify.send_telegram(
            chat_ids=["111", "222"],
            message="hola",
            bot_token="token123",
        )
        assert mock_post.call_count == 2
        chat_ids_sent = [c.kwargs["json"]["chat_id"] for c in mock_post.call_args_list]
        assert "111" in chat_ids_sent
        assert "222" in chat_ids_sent


def test_notify_turno_llama_email_y_telegram():
    with patch("notify.send_email") as mock_email, \
         patch("notify.send_telegram") as mock_tg:
        notify.notify_turno(TURNO, CONFIG, "gmail_pass", "tg_token")
        mock_email.assert_called_once()
        mock_tg.assert_called_once()


def test_notify_turno_sin_emails_no_envia_email():
    config_sin_emails = {
        "notificaciones": {
            "gmail_sender": "sender@gmail.com",
            "emails": [],
            "telegram_chat_ids": ["111"],
        }
    }
    with patch("notify.send_email") as mock_email, \
         patch("notify.send_telegram") as mock_tg:
        notify.notify_turno(TURNO, config_sin_emails, "gmail_pass", "tg_token")
        mock_email.assert_not_called()
        mock_tg.assert_called_once()
