import os
import csv
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, render_template_string, request, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "abifinanzen_ultra_secret"

# --- CONFIG ---
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# SMTP Settings
SMTP_SERVER = "smtp.zeptomail.eu"
SMTP_PORT = 465
SMTP_USER = "emailapikey"
SMTP_PASSWORD = os.environ.get("SMTP_PASS", "yA6KbHtbug+jwGoGRhRvhJOL+t03rP06iiy14irif8IhI9Ll2qFt0EducdCzLmDdjI/Q4qhTPtsTI9rv79xafJA0NoICfJTGTuv4P2uV48xh8ciEYNYig56qBbgUG6RLcBMjDCwxRPgoWA==")

ACTUAL_SENDER = "noreply@abifinanzen.de"
SENDER_NAME = "Abifinanzen Admin"

# Globaler Pfad für das Logo
current_logo = None

# --- HELPER ---
def send_mail(recipient, subject, html_content):
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{SENDER_NAME} <{ACTUAL_SENDER}>"
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Fehler: {e}")
        return False

# --- TEMPLATES ---

NAV = """
<nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4 shadow">
    <div class="container">
        <a class="navbar-brand fw-bold" href="/">abifinanzen.de</a>
        <div class="navbar-nav">
            <a class="nav-link" href="/confirm">✅ Bestätigung</a>
            <a class="nav-link" href="/remind">⏰ Erinnerung</a>
            <a class="nav-link" href="/status">📊 Kontostand</a>
            <a class="nav-link" href="/custom">🎨 Custom HTML</a>
        </div>
    </div>
</nav>
"""

# Gemeinsame Komponente für Logo-Upload
LOGO_UPLOAD_PART = """
<div class="card mb-3 p-3 border-0 bg-light">
    <h6>Header Logo</h6>
    {% if logo_url %}
        <img src="{{ logo_url }}" style="max-height: 50px;" class="mb-2 d-block">
    {% endif %}
    <form action="/upload_logo" method="POST" enctype="multipart/form-data" class="d-flex gap-2">
        <input type="file" name="logo" class="form-control form-control-sm" accept="image/*">
        <button class="btn btn-sm btn-outline-secondary">Upload</button>
    </form>
</div>
"""

# --- ROUTES ---

@app.route('/')
def index():
    return render_template_string(f"{NAV}<div class='container'><h1>Willkommen</h1><p>Wähle einen Typ oben aus.</p></div>")

@app.route('/upload_logo', methods=['POST'])
def upload_logo():
    global current_logo
    file = request.files.get('logo')
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        current_logo = filename
    return redirect(request.referrer)

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ROUTE: Bestätigung (Grün-Themed)
@app.route('/confirm')
def confirm_page():
    logo_url = url_for('uploaded_file', filename=current_logo) if current_logo else None
    html = f"""
    {NAV}
    <div class="container">
        <div class="row">
            <div class="col-md-6">
                <div class="card p-4 border-start border-success border-5">
                    <h2 class="text-success">Zahlungsbestätigung</h2>
                    {LOGO_UPLOAD_PART}
                    <form action="/send_logic" method="POST">
                        <input type="hidden" name="type" value="confirm">
                        <input type="email" name="email" class="form-control mb-2" placeholder="Schüler Email" required>
                        <input type="text" name="name" class="form-control mb-2" placeholder="Vorname">
                        <input type="text" name="val1" class="form-control mb-2" placeholder="Betrag (€)">
                        <input type="text" name="val2" class="form-control mb-2" placeholder="Verwendungszweck">
                        <button class="btn btn-success w-100">Mail senden</button>
                    </form>
                </div>
            </div>
            <div class="col-md-6">
                <div class="p-4 bg-white shadow-sm rounded">
                    <small class="text-muted">Vorschau:</small>
                    <div style="background:#e8f5e9; padding:20px; text-align:center;">
                        {f'<img src="{logo_url}" style="max-height:40px;">' if logo_url else '<h4>LOGOTYP</h4>'}
                    </div>
                    <div style="padding:20px; border:1px solid #eee;">
                        <h3 style="color:#2e7d32;">Vielen Dank!</h3>
                        <p>Zahlung wurde erfolgreich verbucht.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    """
    return render_template_string(html, logo_url=logo_url)

# ROUTE: Erinnerung (Gelb/Orange-Themed)
@app.route('/remind')
def remind_page():
    logo_url = url_for('uploaded_file', filename=current_logo) if current_logo else None
    html = f"""
    {NAV}
    <div class="container">
        <div class="card p-4 border-start border-warning border-5 shadow" style="max-width:600px; margin:auto;">
            <h2 class="text-warning">Zahlungserinnerung</h2>
            {LOGO_UPLOAD_PART}
            <form action="/send_logic" method="POST">
                <input type="hidden" name="type" value="remind">
                <input type="email" name="email" class="form-control mb-2" placeholder="Email" required>
                <input type="text" name="name" class="form-control mb-2" placeholder="Name">
                <input type="text" name="val1" class="form-control mb-2" placeholder="Offener Betrag">
                <input type="text" name="val2" class="form-control mb-2" placeholder="Frist bis">
                <button class="btn btn-warning w-100 fw-bold">Erinnerung schicken</button>
            </form>
        </div>
    </div>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    """
    return render_template_string(html, logo_url=logo_url)

# ROUTE: Status (Blau-Themed)
@app.route('/status')
def status_page():
    logo_url = url_for('uploaded_file', filename=current_logo) if current_logo else None
    html = f"""
    {NAV}
    <div class="container">
        <div class="card p-4 border-start border-primary border-5" style="max-width:600px; margin:auto;">
            <h2 class="text-primary">Kontostand-Update</h2>
            {LOGO_UPLOAD_PART}
            <form action="/send_logic" method="POST">
                <input type="hidden" name="type" value="status">
                <input type="email" name="email" class="form-control mb-2" placeholder="Email" required>
                <input type="text" name="name" class="form-control mb-2" placeholder="Name">
                <input type="text" name="val1" class="form-control mb-2" placeholder="Aktuelles Guthaben">
                <input type="text" name="val2" class="form-control mb-2" placeholder="Letzte Einzahlung">
                <button class="btn btn-primary w-100">Status senden</button>
            </form>
        </div>
    </div>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    """
    return render_template_string(html, logo_url=logo_url)

# ROUTE: Custom (Live Preview)
@app.route('/custom')
def custom_page():
    html = f"""
    {NAV}
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-6">
                <h3>Custom HTML Editor</h3>
                <form action="/send_logic" method="POST">
                    <input type="hidden" name="type" value="custom">
                    <input type="email" name="email" class="form-control mb-2" placeholder="Empfänger Email" required>
                    <input type="text" name="subject" class="form-control mb-2" placeholder="Betreff" required>
                    <textarea id="htmlInput" name="html_content" class="form-control" rows="15" placeholder="Hier HTML eingeben..."></textarea>
                    <button class="btn btn-dark w-100 mt-3">HTML Mail Senden</button>
                </form>
            </div>
            <div class="col-md-6">
                <h3>Live Vorschau</h3>
                <iframe id="preview" style="width:100%; height:600px; border:1px solid #ddd; background:white;"></iframe>
            </div>
        </div>
    </div>
    <script>
        const input = document.getElementById('htmlInput');
        const preview = document.getElementById('preview');
        input.addEventListener('input', () => {{
            const doc = preview.contentDocument || preview.contentWindow.document;
            doc.open();
            doc.write(input.value);
            doc.close();
        }});
    </script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    """
    return render_template_string(html)

@app.route('/send_logic', methods=['POST'])
def send_logic():
    m_type = request.form.get('type')
    email = request.form.get('email')
    
    if m_type == "custom":
        subject = request.form.get('subject')
        content = request.form.get('html_content')
    else:
        name = request.form.get('name')
        v1 = request.form.get('val1')
        v2 = request.form.get('val2')
        logo_html = f'<img src="{request.host_url}static/uploads/{current_logo}" style="max-height:60px; margin-bottom:20px;">' if current_logo else ""
        
        if m_type == "confirm":
            subject = "Zahlung bestätigt - abifinanzen"
            color = "#2e7d32"
            content = f"<div style='font-family:sans-serif; padding:30px; border:10px solid {color};'>{logo_html}<h2 style='color:{color}'>Zahlung bestätigt</h2><p>Hallo {name}, wir haben <b>{v1}</b> für <b>{v2}</b> erhalten.</p></div>"
        elif m_type == "remind":
            subject = "Dringend: Zahlung ausstehend"
            color = "#ed6c02"
            content = f"<div style='font-family:sans-serif; padding:30px; border:10px solid {color};'>{logo_html}<h2 style='color:{color}'>Zahlung fehlt noch</h2><p>Hallo {name}, bitte überweise <b>{v1}</b> bis zum <b>{v2}</b>.</p></div>"
        else: # status
            subject = "Dein Kontostand"
            color = "#0288d1"
            content = f"<div style='font-family:sans-serif; padding:30px; border:10px solid {color};'>{logo_html}<h2 style='color:{color}'>Dein Saldo</h2><p>Hallo {name}, dein Guthaben beträgt: <b>{v1}</b>. Letzte Buchung: {v2}.</p></div>"

    if send_mail(email, subject, content):
        flash(f"Gesendet an {email}")
    else:
        flash("SMTP Fehler")
    return redirect(url_for(f'{m_type}_page'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
