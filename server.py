import os
import threading
import traceback
import logging
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins="*")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "contact@pnt-soinsdestombes.fr")
INTERNAL_EMAIL = os.environ.get("INTERNAL_EMAIL", "contact@pnt-soinsdestombes.fr")

logger.info(f"=== CONFIG RESEND ===")
logger.info(f"FROM_EMAIL: {FROM_EMAIL}")
logger.info(f"INTERNAL_EMAIL: {INTERNAL_EMAIL}")
logger.info(f"RESEND_API_KEY: {'***' if RESEND_API_KEY else '❌ NON DÉFINI !!!'}")

CEMETERY_LABELS = {
    "fontaine_les_dijon": "Fontaine-lès-Dijon",
    "pejoces_dijon": "Cimetière des Péjoces (Dijon)",
    "talant": "Talant",
}

FORMULA_LABELS = {
    "essentiel": "Essentiel — 35€",
    "entretien": "Entretien — 45€",
    "complete": "Complète — 60€",
}

PARTICULARITY_LABELS = {
    "fleurs": "Présence de fleurs",
    "statues": "Statues",
    "ornements": "Ornements",
    "objets_fragiles": "Objets fragiles",
    "pierres_delicates": "Pierres délicates",
}

def send_email_resend(to, subject, html_body):
    logger.info(f"[RESEND] Tentative envoi vers: {to} | Sujet: {subject}")
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": f"PNT – Soins des tombes <{FROM_EMAIL}>",
                "to": [to],
                "subject": subject,
                "html": html_body,
            },
            timeout=30,
        )
        if response.status_code in (200, 201):
            logger.info(f"[RESEND] ✅ Email envoyé avec succès à {to} | ID: {response.json().get('id')}")
        else:
            logger.error(f"[RESEND] ❌ Erreur {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"[RESEND] ❌ ERREUR INCONNUE: {e}")
        traceback.print_exc()

def build_client_email(data):
    parts = data.get("particularities", [])
    parts_html = "".join(
        f'<li>{PARTICULARITY_LABELS.get(p, p)}</li>' for p in parts
    ) if parts else "<li>Aucune</li>"

    photos_html = ""
    for url in (data.get("photo_urls") or []):
        photos_html += f'<img src="{url}" style="max-width:200px;margin:4px;border-radius:8px;" />'

    search_fee = data.get("search_fee", 0) or 0
    total = (data.get("price") or 0) + search_fee
    search_line = f'<tr><td style="padding:6px 0;color:#7a7267;">Recherche de tombe</td><td style="padding:6px 0;font-weight:600;color:#c4a35a;">+{search_fee}€</td></tr>' if search_fee else ""

    return f"""
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8" /></head>
<body style="font-family:'Helvetica Neue',Arial,sans-serif;background:#f5f0e8;margin:0;padding:0;">
  <div style="max-width:600px;margin:40px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
    
    <!-- Header -->
    <div style="background:linear-gradient(135deg,#4a7c59,#3d6a4a);padding:40px 32px;text-align:center;">
      <div style="width:60px;height:60px;background:rgba(255,255,255,0.2);border-radius:50%;display:inline-flex;align-items:center;justify-content:center;margin-bottom:16px;">
        <span style="color:white;font-size:20px;font-weight:700;">PNT</span>
      </div>
      <h1 style="color:white;margin:0;font-size:24px;font-weight:300;letter-spacing:1px;">Votre demande a bien été reçue</h1>
      <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;font-size:14px;">PNT – Soins des tombes</p>
    </div>

    <!-- Body -->
    <div style="padding:32px;">
      <p style="color:#5a5752;font-size:15px;line-height:1.7;">Bonjour <strong>{data.get('first_name', '')} {data.get('last_name', '')}</strong>,</p>
      <p style="color:#7a7267;font-size:14px;line-height:1.8;">
        Nous avons bien reçu votre demande de devis. Notre équipe va l'étudier et vous recontactera dans les plus brefs délais pour confirmer votre intervention.
      </p>

      <!-- Recap card -->
      <div style="background:#f5f0e8;border-radius:12px;padding:24px;margin:24px 0;">
        <h2 style="color:#5a5752;font-size:16px;font-weight:600;margin:0 0 16px;border-bottom:1px solid #e8e4de;padding-bottom:12px;">Récapitulatif de votre demande</h2>
        
        <h3 style="color:#4a7c59;font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;">Sépulture</h3>
        <table style="width:100%;font-size:14px;margin-bottom:16px;">
          <tr><td style="padding:4px 0;color:#7a7267;width:160px;">Personne inhumée</td><td style="padding:4px 0;font-weight:600;color:#2d2926;">{data.get('deceased_name', '')}</td></tr>
          <tr><td style="padding:4px 0;color:#7a7267;">Cimetière</td><td style="padding:4px 0;font-weight:600;color:#2d2926;">{CEMETERY_LABELS.get(data.get('cemetery',''), data.get('cemetery',''))}</td></tr>
          <tr><td style="padding:4px 0;color:#7a7267;">Emplacement</td><td style="padding:4px 0;color:#2d2926;">{data.get('plot_location','–')}</td></tr>
          <tr><td style="padding:4px 0;color:#7a7267;">N° tombe</td><td style="padding:4px 0;color:#2d2926;">{data.get('tomb_number','–')}</td></tr>
        </table>

        <h3 style="color:#4a7c59;font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin:16px 0 8px;">Prestation</h3>
        <table style="width:100%;font-size:14px;margin-bottom:16px;">
          <tr><td style="padding:6px 0;color:#7a7267;width:160px;">Formule</td><td style="padding:6px 0;font-weight:600;color:#2d2926;">{FORMULA_LABELS.get(data.get('formula',''), data.get('formula',''))}</td></tr>
          <tr><td style="padding:6px 0;color:#7a7267;">Mois souhaité</td><td style="padding:6px 0;font-weight:600;color:#2d2926;">{data.get('reservation_date', 'Non renseigné')}</td></tr>
          {search_line}
          <tr style="border-top:1px solid #e8e4de;">
            <td style="padding:10px 0 4px;color:#2d2926;font-weight:600;font-size:15px;">Total estimé</td>
            <td style="padding:10px 0 4px;font-weight:700;color:#4a7c59;font-size:20px;">{total}€</td>
          </tr>
        </table>

        <h3 style="color:#4a7c59;font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin:16px 0 8px;">Particularités</h3>
        <ul style="margin:0;padding-left:16px;font-size:14px;color:#5a5752;">{parts_html}</ul>
      </div>

      {f'<div style="margin:16px 0;"><h3 style="color:#5a5752;font-size:14px;">Photos transmises :</h3>{photos_html}</div>' if photos_html else ''}

      <!-- Info box -->
      <div style="border-left:4px solid #7a9e7e;background:#f0f7f2;padding:16px 20px;border-radius:0 8px 8px 0;margin:24px 0;">
        <p style="margin:0;font-size:14px;color:#4a7c59;font-weight:600;">Prochaine étape</p>
        <p style="margin:6px 0 0;font-size:13px;color:#5a5752;line-height:1.7;">
          Nous vous contacterons par téléphone ou email sous 24–48h pour confirmer la date exacte de l'intervention (mercredi ou vendredi).
          Le paiement s'effectue en espèces le jour de l'intervention.
        </p>
      </div>

      <p style="color:#7a7267;font-size:14px;line-height:1.7;">
        Cordialement,<br />
        <strong style="color:#5a5752;">L'équipe PNT – Soins des tombes</strong><br />
        <span style="font-size:12px;">📞 07 68 29 53 49 | ✉️ contact@pnt-soinsdestombes.fr</span>
      </p>
    </div>

    <!-- Footer -->
    <div style="background:#5a5752;padding:20px 32px;text-align:center;">
      <p style="color:rgba(255,255,255,0.5);font-size:11px;margin:0;">
        PNT – Soins des Tombes · Dijon & alentours · Côte-d'Or (21)<br />
        Paul & Nélio (Fondateurs) · Tom (Co-fondateur)
      </p>
    </div>
  </div>
</body>
</html>
"""

def build_internal_email(data):
    parts = data.get("particularities", [])
    parts_str = ", ".join(PARTICULARITY_LABELS.get(p, p) for p in parts) if parts else "Aucune"
    search_fee = data.get("search_fee", 0) or 0
    total = (data.get("price") or 0) + search_fee

    return f"""
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8" /></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px;">
  <div style="max-width:600px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,0.1);">
    <div style="background:#2d2926;padding:24px 28px;">
      <h1 style="color:white;margin:0;font-size:18px;">🔔 Nouvelle demande de devis</h1>
      <p style="color:rgba(255,255,255,0.6);margin:4px 0 0;font-size:13px;">PNT – Panel Admin</p>
    </div>
    <div style="padding:28px;">
      <table style="width:100%;font-size:14px;border-collapse:collapse;">
        <tr style="background:#f5f0e8;"><th colspan="2" style="text-align:left;padding:8px 12px;color:#4a7c59;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Client</th></tr>
        <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Nom</td><td style="padding:8px 12px;font-weight:600;border-bottom:1px solid #f0ece6;">{data.get('first_name','')} {data.get('last_name','')}</td></tr>
        <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Email</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;"><a href="mailto:{data.get('email','')}">{data.get('email','')}</a></td></tr>
        <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Téléphone</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;"><a href="tel:{data.get('phone','')}">{data.get('phone','')}</a></td></tr>
        <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Adresse</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;">{data.get('address','')} {data.get('postal_code','')} {data.get('city','')}</td></tr>

        <tr style="background:#f5f0e8;"><th colspan="2" style="text-align:left;padding:8px 12px;color:#4a7c59;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Sépulture</th></tr>
        <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Défunt</td><td style="padding:8px 12px;font-weight:600;border-bottom:1px solid #f0ece6;">{data.get('deceased_name','')}</td></tr>
        <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Cimetière</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;">{CEMETERY_LABELS.get(data.get('cemetery',''), data.get('cemetery',''))}</td></tr>
        <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Emplacement</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;">{data.get('plot_location','–')}</td></tr>
        <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">N° tombe</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;">{data.get('tomb_number','–')}</td></tr>
        <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Particularités</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;">{parts_str}</td></tr>

        <tr style="background:#f5f0e8;"><th colspan="2" style="text-align:left;padding:8px 12px;color:#4a7c59;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Prestation</th></tr>
        <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Formule</td><td style="padding:8px 12px;font-weight:600;border-bottom:1px solid #f0ece6;">{FORMULA_LABELS.get(data.get('formula',''), data.get('formula',''))}</td></tr>
        <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Mois souhaité</td><td style="padding:8px 12px;font-weight:600;border-bottom:1px solid #f0ece6;">{data.get('reservation_date', 'Non renseigné')}</td></tr>
        <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Frais recherche</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;">+{search_fee}€</td></tr>
        <tr style="background:#e8f5ee;"><td style="padding:10px 12px;font-weight:700;font-size:16px;">TOTAL</td><td style="padding:10px 12px;font-weight:700;font-size:18px;color:#4a7c59;">{total}€</td></tr>
      </table>
    </div>
  </div>
</body>
</html>
"""

def async_send(fn, *args):
    t = threading.Thread(target=fn, args=args)
    t.daemon = True
    t.start()

@app.route("/api/health", methods=["HEAD", "GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/api/send-client-email", methods=["OPTIONS", "POST"])
def send_client_email():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    data = request.json or {}
    to = data.get("to") or data.get("email", "")
    logger.info(f"[API] /send-client-email reçu | destinataire: {to}")
    if not to:
        logger.error("[API] ❌ Email manquant dans la requête")
        return jsonify({"error": "Email manquant"}), 400
    html = build_client_email(data)
    async_send(send_email_resend, to, "✅ Votre demande de devis – PNT Soins des tombes", html)
    logger.info(f"[API] Thread email client lancé pour {to}")
    return jsonify({"status": "sent"}), 200

@app.route("/api/send-internal-email", methods=["OPTIONS", "POST"])
def send_internal_email():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    data = request.json or {}
    html = build_internal_email(data)
    name = f"{data.get('first_name','')} {data.get('last_name','')}".strip() or "Inconnu"
    logger.info(f"[API] /send-internal-email reçu | client: {name} | destinataire interne: {INTERNAL_EMAIL}")
    async_send(send_email_resend, INTERNAL_EMAIL, f"🔔 Nouvelle demande – {name}", html)
    logger.info(f"[API] Thread email interne lancé vers {INTERNAL_EMAIL}")
    return jsonify({"status": "sent"}), 200

@app.route("/api/send-verification-code", methods=["OPTIONS", "POST"])
def send_verification_code():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    data = request.json or {}
    to = data.get("to", "")
    code = data.get("code", "")
    name = data.get("full_name", "")
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;background:#f5f0e8;padding:40px;border-radius:16px;">
      <h2 style="color:#4a7c59;">Votre code de vérification</h2>
      <p style="color:#5a5752;">Bonjour {name},</p>
      <div style="background:white;border-radius:12px;padding:24px;text-align:center;margin:20px 0;">
        <span style="font-size:40px;font-weight:700;letter-spacing:8px;color:#2d2926;">{code}</span>
      </div>
      <p style="color:#9e9b96;font-size:12px;">Ce code expire dans 10 minutes. Ne le partagez pas.</p>
    </div>
    """
    async_send(send_email_smtp, to, "🔐 Code de vérification – PNT", html)
    return jsonify({"status": "sent"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
