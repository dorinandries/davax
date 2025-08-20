import smtplib
from email.message import EmailMessage
from .config import settings


def send_otp_email(to_email: str, code: str):
    msg = EmailMessage()
    msg["Subject"] = "Your Smart Librarian verification code"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content(f"Your verification code is: {code}\nIt expires in {settings.otp_ttl//60} minutes.")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_pass)
        server.send_message(msg)