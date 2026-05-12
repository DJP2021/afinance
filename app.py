import os
import csv
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, render_template_string, request, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "abifinanzen_premium_2026"

# --- CONFIG ---
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

SMTP_SERVER = "smtp.zeptomail.eu"
SMTP_PORT = 465
SMTP_USER = "emailapikey"
SMTP_PASSWORD = os.environ.get("SMTP_PASS", "yA6KbHtbug+jwGoGRhRvhJOL+t03rP06iiy14irif8IhI9Ll2qFt0EducdCzLmDdjI/Q4qhTPtsTI9rv79xafJA0NoICfJTGTuv4P2uV48xh8ciEYNYig56qBbgUG6RLcBMjDCwxRPgoWA==")

ACTUAL_SENDER = "noreply@abifinanzen.de"
SENDER_NAME = "Abifinanzen Management"

current_logo = None

# --- ENGINE ---
def send_mail(recipient, subject, html_content):
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{SENDER_NAME} <{ACTUAL_SENDER}>"
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=12) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"SMTP Fehler: {e}")
        return False

# --- UI COMPONENTS ---
HEADER = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <style>
        :root { --sidebar-bg: #0f172a; --accent: #3b82f6; }
        body { background-color: #f8fafc; font-family: 'Inter', system-ui, sans-serif; }
        .sidebar { background: var(--sidebar-bg); min-height: 100vh; color: white; position: fixed; width: 250px; padding-top: 20px; }
        .main-content { margin-left: 250px; padding: 40px; }
        .nav-link { color: #94a3b8; padding: 12px 20px; border-radius: 8px; margin: 4px 15px; display: flex; align-items: center; transition: 0.2s; }
        .nav-link i { margin-right: 12px; font-size: 1.2rem; }
        .nav-link:hover, .nav-link.active { background: rgba(255,255,255,0.1); color: white; }
        .nav-link.active { border-left: 4px solid var(--accent); }
        .card { border: none; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .stat-card { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: white; }
        .preview-pane { background: #e2e8f0; border-radius: 12px; padding: 20px; position: sticky; top: 40px; }
    </style>
</head>
<body>
    <div class="sidebar shadow">
        <div class="px-4 mb-4">
            <h4 class="fw-bold text-white mb-0">abi<span class="text-primary">finanzen</span></h4>
            <small class="text-muted">Admin Panel v2.0</small>
        </div>
        <div class="nav flex-column">
            <a href="/" class="nav-link {{'active' if page=='dash' else ''}}"><i class="bi bi-speedometer2"></i> Dashboard</a>
            <a href="/confirm" class="nav-link {{'active' if page=='confirm' else ''}}"><i class="bi bi-check-circle"></i> Bestätigung</a>
            <a href="/remind" class="nav-link {{'active' if page=='remind' else ''}}"><i class="bi bi-alarm"></i> Erinnerung</a>
            <a href="/status" class="nav-link {{'active' if page=='status' else ''}}"><i class="bi bi-bar-chart"></i> Kontostand</a>
            <a href="/custom" class="nav-link {{'active' if page=='custom' else ''}}"><i class="bi bi-code-slash"></i> Custom HTML</a>
        </div>
    </div>
    <div class="main-content">
"""

# --- EMAIL TEMPLATE GENERATOR ---
def build_pro_email(title, name, lead, val1_label, val1_val, val2_label, val2_val, color="#3b82f6", button_text="Details ansehen"):
    logo_path = f"{request.host_url}static/uploads/{current_logo}" if current_logo else ""
    logo_img = f'<img src="{logo_path}" height="50" style="margin-bottom:20px; outline:none; text-decoration:none;">' if current_logo else f'<h1 style="color:{color}; margin:0;">Abifinanzen</h1>'
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; background-color: #f1f5f9; font-family: Arial, sans-serif; }}
            .container {{ width: 100%; max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
            .header {{ background-color: #ffffff; padding: 40px; text-align: center; border-bottom: 1px solid #e2e8f0; }}
            .body {{ padding: 40px; color: #1e293b; line-height: 1.6; }}
            .info-table {{ width: 100%; background: #f8fafc; border-radius: 6px; border-spacing: 0; margin: 20px 0; }}
            .info-table td {{ padding: 15px; border-bottom: 1px solid #edf2f7; }}
            .label {{ color: #64748b; font-size: 12px; font-weight: bold; text-transform: uppercase; }}
            .value {{ font-size: 16px; font-weight: bold; color: #0f172a; text-align: right; }}
            .footer {{ background: #f8fafc; padding: 20px; text-align: center; font-size: 12px; color: #94a3b8; }}
            .btn {{ display: inline-block; padding: 12px 24px; background: {color}; color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">{logo_img}</div>
            <div class="body">
                <h2 style="margin-top:0; color:#0f172a;">{title}</h2>
                <p>Hallo {name},</p>
                <p>{lead}</p>
                <table class="info-table">
                    <tr><td class="label">{val1_label}</td><td class="value">{val1_val}</td></tr>
                    <tr><td class="label">{val2_label}</td><td class="value">{val2_val}</td></tr>
                </table>
                <center><a href="https://abifinanzen.de" class="btn">{button_text}</a></center>
            </div>
            <div class="footer">Diese Mail wurde automatisch generiert. &copy; 2026 Abifinanzen.de</div>
        </div>
    </body>
    </html>
    """

# --- ROUTES ---

@app.route('/')
def index():
    logo_url = url_for('uploaded_file', filename=current_logo) if current_logo else None
    content = f"""
    <div class="row g-4">
        <div class="col-md-8">
            <div class="card p-5 stat-card shadow-lg mb-4">
                <h1 class="display-5 fw-bold">Willkommen zurück!</h1>
                <p class="lead opacity-75">Hier verwaltest du die Finanzen deiner Stufe. Wähle eine Mail-Vorlage aus, um loszulegen.</p>
                <div class="d-flex gap-3 mt-3">
                    <div class="p-3 bg-white bg-opacity-10 rounded">
                        <h4 class="mb-0">Aktiv</h4>
                        <small>SMTP System bereit</small>
                    </div>
                </div>
            </div>
            <div class="card p-4">
                <h5><i class="bi bi-image me-2"></i>Globales Logo-Setup</h5>
                <p class="text-muted small">Lade hier das Stufen-Logo hoch. Es wird automatisch in alle professionellen Templates eingebunden.</p>
                <form action="/upload_logo" method="POST" enctype="multipart/form-data" class="d-flex gap-2">
                    <input type="file" name="logo" class="form-control" accept="image/*">
                    <button class="btn btn-primary px-4">Speichern</button>
                </form>
                {f'<div class="mt-3 p-3 bg-light rounded text-center"><img src="{logo_url}" height="50"></div>' if logo_url else ''}
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-4 mb-4">
                <h6>Schnellzugriff</h6>
                <div class="list-group list-group-flush">
                    <a href="/confirm" class="list-group-item list-group-item-action border-0 px-0"><i class="bi bi-check2-circle text-success me-2"></i> Zahlung bestätigen</a>
                    <a href="/remind" class="list-group-item list-group-item-action border-0 px-0"><i class="bi bi-exclamation-triangle text-warning me-2"></i> Mahnung senden</a>
                </div>
            </div>
        </div>
    </div>
    """
    return render_template_string(HEADER + content + "</div></body></html>", page="dash")

@app.route('/upload_logo', methods=['POST'])
def upload_logo():
    global current_logo
    file = request.files.get('logo')
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        current_logo = filename
        flash("Logo erfolgreich aktualisiert!")
    return redirect(request.referrer)

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/<mode>')
def mail_pages(mode):
    if mode not in ['confirm', 'remind', 'status', 'custom']: return redirect('/')
    
    config = {
        'confirm': {'title': 'Zahlungsbestätigung', 'color': '#10b981', 'icon': 'bi-check-all'},
        'remind': {'title': 'Erinnerung', 'color': '#f59e0b', 'icon': 'bi-clock-history'},
        'status': {'title': 'Kontostand', 'color': '#3b82f6', 'icon': 'bi-wallet2'}
    }
    
    if mode == 'custom':
        form_content = """
        <div class="row">
            <div class="col-md-6">
                <div class="card p-4 shadow-sm">
                    <h5><i class="bi bi-code-square me-2"></i>HTML Editor</h5>
                    <form action="/send_logic" method="POST">
                        <input type="hidden" name="type" value="custom">
                        <input type="email" name="email" class="form-control mb-3" placeholder="Empfänger" required>
                        <input type="text" name="subject" class="form-control mb-3" placeholder="E-Mail Betreff" required>
                        <textarea id="code" name="html_content" class="form-control mb-3" rows="12" style="font-family: monospace;"></textarea>
                        <button class="btn btn-dark w-100 py-3">E-Mail absenden</button>
                    </form>
                </div>
            </div>
            <div class="col-md-6">
                <div class="preview-pane shadow-sm">
                    <h6>Vorschau</h6>
                    <iframe id="prev" style="width:100%; height:500px; border:none; background:white; border-radius:8px;"></iframe>
                </div>
            </div>
        </div>
        <script>
            const i = document.getElementById('code'); const p = document.getElementById('prev');
            i.addEventListener('input', () => { const d = p.contentDocument; d.open(); d.write(i.value); d.close(); });
        </script>
        """
    else:
        c = config[mode]
        form_content = f"""
        <div class="row">
            <div class="col-md-5">
                <div class="card p-4 shadow-sm border-0">
                    <h4 style="color:{c['color']}"><i class="bi {c['icon']} me-2"></i>{c['title']}</h4>
                    <form action="/send_logic" method="POST" class="mt-4">
                        <input type="hidden" name="type" value="{mode}">
                        <div class="mb-3"><label class="small fw-bold">EMPFÄNGER EMAIL</label><input type="email" name="email" class="form-control shadow-sm" required></div>
                        <div class="mb-3"><label class="small fw-bold">NAME DES SCHÜLERS</label><input type="text" name="name" class="form-control shadow-sm" required></div>
                        <div class="mb-3"><label class="small fw-bold">HAUPT-BETRAG</label><input type="text" name="v1" class="form-control shadow-sm" placeholder="45,00 €"></div>
                        <div class="mb-3"><label class="small fw-bold">ZUSATZ-INFO</label><input type="text" name="v2" class="form-control shadow-sm" placeholder="z.B. Frist 20.05."></div>
                        <div class="mb-3"><label class="small fw-bold">BUTTON TEXT</label><input type="text" name="btn_text" class="form-control shadow-sm" value="Im Dashboard prüfen"></div>
                        <button class="btn w-100 py-3 text-white fw-bold shadow-sm" style="background:{c['color']}">Senden</button>
                    </form>
                </div>
            </div>
            <div class="col-md-7">
                <div class="preview-pane shadow-sm text-center">
                    <p class="small text-muted mb-3 text-uppercase fw-bold">Pro-Template Live Vorschau</p>
                    <div class="bg-white rounded shadow-sm mx-auto" style="max-width:400px; height:500px; overflow:hidden;">
                        <div style="background:{c['color']}; height:8px;"></div>
                        <div class="p-4"><div class="bg-light mx-auto" style="height:30px; width:120px; border-radius:4px;"></div></div>
                        <div class="px-4 text-start"><div class="bg-light mb-2" style="height:20px; width:180px;"></div><div class="bg-light" style="height:12px; width:240px;"></div></div>
                        <div class="p-4"><div class="bg-light rounded" style="height:100px;"></div></div>
                        <div class="mt-2"><div class="bg-light mx-auto rounded" style="height:40px; width:150px;"></div></div>
                    </div>
                </div>
            </div>
        </div>
        """
    return render_template_string(HEADER + form_content + "</div></body></html>", page=mode)

@app.route('/send_logic', methods=['POST'])
def send_logic():
    m = request.form.get('type')
    email = request.form.get('email')
    
    if m == 'custom':
        subj = request.form.get('subject')
        content = request.form.get('html_content')
    else:
        name, v1, v2, bt = request.form.get('name'), request.form.get('v1'), request.form.get('v2'), request.form.get('btn_text')
        if m == 'confirm':
            subj, content = "Zahlung erfolgreich | Informationen zu Deinem Abijahrgang", build_pro_email("Zahlung verbucht", name, "Deine Zahlung für die Abikasse wurde erfolgreich registriert.", "Betrag", v1, "Verwendungszweck", v2, "#10b981")
        elif m == 'remind':
            subj, content = "WICHTIG: Zahlung ausstehend | Informationen zu Deinem Abijahrgang", build_pro_email("Zahlungserinnerung", name, "Uns ist aufgefallen, dass dein Beitrag für den Abiball noch fehlt.", "Offener Betrag", v1, "Frist bis", v2, "#f59e0b")
        else:
            subj, content = "Dein aktueller Kontostand | Informationen zu Deinem Abijahrgang", build_pro_email("Kontostand-Update", name, "Hier ist die aktuelle Übersicht deiner Einzahlungen.", "Gesamtguthaben", v1, "#3b82f6")

    if send_mail(email, subj, content):
        flash(f"Erfolg: E-Mail an {email} wurde übermittelt.")
    else:
        flash("Fehler: SMTP Verbindung fehlgeschlagen.")
    return redirect(f"/{m}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
