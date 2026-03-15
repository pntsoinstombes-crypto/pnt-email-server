import os
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ==============================
# CONFIGURATION EMAIL
# ==============================

GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")
INTERNAL_EMAIL = os.environ.get("INTERNAL_EMAIL", GMAIL_USER)

if not GMAIL_USER or not GMAIL_PASSWORD:
    raise Exception("GMAIL_USER et GMAIL_PASSWORD doivent être définis dans les variables d'environnement")

# ==============================
# EMAIL SMTP
# ==============================

def send_email_smtp(to, subject, html_body):

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"PNT – Soins des tombes <{GMAIL_USER}>"
    msg["To"] = to

    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, to, msg.as_string())


def async_send(fn, *args):
    thread = threading.Thread(target=fn, args=args)
    thread.daemon = True
    thread.start()


# ==============================
# EMAIL CLIENT
# ==============================

def build_client_email(data):

    total = data.get("price", 0)

    return f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial;background:#f5f5f5;padding:40px">

<div style="max-width:600px;margin:auto;background:white;border-radius:12px;overflow:hidden">

<div style="background:#4a7c59;color:white;padding:30px;text-align:center">
<h1>PNT – Soins des Tombes</h1>
<p>Confirmation de votre demande</p>
</div>

<div style="padding:30px">

<p>Bonjour <b>{data.get("first_name","")}</b>,</p>

<p>Nous avons bien reçu votre demande de nettoyage de tombe.</p>

<h3>Détails de votre demande</h3>

<table style="width:100%;border-collapse:collapse">

<tr>
<td style="padding:8px;border-bottom:1px solid #eee">Défunt</td>
<td style="padding:8px;border-bottom:1px solid #eee"><b>{data.get("deceased_name","")}</b></td>
</tr>

<tr>
<td style="padding:8px;border-bottom:1px solid #eee">Cimetière</td>
<td style="padding:8px;border-bottom:1px solid #eee">{data.get("cemetery","")}</td>
</tr>

<tr>
<td style="padding:8px;border-bottom:1px solid #eee">Formule</td>
<td style="padding:8px;border-bottom:1px solid #eee">{data.get("formula","")}</td>
</tr>

<tr>
<td style="padding:8px;border-bottom:1px solid #eee">Date souhaitée</td>
<td style="padding:8px;border-bottom:1px solid #eee">{data.get("reservation_date","")}</td>
</tr>

<tr>
<td style="padding:10px;font-size:18px"><b>Total</b></td>
<td style="padding:10px;font-size:18px;color:#4a7c59"><b>{total} €</b></td>
</tr>

</table>

<p style="margin-top:20px">
Notre équipe vous contactera sous <b>24 à 48h</b> pour confirmer l’intervention.
</p>

<p>
Cordialement,<br>
<b>Equipe PNT – Soins des Tombes</b><br>
📞 07 68 29 53 49
</p>

</div>

</div>
</body>
</html>
"""


# ==============================
# EMAIL ADMIN
# ==============================

def build_internal_email(data):

    return f"""
<html>
<body style="font-family:Arial;background:#f5f5f5;padding:40px">

<div style="max-width:600px;margin:auto;background:white;border-radius:12px;padding:30px">

<h2>Nouvelle demande client</h2>

<p><b>Nom :</b> {data.get("first_name")} {data.get("last_name")}</p>
<p><b>Email :</b> {data.get("email")}</p>
<p><b>Téléphone :</b> {data.get("phone")}</p>

<hr>

<p><b>Défunt :</b> {data.get("deceased_name")}</p>
<p><b>Cimetière :</b> {data.get("cemetery")}</p>
<p><b>Formule :</b> {data.get("formula")}</p>
<p><b>Date :</b> {data.get("reservation_date")}</p>

</div>

</body>
</html>
"""


# ==============================
# ROUTES API
# ==============================

@app.route("/api/health")
def health():
    return jsonify({"status":"ok"})


@app.route("/api/send-client-email", methods=["POST"])
def send_client_email():

    data = request.json

    email = data.get("email")

    html = build_client_email(data)

    async_send(
        send_email_smtp,
        email,
        "Confirmation de votre demande – PNT",
        html
    )

    return jsonify({"status":"sent"})


@app.route("/api/send-internal-email", methods=["POST"])
def send_internal_email():

    data = request.json

    html = build_internal_email(data)

    async_send(
        send_email_smtp,
        INTERNAL_EMAIL,
        "Nouvelle demande client",
        html
    )

    return jsonify({"status":"sent"})


# ==============================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
