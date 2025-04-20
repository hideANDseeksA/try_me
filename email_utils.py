import logging
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from config import SMTP_CONFIG

async def send_email(to_email: str, subject: str, text_body: str, html_body: str):
    message = MIMEMultipart()
    message["From"] = formataddr(("Easy Docs", SMTP_CONFIG["sender_email"]))
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            message.as_string(),
            sender=SMTP_CONFIG["sender_email"],
            recipients=[to_email],
            hostname=SMTP_CONFIG["server"],
            port=SMTP_CONFIG["port"],
            username=SMTP_CONFIG["username"],
            password=SMTP_CONFIG["password"],
            use_tls=False,
            start_tls=True,
        )
        logging.info(f"✅ Email sent to {to_email}")
    except Exception as e:
        logging.error(f"❌ Email sending failed: {e}")
