import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

def send_email(to, subject, html):

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "from": "PNT Soins des Tombes <onboarding@resend.dev>",
            "to": [to],
            "subject": subject,
            "html": html
        }
    )

    print(response.json())


@app.route("/api/send-client-email", methods=["POST"])
def send_client():

    data = request.json

    html = f"""
    <h2>Confirmation de votre demande</h2>

    Bonjour {data.get("first_name")},

    Nous avons reçu votre demande pour :

    <b>{data.get("deceased_name")}</b>

    Cimetière : {data.get("cemetery")}
    Formule : {data.get("formula")}
    Prix : {data.get("price")} €
    """

    send_email(
        data["email"],
        "Confirmation de votre demande – PNT",
        html
    )

    return jsonify({"status":"sent"})


@app.route("/api/send-internal-email", methods=["POST"])
def send_internal():

    data = request.json

    html = f"""
    <h2>Nouvelle demande client</h2>

    Client : {data.get("first_name")} {data.get("last_name")}

    Email : {data.get("email")}

    Téléphone : {data.get("phone")}

    Défunt : {data.get("deceased_name")}
    """

    send_email(
        "pnt.soins.tombes@gmail.com",
        "Nouvelle demande client",
        html
    )

    return jsonify({"status":"sent"})


@app.route("/")
def home():
    return "API EMAIL OK"


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
