import os
import smtplib
from email.message import EmailMessage

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")  # fallback

def send_verification_email(email, token):
    msg = EmailMessage()
    msg.set_content(f"Click to verify: {BASE_URL}/register/verify-email?token={token}")
    msg['Subject'] = "Voting Registration Token"
    msg['From'] = SMTP_EMAIL
    msg['To'] = email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(SMTP_EMAIL, SMTP_PASSWORD)
            s.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        print(f"[SMTP ERROR] Authentication failed: {e}")
        raise
    except Exception as e:
        print(f"[SMTP ERROR] Could not send email: {e}")
        raise
