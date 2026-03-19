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
    "essentiel": "Essentiel",
    "entretien": "Entretien",
    "complete": "Complète",
    "incineration": "Incinération",
}

FORMULA_PRICES = {
    "essentiel": 35,
    "entretien": 45,
    "complete": 70,
    "incineration": 15,
}

PARTICULARITY_LABELS = {
    "fleurs": "Présence de fleurs",
    "statues": "Statues",
    "ornements": "Ornements",
    "objets_fragiles": "Objets fragiles",
    "pierres_delicates": "Pierres délicates",
}

FOOTER_HTML = """
<div style="background:#2d2926;padding:28px 32px;text-align:center;">
  <p style="color:white;font-size:13px;font-weight:600;margin:0 0 8px;">Contactez-nous directement</p>
  <p style="color:rgba(255,255,255,0.75);font-size:12px;margin:0 0 3px;">📞 07 68 29 53 49</p>
  <p style="color:rgba(255,255,255,0.75);font-size:12px;margin:0 0 12px;">✉️ contact@pnt-soinsdestombes.fr</p>
  <table style="width:100%;max-width:440px;margin:0 auto 12px;font-size:11px;color:rgba(255,255,255,0.6);">
    <tr>
      <td style="padding:3px 6px;text-align:center;">Paul<br/><a href="mailto:paul@pnt-soinsdestombes.fr" style="color:rgba(255,255,255,0.5);text-decoration:none;">paul@pnt-soinsdestombes.fr</a></td>
      <td style="padding:3px 6px;text-align:center;">Tom<br/><a href="mailto:tom@pnt-soinsdestombes.fr" style="color:rgba(255,255,255,0.5);text-decoration:none;">tom@pnt-soinsdestombes.fr</a></td>
      <td style="padding:3px 6px;text-align:center;">Nélio<br/><a href="mailto:nelio@pnt-soinsdestombes.fr" style="color:rgba(255,255,255,0.5);text-decoration:none;">nelio@pnt-soinsdestombes.fr</a></td>
    </tr>
  </table>
  <p style="color:rgba(255,255,255,0.35);font-size:10px;margin:0;">
    PNT – Soins des Tombes · Dijon & alentours · Côte-d'Or (21)<br/>
    Interventions les mercredis et vendredis · 13h30 – 18h00
  </p>
</div>
"""

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
        f'<li style="margin-bottom:4px;">{PARTICULARITY_LABELS.get(p, p)}</li>' for p in parts
    ) if parts else "<li>Aucune</li>"

    photos_html = ""
    photo_urls = data.get("photo_urls") or []
    if photo_urls:
        for i, url in enumerate(photo_urls):
            photos_html += f'<a href="{url}" style="display:inline-block;margin:4px;padding:8px 14px;background:#f5f0e8;border-radius:8px;font-size:13px;color:#4a7c59;text-decoration:none;border:1px solid #e8e4de;">📷 Photo {i+1}</a>'

    # Calcul du prix — toujours recalculé côté serveur pour fiabilité
    search_fee = int(data.get("search_fee", 0) or 0)
    base_price = int(data.get("price") or FORMULA_PRICES.get(data.get("formula", ""), 0))
    total = base_price + search_fee

    plot_loc = data.get('plot_location', '') or ''
    tomb_num = data.get('tomb_number', '') or ''
    location_unknown = plot_loc in ('', 'RECHERCHE_NECESSAIRE')
    tomb_unknown = tomb_num in ('', 'RECHERCHE_NECESSAIRE')

    emplacement_cell = "<span style='color:#c4a35a;font-weight:600;'>Inconnu — recherche incluse (+5€)</span>" if location_unknown else plot_loc
    tomb_cell = "<span style='color:#c4a35a;font-weight:600;'>Inconnu — recherche incluse (+5€)</span>" if tomb_unknown else tomb_num
    search_row = f'<tr><td style="padding:7px 0;color:#7a7267;border-bottom:1px solid #e8e4de;">Recherche d'emplacement</td><td style="padding:7px 0;font-weight:600;color:#c4a35a;border-bottom:1px solid #e8e4de;">+{search_fee}€</td></tr>' if search_fee else ""

    formula_label = FORMULA_LABELS.get(data.get('formula', ''), data.get('formula', ''))
    formula_price_label = f"{base_price}€"

    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"/></head>
<body style="font-family:'Helvetica Neue',Arial,sans-serif;background:#f5f0e8;margin:0;padding:0;">
<div style="max-width:620px;margin:40px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.10);">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#4a7c59,#3d6a4a);padding:40px 32px;text-align:center;">
    <img src="https://media.base44.com/images/public/69b31e939eb62bc729748196/021f5cd7f_image.png" alt="PNT Logo" width="72" height="72" style="border-radius:50%;object-fit:cover;margin-bottom:16px;display:block;margin-left:auto;margin-right:auto;border:3px solid rgba(255,255,255,0.3);" />
    <h1 style="color:white;margin:0;font-size:22px;font-weight:300;letter-spacing:1px;">Demande de devis reçue ✅</h1>
    <p style="color:rgba(255,255,255,0.75);margin:8px 0 0;font-size:13px;">PNT – Soins des tombes · Dijon & alentours</p>
  </div>

  <!-- Body -->
  <div style="padding:32px 36px;">
    <p style="color:#5a5752;font-size:15px;line-height:1.7;margin:0 0 8px;">Bonjour <strong>{data.get('first_name', '')} {data.get('last_name', '')}</strong>,</p>
    <p style="color:#7a7267;font-size:14px;line-height:1.8;margin:0 0 24px;">
      Nous avons bien reçu votre demande de devis. Vous trouverez ci-dessous le récapitulatif complet de votre demande.
    </p>

    <!-- === DEVIS === -->
    <div style="background:#f9f6f0;border-radius:14px;padding:24px 28px;margin-bottom:24px;border:1px solid #e8e4de;">
      
      <!-- Numéro de devis fictif -->
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;padding-bottom:14px;border-bottom:2px solid #e8e4de;">
        <div>
          <p style="margin:0;font-size:18px;font-weight:700;color:#2d2926;">Devis estimatif</p>
          <p style="margin:4px 0 0;font-size:11px;color:#9e9b96;text-transform:uppercase;letter-spacing:1px;">PNT – Soins des tombes</p>
        </div>
        <div style="text-align:right;">
          <p style="margin:0;font-size:22px;font-weight:800;color:#4a7c59;">{total}€</p>
          <p style="margin:2px 0 0;font-size:11px;color:#9e9b96;">Total estimé TTC</p>
        </div>
      </div>

      <!-- Infos client -->
      <h3 style="color:#4a7c59;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;margin:0 0 10px;">Vos informations</h3>
      <table style="width:100%;font-size:13px;margin-bottom:18px;border-collapse:collapse;">
        <tr><td style="padding:6px 0;color:#9e9b96;width:170px;border-bottom:1px solid #f0ece6;">Nom / Prénom</td><td style="padding:6px 0;font-weight:600;color:#2d2926;border-bottom:1px solid #f0ece6;">{data.get('first_name','')} {data.get('last_name','')}</td></tr>
        <tr><td style="padding:6px 0;color:#9e9b96;border-bottom:1px solid #f0ece6;">Téléphone</td><td style="padding:6px 0;color:#2d2926;border-bottom:1px solid #f0ece6;">{data.get('phone','')}</td></tr>
        <tr><td style="padding:6px 0;color:#9e9b96;border-bottom:1px solid #f0ece6;">Email</td><td style="padding:6px 0;color:#2d2926;border-bottom:1px solid #f0ece6;">{data.get('email','')}</td></tr>
        <tr><td style="padding:6px 0;color:#9e9b96;">Ville</td><td style="padding:6px 0;color:#2d2926;">{data.get('postal_code','')} {data.get('city','')}</td></tr>
      </table>

      <!-- Sépulture -->
      <h3 style="color:#4a7c59;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;margin:0 0 10px;">Sépulture</h3>
      <table style="width:100%;font-size:13px;margin-bottom:18px;border-collapse:collapse;">
        <tr><td style="padding:6px 0;color:#9e9b96;width:170px;border-bottom:1px solid #f0ece6;">Personne inhumée</td><td style="padding:6px 0;font-weight:600;color:#2d2926;border-bottom:1px solid #f0ece6;">{data.get('deceased_name','')}</td></tr>
        <tr><td style="padding:6px 0;color:#9e9b96;border-bottom:1px solid #f0ece6;">Cimetière</td><td style="padding:6px 0;font-weight:600;color:#2d2926;border-bottom:1px solid #f0ece6;">{CEMETERY_LABELS.get(data.get('cemetery',''), data.get('cemetery',''))}</td></tr>
        <tr><td style="padding:6px 0;color:#9e9b96;border-bottom:1px solid #f0ece6;">Emplacement</td><td style="padding:6px 0;border-bottom:1px solid #f0ece6;">{emplacement_cell}</td></tr>
        <tr><td style="padding:6px 0;color:#9e9b96;">N° tombe</td><td style="padding:6px 0;">{tomb_cell}</td></tr>
      </table>

      <!-- Particularités -->
      <h3 style="color:#4a7c59;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;margin:0 0 8px;">Particularités</h3>
      <ul style="margin:0 0 18px;padding-left:18px;font-size:13px;color:#5a5752;">{parts_html}</ul>

      <!-- Prestation & prix -->
      <h3 style="color:#4a7c59;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;margin:0 0 10px;">Prestation</h3>
      <table style="width:100%;font-size:13px;border-collapse:collapse;">
        <tr><td style="padding:7px 0;color:#9e9b96;border-bottom:1px solid #e8e4de;width:170px;">Formule</td><td style="padding:7px 0;font-weight:600;color:#2d2926;border-bottom:1px solid #e8e4de;">{formula_label}</td></tr>
        <tr><td style="padding:7px 0;color:#9e9b96;border-bottom:1px solid #e8e4de;">Prix de la formule</td><td style="padding:7px 0;font-weight:600;color:#2d2926;border-bottom:1px solid #e8e4de;">{formula_price_label}</td></tr>
        <tr><td style="padding:7px 0;color:#9e9b96;border-bottom:1px solid #e8e4de;">Mois souhaité</td><td style="padding:7px 0;font-weight:600;color:#2d2926;border-bottom:1px solid #e8e4de;">{data.get('reservation_date','Non renseigné')}</td></tr>
        {search_row}
        <tr style="background:#edf7f1;border-radius:8px;">
          <td style="padding:10px 8px;font-weight:700;font-size:15px;color:#2d2926;border-radius:6px 0 0 6px;">TOTAL ESTIMÉ</td>
          <td style="padding:10px 8px;font-weight:800;font-size:20px;color:#4a7c59;border-radius:0 6px 6px 0;">{total}€</td>
        </tr>
      </table>
    </div>

    {f'<div style="margin:0 0 24px;"><p style="color:#5a5752;font-size:13px;font-weight:600;margin:0 0 8px;">📷 Photos transmises :</p>{photos_html}</div>' if photos_html else ''}

    <!-- Prochaines étapes -->
    <div style="border-left:4px solid #7a9e7e;background:#f0f7f2;padding:18px 20px;border-radius:0 10px 10px 0;margin-bottom:24px;">
      <p style="margin:0 0 6px;font-size:14px;color:#4a7c59;font-weight:700;">Que se passe-t-il maintenant ?</p>
      <ol style="margin:0;padding-left:18px;font-size:13px;color:#5a5752;line-height:1.9;">
        <li>Nous étudions votre demande et préparons votre devis définitif <strong>sous 24–48h</strong>.</li>
        <li>Paul ou Nélio vous appellera pour fixer la date exacte d'intervention (mercredi ou vendredi).</li>
        <li>Le paiement s'effectue <strong>en espèces le jour de l'intervention</strong>. Aucun paiement anticipé.</li>
      </ol>
    </div>

    <div style="background:#fff8e6;border:1px solid #f0d080;border-radius:10px;padding:14px 18px;margin-bottom:24px;">
      <p style="margin:0;font-size:13px;color:#7a6020;">
        📞 <strong>Horaires de contact :</strong> Mercredi & Vendredi, 13h30 – 18h00 · 07 68 29 53 49
      </p>
    </div>

    <p style="color:#7a7267;font-size:14px;line-height:1.7;margin:0;">
      Cordialement,<br/>
      <strong style="color:#5a5752;">L'équipe PNT – Soins des tombes</strong>
    </p>
  </div>

  {FOOTER_HTML}
</div>
</body>
</html>"""

def build_internal_email(data):
    parts = data.get("particularities", [])
    parts_str = ", ".join(PARTICULARITY_LABELS.get(p, p) for p in parts) if parts else "Aucune"

    search_fee = int(data.get("search_fee", 0) or 0)
    base_price = int(data.get("price") or FORMULA_PRICES.get(data.get("formula", ""), 0))
    total = base_price + search_fee

    plot_loc = data.get('plot_location', '') or ''
    tomb_num = data.get('tomb_number', '') or ''
    location_unknown = plot_loc in ('', 'RECHERCHE_NECESSAIRE')
    tomb_unknown = tomb_num in ('', 'RECHERCHE_NECESSAIRE')

    formula_label = FORMULA_LABELS.get(data.get('formula', ''), data.get('formula', ''))

    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"/></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px;">
<div style="max-width:620px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,0.1);">
  <div style="background:#2d2926;padding:24px 28px;">
    <h1 style="color:white;margin:0;font-size:18px;">🔔 Nouvelle demande de devis</h1>
    <p style="color:rgba(255,255,255,0.6);margin:4px 0 0;font-size:13px;">PNT – Panel Admin · Total estimé : <strong style="color:#7a9e7e;">{total}€</strong></p>
  </div>
  <div style="padding:28px;">
    <table style="width:100%;font-size:14px;border-collapse:collapse;">
      <tr style="background:#f5f0e8;"><th colspan="2" style="text-align:left;padding:8px 12px;color:#4a7c59;font-size:11px;text-transform:uppercase;letter-spacing:1px;">Client</th></tr>
      <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;width:180px;">Nom / Prénom</td><td style="padding:8px 12px;font-weight:600;border-bottom:1px solid #f0ece6;">{data.get('first_name','')} {data.get('last_name','')}</td></tr>
      <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Email</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;"><a href="mailto:{data.get('email','')}">{data.get('email','')}</a></td></tr>
      <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Téléphone</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;"><a href="tel:{data.get('phone','')}">{data.get('phone','')}</a></td></tr>
      <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Adresse</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;">{data.get('address','')} {data.get('postal_code','')} {data.get('city','')}</td></tr>

      <tr style="background:#f5f0e8;"><th colspan="2" style="text-align:left;padding:8px 12px;color:#4a7c59;font-size:11px;text-transform:uppercase;letter-spacing:1px;">Sépulture</th></tr>
      <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Défunt</td><td style="padding:8px 12px;font-weight:600;border-bottom:1px solid #f0ece6;">{data.get('deceased_name','')}</td></tr>
      <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Cimetière</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;">{CEMETERY_LABELS.get(data.get('cemetery',''), data.get('cemetery',''))}</td></tr>
      <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Emplacement</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;font-weight:600;color:{'#c4a35a' if location_unknown else '#2d2926'};">{"⚠️ INCONNU – à rechercher (+5€)" if location_unknown else plot_loc}</td></tr>
      <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">N° tombe</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;font-weight:600;color:{'#c4a35a' if tomb_unknown else '#2d2926'};">{"⚠️ INCONNU – à rechercher (+5€)" if tomb_unknown else tomb_num}</td></tr>
      <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Particularités</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;">{parts_str}</td></tr>

      <tr style="background:#f5f0e8;"><th colspan="2" style="text-align:left;padding:8px 12px;color:#4a7c59;font-size:11px;text-transform:uppercase;letter-spacing:1px;">Prestation & Tarif</th></tr>
      <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Formule</td><td style="padding:8px 12px;font-weight:600;border-bottom:1px solid #f0ece6;">{formula_label} ({base_price}€)</td></tr>
      <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Mois souhaité</td><td style="padding:8px 12px;font-weight:600;border-bottom:1px solid #f0ece6;">{data.get('reservation_date','Non renseigné')}</td></tr>
      <tr><td style="padding:8px 12px;color:#7a7267;border-bottom:1px solid #f0ece6;">Frais recherche</td><td style="padding:8px 12px;border-bottom:1px solid #f0ece6;color:{'#c4a35a' if search_fee else '#9e9b96'};font-weight:{'600' if search_fee else '400'};">{f'+{search_fee}€' if search_fee else '—'}</td></tr>
      <tr style="background:#e8f5ee;">
        <td style="padding:12px;font-weight:700;font-size:16px;">TOTAL</td>
        <td style="padding:12px;font-weight:800;font-size:20px;color:#4a7c59;">{total}€</td>
      </tr>
    </table>
  </div>
  {FOOTER_HTML}
</div>
</body>
</html>"""

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
    async_send(send_email_resend, to, "✅ Votre devis – PNT Soins des tombes", html)
    logger.info(f"[API] Thread email client lancé pour {to}")
    return jsonify({"status": "sent"}), 200

@app.route("/api/send-internal-email", methods=["OPTIONS", "POST"])
def send_internal_email():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    data = request.json or {}
    html = build_internal_email(data)
    name = f"{data.get('first_name','')} {data.get('last_name','')}".strip() or "Inconnu"
    search_fee = int(data.get("search_fee", 0) or 0)
    base_price = int(data.get("price") or FORMULA_PRICES.get(data.get("formula", ""), 0))
    total = base_price + search_fee
    logger.info(f"[API] /send-internal-email reçu | client: {name} | total: {total}€ | destinataire interne: {INTERNAL_EMAIL}")
    async_send(send_email_resend, INTERNAL_EMAIL, f"🔔 Nouvelle demande – {name} – {total}€", html)
    return jsonify({"status": "sent"}), 200

@app.route("/api/send-mailing", methods=["OPTIONS", "POST"])
def send_mailing():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    data = request.json or {}
    to = data.get("to", "")
    subject = data.get("subject", "Message de PNT – Soins des tombes")
    html = data.get("html", "")
    if not to or not html:
        return jsonify({"error": "Destinataire ou contenu manquant"}), 400
    logger.info(f"[API] /send-mailing | to: {to} | sujet: {subject}")
    async_send(send_email_resend, to, subject, html)
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
    async_send(send_email_resend, to, "Code de vérification – PNT", html)
    return jsonify({"status": "sent"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
