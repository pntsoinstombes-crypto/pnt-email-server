from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Permet les requêtes depuis votre site

# Configuration Gmail
GMAIL_USER = 'pnt.soins.tombes@gmail.com'
GMAIL_APP_PASSWORD = 'cfjc ufog qmfj jnlb'  # Le code de votre capture d'écran

# URLs
SITE_URL = 'https://votre-site-base44.com'  # À remplacer

def send_email(to_email, subject, html_body):
    """Envoie un email via Gmail SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f'PNT – Soins des Tombes <{GMAIL_USER}>'
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Ajouter le corps HTML
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Connexion SMTP Gmail
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Erreur envoi email: {e}")
        return False

@app.route('/api/send-client-email', methods=['POST'])
def send_client_email():
    """Email de confirmation au client"""
    data = request.json
    
    cemetery_names = {
        'fontaine_les_dijon': 'Fontaine-lès-Dijon',
        'pejoces_dijon': 'Cimetière des Péjoces (Dijon)',
        'talant': 'Talant'
    }
    
    formula_names = {
        'essentiel': 'Essentiel — 25€',
        'entretien': 'Entretien — 35€',
        'complete': 'Complète — 50€'
    }
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Jost', Arial, sans-serif; line-height: 1.6; color: #5a5752; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #fdfcf9; }}
            .header {{ background: linear-gradient(135deg, #7a9e7e 0%, #4e7352 100%); padding: 40px 20px; text-align: center; }}
            .logo {{ width: 80px; height: 80px; background: white; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; color: #7a9e7e; }}
            .content {{ padding: 40px 30px; }}
            .section {{ margin: 30px 0; padding: 20px; background: #f5f0e8; border-radius: 12px; }}
            .section-title {{ font-family: 'Cormorant Garamond', serif; font-size: 20px; font-weight: 600; color: #7a9e7e; margin-bottom: 15px; }}
            .info-row {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 8px 0; border-bottom: 1px solid #e8e4de; }}
            .info-label {{ font-weight: 500; color: #9e9b96; }}
            .info-value {{ font-weight: 600; color: #5a5752; }}
            .footer {{ background: #5a5752; color: rgba(255,255,255,0.7); padding: 30px 20px; text-align: center; font-size: 13px; }}
            .footer a {{ color: #a8c5ab; text-decoration: none; }}
            h1 {{ font-family: 'Cormorant Garamond', serif; color: white; font-size: 32px; margin: 0; font-weight: 400; }}
            .emoji {{ font-size: 24px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">PNT</div>
                <h1>🕊️ Confirmation de votre demande</h1>
            </div>
            
            <div class="content">
                <p style="font-size: 16px; margin-bottom: 20px;">
                    Bonjour <strong>{data['client_name']}</strong>,
                </p>
                
                <p style="font-size: 15px; line-height: 1.8;">
                    Nous vous remercions pour votre confiance. Votre demande d'entretien de sépulture a bien été enregistrée.
                </p>
                
                <div class="section">
                    <div class="section-title">📋 Récapitulatif de votre demande</div>
                    <div class="info-row">
                        <span class="info-label">Formule choisie</span>
                        <span class="info-value">{formula_names.get(data['formula'], data['formula'])}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Cimetière</span>
                        <span class="info-value">{cemetery_names.get(data['cemetery'], data['cemetery'])}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Personne inhumée</span>
                        <span class="info-value">{data['deceased_name']}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Date d'intervention</span>
                        <span class="info-value">{data['reservation_date']}</span>
                    </div>
                    <div class="info-row" style="border-bottom: none;">
                        <span class="info-label">Montant</span>
                        <span class="info-value" style="font-size: 20px; color: #7a9e7e;">{data['price']}€</span>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">✅ Prochaines étapes</div>
                    <p style="margin: 0; font-size: 14px; line-height: 1.7;">
                        • Nous vous recontacterons <strong>sous 24h</strong> pour confirmer votre réservation<br>
                        • Le paiement s'effectuera <strong>en espèces le jour de l'intervention</strong><br>
                        • Après notre intervention, vous recevrez <strong>une photo de la sépulture entretenue</strong>
                    </p>
                </div>
                
                <p style="margin-top: 30px; font-size: 14px; color: #9e9b96; font-style: italic;">
                    Chaque sépulture est entretenue avec respect, discrétion et professionnalisme.
                </p>
            </div>
            
            <div class="footer">
                <p style="margin: 0 0 15px;"><strong style="color: white;">PNT – Soins des Tombes</strong></p>
                <p style="margin: 5px 0;">📞 <a href__="tel:0768295349">07 68 29 53 49</a></p>
                <p style="margin: 5px 0;">✉️ <a href__="mailto:pnt.soins.tombes@gmail.com">pnt.soins.tombes@gmail.com</a></p>
                <p style="margin: 5px 0;">🕒 Mercredi & Vendredi : 13h30–18h00</p>
                <p style="margin-top: 20px; font-size: 11px; opacity: 0.6;">
                    Paul · Nélio · Tom – Entrepreneurs locaux, Côte-d'Or (21)
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    success = send_email(
        data['to'],
        '🕊️ Confirmation de votre demande – PNT Soins des Tombes',
        html_body
    )
    
    if success:
        return jsonify({'status': 'success', 'message': 'Email envoyé'})
    else:
        return jsonify({'status': 'error', 'message': 'Erreur envoi'}), 500

@app.route('/api/send-internal-email', methods=['POST'])
def send_internal_email():
    """Email de notification interne"""
    data = request.json
    
    cemetery_names = {
        'fontaine_les_dijon': 'Fontaine-lès-Dijon',
        'pejoces_dijon': 'Cimetière des Péjoces (Dijon)',
        'talant': 'Talant'
    }
    
    formula_names = {
        'essentiel': 'Essentiel — 25€',
        'entretien': 'Entretien — 35€',
        'complete': 'Complète — 50€'
    }
    
    particularities = data.get('particularities', [])
    particularities_text = '<br>'.join([f'• {p.replace("_", " ").title()}' for p in particularities]) if particularities else 'Aucune'
    
    photos_html = ''
    if data.get('photo_urls'):
        photos_html = '<div style="margin-top: 15px;">'
        for i, url in enumerate(data['photo_urls'], 1):
            photos_html += f'<p style="margin: 5px 0;"><a href__="{url}" style="color: #7a9e7e;">📷 Photo {i}</a></p>'
        photos_html += '</div>'
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }}
            .container {{ max-width: 700px; margin: 20px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #7a9e7e 0%, #4e7352 100%); padding: 30px; text-align: center; color: white; }}
            .alert {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px; color: #856404; }}
            .content {{ padding: 30px; }}
            .section {{ margin: 25px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #7a9e7e; }}
            .section-title {{ font-size: 18px; font-weight: bold; color: #7a9e7e; margin-bottom: 15px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
            .info-item {{ padding: 8px 0; }}
            .info-label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
            .info-value {{ font-size: 15px; font-weight: 600; color: #333; }}
            .action-button {{ display: inline-block; background: #7a9e7e; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; font-size: 28px;">🔔 NOUVELLE DEMANDE</h1>
                <p style="margin: 10px 0 0; opacity: 0.9;">Demande reçue le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
            </div>
            
            <div class="alert">
                <strong>⚡ ACTION REQUISE</strong><br>
                Contacter le client pour confirmer la réservation
            </div>
            
            <div class="content">
                <div class="section">
                    <div class="section-title">👤 INFORMATIONS CLIENT</div>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Nom complet</div>
                            <div class="info-value">{data.get('last_name', '')} {data.get('first_name', '')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Téléphone</div>
                            <div class="info-value">📱 {data.get('phone', 'Non renseigné')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Email</div>
                            <div class="info-value">✉️ {data.get('email', 'Non renseigné')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Ville</div>
                            <div class="info-value">{data.get('postal_code', '')} {data.get('city', '')}</div>
                        </div>
                    </div>
                    <div style="margin-top: 10px;">
                        <div class="info-label">Adresse complète</div>
                        <div class="info-value">{data.get('address', 'Non renseignée')}</div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">⚰️ INFORMATIONS SÉPULTURE</div>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Défunt(e)</div>
                            <div class="info-value">{data.get('deceased_name', '')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Cimetière</div>
                            <div class="info-value">🪦 {cemetery_names.get(data.get('cemetery', ''), data.get('cemetery', ''))}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Emplacement</div>
                            <div class="info-value">{data.get('plot_location', 'Non renseigné')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">N° de tombe</div>
                            <div class="info-value">{data.get('tomb_number', 'Non renseigné')}</div>
                        </div>
                    </div>
                    <div style="margin-top: 15px;">
                        <div class="info-label">Particularités</div>
                        <div class="info-value">{particularities_text}</div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">📋 FORMULE & PLANNING</div>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Formule</div>
                            <div class="info-value">{formula_names.get(data.get('formula', ''), data.get('formula', ''))}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Prix</div>
                            <div class="info-value" style="color: #7a9e7e; font-size: 20px;">💰 {data.get('price', 0)}€</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Date souhaitée</div>
                            <div class="info-value">📅 {data.get('reservation_date', '')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Photos fournies</div>
                            <div class="info-value">📷 {len(data.get('photo_urls', []))} photo(s)</div>
                        </div>
                    </div>
                    {photos_html}
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f0f7f1; border-radius: 8px;">
                    <p style="margin: 0 0 15px; font-weight: bold; color: #4e7352;">PROCHAINES ACTIONS</p>
                    <p style="margin: 5px 0;">1️⃣ Appeler le client : <strong>{data.get('phone', '')}</strong></p>
                    <p style="margin: 5px 0;">2️⃣ Confirmer la disponibilité du {data.get('reservation_date', '')}</p>
                    <p style="margin: 5px 0;">3️⃣ Valider la réservation dans le backoffice</p>
                    <a href__="{SITE_URL}/Admin" class="action-button">Accéder au backoffice →</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    success = send_email(
        GMAIL_USER,
        f'🔔 Nouvelle demande : {data.get("first_name", "")} {data.get("last_name", "")} – {cemetery_names.get(data.get("cemetery", ""), "")}',
        html_body
    )
    
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error'}), 500

@app.route('/api/send-review-request', methods=['POST'])
def send_review_request():
    """Email pour demander un avis après intervention"""
    data = request.json
    
    review_url = f"{SITE_URL}/review?id={data['request_id']}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Jost', Arial, sans-serif; line-height: 1.6; color: #5a5752; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #fdfcf9; }}
            .header {{ background: linear-gradient(135deg, #7a9e7e 0%, #4e7352 100%); padding: 40px 20px; text-align: center; }}
            .logo {{ width: 80px; height: 80px; background: white; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; color: #7a9e7e; }}
            .content {{ padding: 40px 30px; text-align: center; }}
            .stars {{ font-size: 40px; margin: 20px 0; }}
            .cta-button {{ display: inline-block; background: linear-gradient(135deg, #7a9e7e 0%, #4e7352 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 50px; font-weight: 600; font-size: 16px; margin: 20px 0; }}
            .footer {{ background: #5a5752; color: rgba(255,255,255,0.7); padding: 30px 20px; text-align: center; font-size: 13px; }}
            h1 {{ font-family: 'Cormorant Garamond', serif; color: white; font-size: 32px; margin: 0; font-weight: 400; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">PNT</div>
                <h1>💚 Merci pour votre confiance</h1>
            </div>
            
            <div class="content">
                <p style="font-size: 16px;">
                    Bonjour <strong>{data['client_name']}</strong>,
                </p>
                
                <p style="font-size: 15px; line-height: 1.8; margin: 25px 0;">
                    Nous avons récemment entretenu la sépulture de <strong>{data['deceased_name']}</strong> 
                    et espérons que notre intervention vous a donné satisfaction.
                </p>
                
                <div class="stars">⭐⭐⭐⭐⭐</div>
                
                <p style="font-size: 15px; line-height: 1.8; margin: 25px 0;">
                    Votre avis est très important pour nous et aide d'autres familles 
                    à choisir nos services en toute confiance.
                </p>
                
                <p style="font-size: 15px; font-weight: 600; margin: 30px 0 20px;">
                    Pourriez-vous prendre 2 minutes pour partager votre expérience ?
                </p>
                
                <a href__="{review_url}" class="cta-button">
                    ✍️ Laisser un avis
                </a>
                
                <p style="font-size: 13px; color: #9e9b96; margin-top: 30px; font-style: italic;">
                    Nous restons à votre disposition pour tout besoin futur.
                </p>
            </div>
            
            <div class="footer">
                <p style="margin: 0 0 15px;"><strong style="color: white;">PNT – Soins des Tombes</strong></p>
                <p style="margin: 5px 0;">📞 07 68 29 53 49</p>
                <p style="margin: 5px 0;">✉️ pnt.soins.tombes@gmail.com</p>
                <p style="margin-top: 20px; font-size: 11px; opacity: 0.6;">
                    Paul · Nélio · Tom – Entrepreneurs locaux, Côte-d'Or (21)
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    success = send_email(
        data['to'],
        '💚 Votre avis nous intéresse – PNT Soins des Tombes',
        html_body
    )
    
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Vérifier que le serveur fonctionne"""
    return jsonify({'status': 'ok', 'service': 'PNT Email Service'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)