#!/usr/bin/env python3
import os
import smtplib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

def fetch_google_news(topic="fintech Panama"):
    """Obtener noticias de Google News usando RSS (sin API key)"""
    try:
        # URL de Google News RSS
        url = f"https://news.google.com/rss/search?q={topic}&hl=es&gl=ES&ceid=ES:es"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parsear XML
        root = ET.fromstring(response.content)
        
        articles = []
        for item in root.findall(".//item")[:8]:
            title_elem = item.find("title")
            desc_elem = item.find("description")
            link_elem = item.find("link")
            
            title = title_elem.text if title_elem is not None else "Sin título"
            desc = desc_elem.text if desc_elem is not None else "Sin descripción"
            link = link_elem.text if link_elem is not None else ""
            
            # Limpiar descripción (Google News incluye HTML)
            if desc:
                desc = desc.replace("<br>", "\n").replace("<b>", "").replace("</b>", "")
                desc = desc[:300]
            
            articles.append({
                "title": title,
                "description": desc,
                "url": link,
                "source": "Google News"
            })
        
        return articles
    
    except Exception as e:
        print(f"Error obteniendo noticias: {e}")
        return []

def generate_briefing_html(articles, topic):
    """Generar briefing usando Claude API"""
    if not articles:
        return "<p>No se encontraron artículos.</p>"
    
    # Preparar texto de artículos
    articles_text = "\n".join([
        f"{i}. {a['title']}\n   {a['description']}"
        for i, a in enumerate(articles, 1)
    ])
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    prompt = f"""Basándote en estos artículos sobre {topic}, genera un BRIEFING EJECUTIVO CORTO en español:

{articles_text}

FORMATO EXACTO:
RESUMEN EJECUTIVO
[2-3 líneas máximo con lo más importante]

PUNTOS CLAVE
• Punto 1
• Punto 2
• Punto 3

LECTURA RECOMENDADA
[Menciona 2-3 artículos específicos por qué leerlos]

Sé conciso y actionable."""
    
    message = client.messages.create(
        model="claude-opus-4-20250805",
        max_tokens=800,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    briefing = message.content[0].text
    
    # Convertir a HTML
    html_briefing = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px;">
            📰 Briefing: {topic}
        </h2>
        <p style="color: #666; font-size: 12px;">
            {datetime.now().strftime('%d de %B de %Y - %H:%M')}
        </p>
        <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; white-space: pre-wrap; font-family: Arial;">
{briefing}
        </pre>
    </div>
    """
    
    return html_briefing

def create_email_html(articles, briefing_html):
    """Crear email HTML con briefing + artículos"""
    articles_html = "".join([
        f"""<tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 12px; vertical-align: top; width: 20px;">
                <strong>{i}.</strong>
            </td>
            <td style="padding: 12px;">
                <strong><a href="{a['url']}" style="color: #1a73e8; text-decoration: none;">
                    {a['title']}
                </a></strong>
                <br/>
                <small style="color: #666;">Fuente: {a['source']}</small>
                <p style="margin: 8px 0; color: #555;">
                    {a['description']}
                </p>
            </td>
        </tr>"""
        for i, a in enumerate(articles, 1)
    ])
    
    full_html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; background: #f9f9f9; }}
            .container {{ max-width: 700px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            h1 {{ color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 10px; margin-top: 0; }}
            .date {{ color: #999; font-size: 12px; margin-bottom: 20px; }}
            .briefing {{ background: #e8f0fe; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #1a73e8; }}
            .briefing pre {{ margin: 0; white-space: pre-wrap; font-size: 13px; line-height: 1.6; color: #333; }}
            table {{ width: 100%; border-collapse: collapse; }}
            a {{ color: #1a73e8; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .footer {{ text-align: center; color: #999; font-size: 11px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📰 Tu Briefing Diario</h1>
            <div class="date">{datetime.now().strftime('%d de %B de %Y a las %H:%M')}</div>
            
            <div class="briefing">
                {briefing_html}
            </div>
            
            <h2 style="color: #333; margin-top: 30px;">Artículos Completos</h2>
            <table>
                {articles_html}
            </table>
            
            <div class="footer">
                <p>Este email fue generado automáticamente por tu sistema de News Briefing.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return full_html

def send_email(html_content, topic):
    """Enviar email usando Gmail SMTP"""
    if not all([SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL]):
        print("❌ Falta configurar variables de entorno en .env")
        print(f"   SENDER_EMAIL: {'✓' if SENDER_EMAIL else '✗'}")
        print(f"   SENDER_PASSWORD: {'✓' if SENDER_PASSWORD else '✗'}")
        print(f"   RECIPIENT_EMAIL: {'✓' if RECIPIENT_EMAIL else '✗'}")
        return False
    
    try:
        # Crear mensaje
        message = MIMEMultipart("alternative")
        message["Subject"] = f"📰 Briefing Diario: {topic} - {datetime.now().strftime('%d/%m/%Y')}"
        message["From"] = SENDER_EMAIL
        message["To"] = RECIPIENT_EMAIL
        
        # Agregar HTML
        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(html_part)
        
        # Conectar a Gmail y enviar
        print("📧 Conectando a Gmail SMTP...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, message.as_string())
        
        print(f"✅ Email enviado exitosamente a {RECIPIENT_EMAIL}")
        return True
    
    except smtplib.SMTPAuthenticationError:
        print("❌ Error de autenticación.")
        print("   Verifica que usas Gmail App Password, NO tu contraseña normal")
        print("   Genera una en: https://myaccount.google.com/apppasswords")
        return False
    
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        return False

def main():
    """Pipeline principal"""
    print("\n" + "="*60)
    print("📧 DAILY NEWS EMAIL (Google News)")
    print("="*60)
    
    # Temas personalizables
    topics = [
        "fintech Panama",
        "AI startups",
        "entrepreneurship Latin America"
    ]
    
    for topic in topics:
        print(f"\n🔍 Obteniendo noticias: {topic}")
        articles = fetch_google_news(topic)
        
        if not articles:
            print(f"⚠️ No se encontraron artículos para: {topic}")
            continue
        
        print(f"✅ {len(articles)} artículos encontrados")
        
        print(f"🤖 Generando briefing con Claude...")
        briefing_html = generate_briefing_html(articles, topic)
        
        print(f"📧 Creando email HTML...")
        email_html = create_email_html(articles, briefing_html)
        
        print(f"✉️ Enviando email...")
        send_email(email_html, topic)
    
    print("\n" + "="*60)
    print("✅ PROCESO COMPLETADO")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
