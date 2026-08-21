import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def send_match_notification(to_email, item_title, tracking_code, match_probability):
    """Verschickt eine Match-Benachrichtigung. Gibt True/False zurück, wirft nie."""
    if not to_email:
        return False
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("[WARNUNG] Gmail-Zugangsdaten fehlen (.env), E-Mail wird nicht versendet.")
        return False

    subject = "🎉 Möglicher Match für deine Meldung gefunden!"
    body = (
        f"Hallo,\n\n"
        f"gute Nachrichten! Für deine Meldung \"{item_title}\" (Wartemarke: {tracking_code}) "
        f"wurde ein möglicher Match gefunden (Wahrscheinlichkeit: {match_probability}%).\n\n"
        f"Status hier abrufen: http://127.0.0.1:5003/status/{tracking_code}\n\n"
        f"Viele Grüße\nDein Lost & Found Berlin Team"
    )

    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[WARNUNG] E-Mail konnte nicht gesendet werden: {e}")
        return False