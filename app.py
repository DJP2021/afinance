import os
import csv
import io
import requests
from flask import Flask, render_template_string, request, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = "abifinanzen_premium_key"

# --- KONFIGURATION (API statt SMTP für Render Stabilität) ---
ZEPTO_API_URL = "https://api.zeptomail.eu/v1.1/email"
ZEPTO_KEY = "yA6KbHtbug+jwGoGRhRvhJOL+t03rP06iiy14irif8IhI9Ll2qFt0EducdCzLmDdjI/Q4qhTPtsTI9rv79xafJA0NoICfJTGTuv4P2uV48xh8ciEYNYig56qBbgUG6RLcBMjDCwxRPgoWA=="
ACTUAL_SENDER = "noreply@abifinanzen.de"
SENDER_NAME = "Abifinanzen Team"

# --- EMAIL ENGINE ---
def send_zeptomail(recipient, subject, html_content):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Zoho-enczpt {ZEPTO_KEY}"
    }
    payload = {
        "from": {"address": ACTUAL_SENDER, "name": SENDER_NAME},
        "to": [{"email_address": {"address": recipient}}],
        "subject": subject,
        "htmlbody": html_content
    }
    try:
        response = requests.post(ZEPTO_API_URL, json=payload, headers=headers, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"API Fehler: {e}")
        return False

# --- TEMPLATES ---
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Abifinanzen Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root { --primary: #1a1f36; --accent: #3b82f6; }
        body { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
        .sidebar { background: var(--primary); min-height: 100vh; color: white; padding: 20px; }
        .nav-link { color: #94a3b8; margin-bottom: 10px; border-radius: 8px; transition: 0.3s; }
        .nav-link:hover, .nav-link.active { background: rgba(255,255,255,0.1); color: white; }
        .card { border: none; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .btn-primary { background: var(--primary); border: none; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-2 sidebar d-none d-md-block">
                <h4 class="mb-5 header-title">abifinanzen</h4>
                <div class="nav flex-column">
                    <a href="/" class="nav-link">🏠 Dashboard</a>
                    <hr>
                    <a href="/type/confirm" class="nav-link">✅ Bestätigung</a>
                    <a href="/type/remind" class="nav-link">⏰ Erinnerung</a>
                    <a href="/type/status" class="nav-link">📊 Kontostand</a>
                    <a href="/type/bulk" class="nav-link">📂 Massenversand</a>
                </div>
            </nav>
            <main class="col-md-10 ms-sm-auto px-md-4 py-4">
                {% with messages = get_flashed_messages() %}
                    {% if messages %}{% for m in messages %}<div class="alert alert-info border-0 shadow-sm">{{ m }}</div>{% endfor %}{% endif %}
                {% endwith %}
                {{ content | safe }}
            </main>
        </div>
    </div>
</body>
</html>
"""

def generate_html_email(title, greeting, lead_text, amount_label, amount_value, detail_label, detail_value):
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; border-radius: 10px; overflow: hidden;">
        <div style="background: #1a1f36; color: white; padding: 30px; text-align: center;"><h1>abifinanzen.de</h1></div>
        <div style="padding: 30px; color: #333;">
            <h2>{title}</h2>
            <p>Hallo {greeting},</p>
            <p>{lead_text}</p>
            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>{amount_label}:</strong> {amount_value}</p>
                <p><strong>{detail_label}:</strong> {detail_value}</p>
            </div>
        </div>
        <div style="text-align: center; font-size: 12px; color: #999; padding: 20px;">&copy; 2026 Abikasse Team</div>
    </div>
    """

# --- ROUTES ---
@app.route('/')
def dashboard():
    html = '<div class="card p-5 text-center"><h1>Willkommen im Finanz-Admin</h1><p>Wähle links eine Kategorie aus, um E-Mails zu versenden.</p></div>'
    return render_template_string(BASE_LAYOUT, content=html)

@app.route('/type/<mode>')
def mail_form(mode):
    titles = {"confirm": "Zahlungsbestätigung", "remind": "Zahlungserinnerung", "status": "Kontostand senden", "bulk": "CSV Massen-Upload"}
    
    if mode == "bulk":
        form_content = """
        <form action="/send_bulk" method="POST" enctype="multipart/form-data">
            <div class="mb-3"><label class="form-label">CSV Datei auswählen</label><input type="file" name="file" class="form-control" accept=".csv" required></div>
            <button class="btn btn-primary w-100">Massenversand starten</button>
        </form>
        """
    else:
        form_content = f"""
        <form action="/process_send" method="POST">
            <input type="hidden" name="mode" value="{mode}">
            <div class="row mb-3">
                <div class="col-md-6"><label class="form-label">Empfänger Email</label><input type="email" name="email" class="form-control" required></div>
                <div class="col-md-6"><label class="form-label">Name des Schülers</label><input type="text" name="name" class="form-control" required></div>
            </div>
            <div class="row mb-3">
                <div class="col-md-6"><label class="form-label">Betrag (€)</label><input type="text" name="amount" class="form-control" placeholder="45,00 €"></div>
                <div class="col-md-6"><label class="form-label">Zusatz-Info (Frist/Datum)</label><input type="text" name="detail" class="form-control"></div>
            </div>
            <button class="btn btn-primary w-100">E-Mail jetzt an Einzelerzeuger senden</button>
        </form>
        """
    
    content = f'<div class="card p-4"><h3>{titles.get(mode)}</h3><hr>{form_content}</div>'
    return render_template_string(BASE_LAYOUT, content=content)

@app.route('/process_send', methods=['POST'])
def process_send():
    mode = request.form.get('mode')
    email = request.form.get('email')
    name = request.form.get('name')
    amt = request.form.get('amount')
    det = request.form.get('detail')

    if mode == "confirm":
        subj, html = "Zahlung bestätigt", generate_html_email("Vielen Dank!", name, "Deine Zahlung wurde erfolgreich verbucht.", "Erhaltener Betrag", amt, "Zweck", det)
    elif mode == "remind":
        subj, html = "Zahlungserinnerung", generate_html_email("Erinnerung", name, "Dein Beitrag steht noch aus.", "Offener Betrag", amt, "Frist", det)
    else:
        subj, html = "Dein Kontostand", generate_html_email("Kontostand", name, "Hier ist dein aktueller Status.", "Guthaben", amt, "Letzte Buchung", det)

    if send_zeptomail(email, subj, html):
        flash(f"Erfolgreich gesendet an {email}")
    else:
        flash("Fehler beim API-Versand.")
    return redirect(url_for('mail_form', mode=mode))

@app.route('/send_bulk', methods=['POST'])
def send_bulk():
    file = request.files['file']
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.reader(stream)
    count = 0
    for row in csv_input:
        if len(row) < 4: continue
        email, name, amt, det = row
        html = generate_html_email("Bestätigung", name, "Zahlung verbucht.", "Betrag", amt, "Info", det)
        if send_zeptomail(email, "Update Abikasse", html): count += 1
    flash(f"Massenversand fertig: {count} Mails verschickt.")
    return redirect(url_for('mail_form', mode='bulk'))

if __name__ == '__main__':
    app.run(debug=True)
