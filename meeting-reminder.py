#!/usr/bin/env python3
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

def send_meeting_reminder():
    if not all([SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL]):
        print("❌ Faltan variables de entorno")
        return False
    
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = "🔔 REUNIÓN EN 10 MINUTOS"
        message["From"] = SENDER_EMAIL
        message["To"] = RECIPIENT_EMAIL
        
        html = """
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial; text-align: center; padding: 40px;">
            <h1 style="color: #FF6B6B; font-size: 48px;">🔔 REUNIÓN EN 10 MINUTOS</h1>
            <p style="font-size: 24px; color: #333;">Hora: {}</p>
            <p style="color: #999;">No olvides prepararte</p>
        </body>
        </html>
        """.format(datetime.now().strftime('%H:%M'))
        
        message.attach(MIMEText(html, "html", "utf-8"))
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, message.as_string())
        
        print("✅ Email de reunión enviado")
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    send_meeting_reminder()
