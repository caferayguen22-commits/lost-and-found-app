import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def _send_email(to_email, subject, body):
    """Verschickt eine einzelne E-Mail. Gibt True/False zurück, wirft nie."""
    if not to_email:
        return False
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("[WARNUNG] Gmail-Zugangsdaten fehlen (.env), E-Mail wird nicht versendet.")
        return False

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


def send_match_notification(to_email, item_title, tracking_code, match_probability):
    """Verschickt eine Match-Benachrichtigung (KI-Matching zweier Meldungen)."""
    subject = "🎉 Möglicher Match für deine Meldung gefunden!"
    body = (
        f"Hallo,\n\n"
        f"gute Nachrichten! Für deine Meldung \"{item_title}\" (Wartemarke: {tracking_code}) "
        f"wurde ein möglicher Match gefunden (Wahrscheinlichkeit: {match_probability}%).\n\n"
        f"Status hier abrufen: http://127.0.0.1:5003/status/{tracking_code}\n\n"
        f"Viele Grüße\nDein Lost & Found Berlin Team"
    )
    return _send_email(to_email, subject, body)


def send_claim_verified_notification(to_email, item_title, tracking_code, claimant_email):
    """
    Verschickt eine Benachrichtigung an den FINDER, wenn jemand auf /durchsuchen
    das geheime Merkmal seines Fundes korrekt genannt hat. Der Finder entscheidet
    selbst, ob und wie er reagiert -- keine automatische Gegenseitig-Freigabe.
    """
    subject = "🕵️ Jemand hat das geheime Merkmal deines Fundes erkannt!"
    body = (
        f"Hallo,\n\n"
        f"für deine Fundmeldung \"{item_title}\" (Wartemarke: {tracking_code}) hat jemand "
        f"das von dir hinterlegte geheime Merkmal korrekt genannt -- das spricht stark dafür, "
        f"dass diese Person die echte Eigentümerin bzw. der echte Eigentümer ist.\n\n"
        f"Kontaktadresse: {claimant_email}\n\n"
        f"Du entscheidest natürlich selbst, ob und wie du dich meldest.\n\n"
        f"Viele Grüße\nDein Lost & Found Berlin Team"
    )
    return _send_email(to_email, subject, body)
