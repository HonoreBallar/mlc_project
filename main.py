import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from twilio.rest import Client
from dotenv import load_dotenv


# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Instancier l'application FastAPI
app = FastAPI()

# Configuration Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# Remplacer 'chemin/vers/votre/credentials.json' par le chemin réel
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_CREDENTIALS_PATH")
SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# Configuration Twilio (WhatsApp)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TO_PHONE_NUMBER = os.getenv("TO_PHONE_NUMBER")

# Configuration Email
# SENDER_EMAIL = os.getenv("SENDER_EMAIL")
# SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
# RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

MAILTRAP_HOST = os.getenv("EMAIL_HOST")
MAILTRAP_PORT = os.getenv("EMAIL_PORT")
MAILTRAP_USERNAME = os.getenv("EMAIL_HOST_USER")
MAILTRAP_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

# Modèle Pydantic pour la validation des données
class ContactForm(BaseModel):
    nom: str
    email: str
    telephone: str

def get_google_sheets_service():
    """Crée et retourne le service Google Sheets API."""
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        return service
    except Exception as e:
        print(f"Erreur lors de la connexion à Google Sheets : {e}")
        return None

def send_whatsapp_message(to_number, body):
    """Envoie un message WhatsApp via Twilio."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            from_=f'whatsapp:{TWILIO_PHONE_NUMBER}',
            body=body,
            to=f'whatsapp:{to_number}'
        )
        print(f"Message WhatsApp envoyé avec SID : {message.sid}")
        return message.sid
    except Exception as e:
        print(f"Erreur lors de l'envoi du message WhatsApp : {e}")
        return None

def send_email(subject, body, to_email):
    """Envoie un e-mail via SMTP."""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(MAILTRAP_HOST, MAILTRAP_PORT) as smtp:
            smtp.starttls() # Utilisez TLS pour sécuriser la connexion
            smtp.login(MAILTRAP_USERNAME, MAILTRAP_PASSWORD)
            smtp.send_message(msg)
        
        # with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        #     smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        #     smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail : {e}")
        return False

@app.post("/prospect")
async def submit_form(contact_form: ContactForm):
    # 1. Enregistrement dans Google Sheets
    service = get_google_sheets_service()
    if not service:
        raise HTTPException(status_code=500, detail="Erreur de connexion à Google Sheets")

    sheet = service.spreadsheets()
    values = [[contact_form.nom, contact_form.email, contact_form.telephone]]
    body = {'values': values}

    try:
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="A2", # Ajoute les données à partir de la première cellule disponible
            valueInputOption="RAW",
            body=body
        ).execute()
        print(f"Données ajoutées à Google Sheets : {result}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement dans Google Sheets: {e}")

    # 2. Envoi de l'e-mail
    HTML_EMAIL_TEMPLATE = f"""<!DOCTYPE html>
        <html lang="fr">
        <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
        <title>Bienvenue chez MLC</title>
        <style>
        @media only screen and (max-width:600px) {{
            .container {{ width:100% !important; }}
            .stack-column, .stack-cell {{ display:block !important; width:100% !important; max-width:100% !important; }}
            .greeting {{ font-size:1.25rem !important; }}
            .logo-img {{ height:44px !important; }}
            .feature-img {{ width:40px !important; height:auto !important; }}
            .cta-button {{ padding:12px 20px !important; font-size:16px !important; }}
        }}
        </style>
        </head>
        <body style="margin:0;padding:0;background-color:#f8f9fa;font-family:Arial, Helvetica, sans-serif;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f8f9fa;">
        <tr>
            <td align="center" style="padding:20px;">
            <table role="presentation" class="container" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.06);">
                <tr>
                <td style="background:linear-gradient(135deg,#2563eb 0%,#1d4ed8 100%);padding:22px 20px;text-align:left;">
                    <table role="presentation" width="100%">
                    <tr>
                        <td>
                        <a href="https://mlc.health" target="_blank" style="text-decoration:none;display:inline-block;">
                            <img src="https://mlc.health/img/logo.png" alt="MLC" class="logo-img" width="60" height="60" style="display:block;max-width:100%;width:60px;height:60px;border-radius:50%;background-color:#ffffff;padding:6px;box-shadow:0 0 5px rgba(0,0,0,0.1);border:0;outline:0;">
                        </a>
                        </td>
                        <td style="text-align:right;color:#e8f0ff;font-size:14px;">
                        <div style="font-weight:600">Programme de Santé Globale</div>
                        </td>
                    </tr>
                    </table>
                </td>
                </tr>

                <tr>
                <td style="padding:34px 30px 20px 30px;">
                    <div class="greeting" style="font-size:1.6rem;color:#1f2937;font-weight:600;margin-bottom:14px;">
                    Bonjour <span style="color:#2563eb;font-weight:700;">{contact_form.nom}</span> !
                    </div>

                    <div style="font-size:1.02rem;color:#4b5563;line-height:1.6;margin-bottom:16px;">
                    Bienvenue dans l'aventure <span style="color:#2563eb;font-weight:600;">MLC</span> ! Nous sommes ravis de vous accueillir dans notre programme innovant de santé globale qui aide déjà de nombreuses personnes à transformer leur quotidien.
                    </div>

                    <div style="font-size:1.02rem;color:#4b5563;line-height:1.6;margin-bottom:22px;">
                    Cette <span style="color:#2563eb;font-weight:600;">opportunité unique</span> dans le domaine de la santé et du bien-être va vous permettre d'améliorer durablement votre énergie, votre forme physique et votre équilibre de vie.
                    </div>

                    <table role="presentation" width="100%" style="margin-bottom:18px;">
                    <tr>
                        <td class="stack-cell" valign="top" align="center" style="padding:8px;">
                        <table role="presentation" style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:18px;width:100%;">
                            <tr><td align="center" style="padding-bottom:8px;">
                            <img src="https://cdn-icons-png.flaticon.com/512/1828/1828884.png" alt="Innovation" class="feature-img" width="45" style="display:block;width:45px;height:auto;border:0;outline:0;">
                            </td></tr>
                            <tr><td align="center" style="font-size:0.95rem;font-weight:600;color:#374151;">Innovation</td></tr>
                            <tr><td align="center" style="font-size:0.85rem;color:#6b7280;">Programme révolutionnaire</td></tr>
                        </table>
                        </td>
                        <td class="stack-cell" valign="top" align="center" style="padding:8px;">
                        <table role="presentation" style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:18px;width:100%;">
                            <tr><td align="center" style="padding-bottom:8px;">
                            <img src="https://cdn-icons-png.flaticon.com/512/869/869869.png" alt="Bien-être" class="feature-img" width="45">
                            </td></tr>
                            <tr><td align="center" style="font-size:0.95rem;font-weight:600;color:#374151;">Bien-être</td></tr>
                            <tr><td align="center" style="font-size:0.85rem;color:#6b7280;">Transformation durable</td></tr>
                        </table>
                        </td>
                        <td class="stack-cell" valign="top" align="center" style="padding:8px;">
                        <table role="presentation" style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:18px;width:100%;">
                            <tr><td align="center" style="padding-bottom:8px;">
                            <img src="https://cdn-icons-png.flaticon.com/512/1256/1256650.png" alt="Communauté" class="feature-img" width="45">
                            </td></tr>
                            <tr><td align="center" style="font-size:0.95rem;font-weight:600;color:#374151;">Communauté</td></tr>
                            <tr><td align="center" style="font-size:0.85rem;color:#6b7280;">Accompagnement expert</td></tr>
                        </table>
                        </td>
                    </tr>
                    </table>

                    <div style="background:#f0f9ff;border-left:4px solid #2563eb;padding:14px 18px;margin-bottom:22px;font-size:1rem;color:#374151;line-height:1.6;">
                    <strong>Voici les étapes à suivre :</strong><br>
                    <strong>ÉTAPE 1 :</strong> Inscrivez-vous sur la plateforme officielle MLC en cliquant 👉 <a href="https://mlc.health/fr/fsd865" target="_blank" style="color:#2563eb;font-weight:600;">ici</a><br>
                    <strong>ÉTAPE 2 :</strong> Rejoignez le groupe WhatsApp en cliquant 👉 <a href="https://chat.whatsapp.com/CuYWhHMHkin9PjwO4t2JMM?mode=ac_t" target="_blank" style="color:#2563eb;font-weight:600;">ici</a>
                    </div>
                </td>
                </tr>

                <tr>
                <td style="background-color:#f8fafc;padding:18px 24px 24px 24px;text-align:center;border-top:1px solid #e5e7eb;color:#6b7280;font-size:0.95rem;">
                    <div style="font-weight:700;color:#374151;margin-bottom:6px;">Votre parcours vers un mieux-être optimal commence ici !</div>
                    <div style="font-size:0.85rem;color:#9ca3af;">MLC Health • noeliagui.mlc@gmail.com</div>
                </td>
                </tr>
            </table>
            </td>
        </tr>
        </table>
        </body>
        </html>
        """
    send_email("Bienvenue au programme MLC", HTML_EMAIL_TEMPLATE, contact_form.email)

    # 3. Envoi du message WhatsApp
    whatsapp_body = f"""
        Salut {contact_form.nom} ! :salut_main::scintillements:
        Tu veux en savoir plus sur notre programme MLC et découvrir comment il peut transformer ta vie ? :étoile2:
        Voici les étapes à suivre :
        ETAPE 1 : Inscris-toi sur la plateforme officielle MLC ici :index_vers_la_droite: https://mlc.health/fr/fsd865
        ETAPE 2 : Rejoins le groupe WhatsApp ici :index_vers_la_droite: https://chat.whatsapp.com/CuYWhHMHkin9PjwO4t2JMM?mode=ac_t
        Avec MLC, c’est une transformation garantie et un accompagnement sur mesure :cœur:
    """
    send_whatsapp_message(TO_PHONE_NUMBER, whatsapp_body)
    
    return {"message": "Formulaire soumis avec succès", "data": contact_form}

# Exemple d'exécution : uvicorn main:app --reload