import smtplib
import csv
import io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, render_template_string, request, flash

app = Flask(__name__)
app.secret_key = "abifinanzen_premium_key"

# --- KONFIGURATION ---
SMTP_SERVER = "smtp.zeptomail.eu"
SMTP_PORT = 587
SMTP_USER = "emailapikey"
SMTP_PASSWORD = "yA6KbHtbug+jwGoGRhRvhJOL+t03rP06iiy14irif8IhI9Ll2qFt0EducdCzLmDdjI/Q4qhTPtsTI9rv79xafJA0NoICfJTGTuv4P2uV48xh8ciEYNYig56qBbgUG6RLcBMjDCwxRPgoWA=="

# Das ist die Adresse, die du bei ZeptoMail verifiziert hast!
ACTUAL_SENDER_EMAIL = "noreply@abifinanzen.de" 
SENDER_NAME = "Abifinanzen Team"
# --- HOCHWERTIGES HTML EMAIL TEMPLATE ---
def generate_html_email(title, greeting, lead_text, amount_label, amount_value, detail_label, detail_value, footer_extra=""):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
            body {{ font-family: 'Inter', Helvetica, Arial, sans-serif; background-color: #f0f2f5; margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }}
            .wrapper {{ width: 100%; table-layout: fixed; background-color: #f0f2f5; padding-bottom: 40px; }}
            .main {{ background-color: #ffffff; margin: 0 auto; width: 100%; max-width: 600px; border-spacing: 0; color: #1a1f36; border-radius: 12px; overflow: hidden; margin-top: 30px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }}
            .header {{ background-color: #1a1f36; padding: 40px; text-align: center; color: #ffffff; }}
            .header h1 {{ margin: 0; font-size: 24px; letter-spacing: -0.5px; }}
            .content {{ padding: 40px; line-height: 1.6; font-size: 16px; }}
            .info-box {{ background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 25px 0; }}
            .info-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid #edf2f7; padding-bottom: 10px; }}
            .info-row:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
            .label {{ color: #64748b; font-size: 14px; font-weight: 600; text-transform: uppercase; }}
            .value {{ font-weight: 700; color: #0f172a; }}
            .footer {{ text-align: center; font-size: 12px; color: #94a3b8; padding: 20px; }}
        </style>
    </head>
    <body>
        <div class="wrapper">
            <table class="main">
                <tr>
                    <td class="header">
                        <h1>abifinanzen.de</h1>
                    </td>
                </tr>
                <tr>
                    <td class="content">
                        <h2 style="margin-top:0; font-size: 20px;">{title}</h2>
                        <p>Hallo {greeting},</p>
                        <p>{lead_text}</p>
                        
                        <div class="info-box">
                            <div class="info-row">
                                <span class="label">{amount_label}</span>
                                <span class="value">{amount_value}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">{detail_label}</span>
                                <span class="value">{detail_value}</span>
                            </div>
                        </div>
                        <p style="font-size: 14px; color: #475569;">{footer_extra}</p>
                    </td>
                </tr>
            </table>
            <div class="footer">
                Diese E-Mail wurde automatisch über das Abifinanzen-System versendet.<br>
                &copy; 2026 Abikasse - Gymnasium Mustermann
            </div>
        </div>
    </body>
    </html>
    """

# --- DASHBOARD UI ---
MAIN_UI = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Abifinanzen Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root { --primary: #1a1f36; --accent: #3b82f6; }
        body { background-color: #f8fafc; font-family: 'Segoe UI', sans-serif; color: #1e293b; }
        .nav-custom { background-color: var(--primary); padding: 1rem; color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card { border: none; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .btn-send { background-color: var(--primary); color: white; font-weight: 600; border-radius: 8px; transition: all 0.3s; }
        .btn-send:hover { background-color: var(--accent); color: white; transform: translateY(-1px); }
        .form-label { font-weight: 600; font-size: 0.9rem; color: #64748b; }
        .header-title { font-weight: 800; letter-spacing: -1px; }
    </style>
</head>
<body>
    <nav class="nav-custom mb-5">
        <div class="container d-flex justify-content-between align-items-center">
            <span class="h4 mb-0 header-title">abifinanzen.de</span>
            <span class="badge bg-light text-dark">Admin-Konsole 2026</span>
        </div>
    </nav>

    <div class="container">
        {% with messages = get_flashed_messages() %}
            {% if messages %}{% for m in messages %}<div class="alert alert-primary border-0 shadow-sm">{{ m }}</div>{% endfor %}{% endif %}
        {% endwith %}

        <div class="row g-4">
            <div class="col-lg-7">
                <div class="card p-4 h-100">
                    <h5 class="mb-4">E-Mail erstellen</h5>
                    <form method="POST" action="/send_single">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Email-Typ</label>
                                <select name="type" class="form-select border-0 bg-light">
                                    <option value="confirm">Zahlungsbestätigung</option>
                                    <option value="remind">Zahlungserinnerung</option>
                                    <option value="status">Kontostand-Info</option>
                                    <option value="custom">Individuelle Nachricht</option>
                                </select>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Empfänger E-Mail</label>
                                <input type="email" name="recipient" class="form-control border-0 bg-light" required>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Vorname/Name</label>
                                <input type="text" name="name" class="form-control border-0 bg-light">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Betrag</label>
                                <input type="text" name="amount" class="form-control border-0 bg-light" placeholder="z.B. 45,00 €">
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Zweck / Frist</label>
                            <input type="text" name="purpose" class="form-control border-0 bg-light" placeholder="z.B. 15.06.2026">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Zusatznachricht (Optional)</label>
                            <textarea name="message" class="form-control border-0 bg-light" rows="3"></textarea>
                        </div>
                        <button type="submit" class="btn btn-send w-100 py-3 mt-2">E-Mail jetzt versenden</button>
                    </form>
                </div>
            </div>

            <div class="col-lg-5">
                <div class="card p-4 mb-4">
                    <h5 class="mb-3">Bulk-Import (CSV)</h5>
                    <p class="small text-muted">Format: E-Mail, Name, Betrag, Zweck</p>
                    <form method="POST" action="/send_bulk" enctype="multipart/form-data">
                        <select name="type" class="form-select border-0 bg-light mb-3">
                            <option value="confirm">Zahlungsbestätigung</option>
                            <option value="remind">Zahlungserinnerung</option>
                        </select>
                        <input type="file" name="file" class="form-control border-0 bg-light mb-3" accept=".csv">
                        <button type="submit" class="btn btn-outline-dark w-100">Liste abarbeiten</button>
                    </form>
                </div>
                <div class="card p-4 bg-primary text-white">
                    <h6>Status-Check</h6>
                    <p class="small opacity-75">Server: {{ smtp_host }}<br>Port: {{ smtp_port }}</p>
                    <div class="d-flex align-items-center">
                        <div class="spinner-grow spinner-grow-sm text-success me-2"></div>
                        <span class="small">SMTP System bereit</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# --- LOGIK ---
def send_mail(recipient, subject, html_content):
    try:
        msg = MIMEMultipart()
        # WICHTIG: Hier wird die verifizierte Adresse als Absender gesetzt
        msg['From'] = f"{SENDER_NAME} <{ACTUAL_SENDER_EMAIL}>"
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            # Der Login erfolgt mit 'emailapikey'
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"SMTP Fehler: {e}")
        return False

@app.route('/')
def index():
    return render_template_string(MAIN_UI, smtp_host=SMTP_SERVER, smtp_port=SMTP_PORT)

@app.route('/send_single', methods=['POST'])
def send_single():
    t = request.form.get('type')
    rec = request.form.get('recipient')
    name = request.form.get('name')
    amt = request.form.get('amount')
    purp = request.form.get('purpose')
    msg_extra = request.form.get('message')

    if t == "confirm":
        subj, html = "Zahlung bestätigt - abifinanzen.de", generate_html_email(
            "Vielen Dank!", name, "Wir haben deine Zahlung erfolgreich verbucht. Dein Platz auf der Gästeliste ist damit gesichert.", 
            "Betrag", amt, "Verwendungszweck", purp, "Behalte diese Mail als Beleg für deine Unterlagen.")
    elif t == "remind":
        subj, html = "Zahlungserinnerung - abifinanzen.de", generate_html_email(
            "Erinnerung", name, "Es steht noch ein Betrag für deinen Abiball offen. Bitte überweise diesen zeitnah.", 
            "Offener Betrag", amt, "Frist bis", purp, "Solltest du bereits überwiesen haben, ignoriere diese Mail.")
    elif t == "status":
        subj, html = "Dein Kontostand - abifinanzen.de", generate_html_email(
            "Aktueller Stand", name, "Hier ist die Übersicht deines aktuellen Guthabens in der Abikasse.", 
            "Guthaben", amt, "Letzte Buchung", purp)
    else:
        subj, html = "Wichtige Nachricht - abifinanzen.de", generate_html_email(
            "Update", name, msg_extra, "Referenz", amt if amt else "-", "Info", purp if purp else "-")

    if send_mail(rec, subj, html):
        flash(f"Premium-Email erfolgreich an {rec} gesendet!")
    else:
        flash("Fehler beim Versand. Bitte SMTP-Log prüfen.")
    return index()

@app.route('/send_bulk', methods=['POST'])
def send_bulk():
    m_type = request.form.get('type')
    file = request.files['file']
    if not file: return "Datei fehlt"
    
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.reader(stream)
    
    count = 0
    for row in csv_input:
        if len(row) < 4: continue
        email, name, amount, purpose = row
        # Hier wird die Logik für Bulk analog zu send_single angewandt
        if m_type == "confirm":
            subj, html = "Zahlung bestätigt", generate_html_email("Bestätigung", name, "Zahlung erhalten.", "Betrag", amount, "Zweck", purpose)
        else:
            subj, html = "Erinnerung", generate_html_email("Zahlung offen", name, "Bitte überweisen.", "Betrag", amount, "Frist", purpose)
        
        if send_mail(email, subj, html):
            count += 1
            
    flash(f"Bulk-Versand abgeschlossen: {count} Empfänger erreicht.")
    return index()

if __name__ == '__main__':
    app.run(debug=True)
