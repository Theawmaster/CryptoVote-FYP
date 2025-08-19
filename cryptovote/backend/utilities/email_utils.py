# utilities/email_utils.py
import os, smtplib, ssl
from email.message import EmailMessage

def send_email(subject: str, body: str,
               to: str | None = None,
               sender: str | None = None) -> bool:
    host = os.getenv("ALERT_SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("ALERT_SMTP_PORT", "587"))
    user = os.getenv("ALERT_SMTP_USER")
    pwd  = os.getenv("ALERT_SMTP_PASS")
    sender = sender or os.getenv("ALERT_FROM", user or "noreply.ntuvote@gmail.com")
    to     = to     or os.getenv("ALERT_TO",   "noreply.ntuvote@gmail.com")

    if not (user and pwd):
        print("⚠️ Email not sent: SMTP creds missing")
        return False

    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = sender, to, subject
    msg.set_content(body)

    ctx = ssl.create_default_context()
    with smtplib.SMTP(host, port) as s:
        s.starttls(context=ctx)
        s.login(user, pwd)
        s.send_message(msg)
    return True
