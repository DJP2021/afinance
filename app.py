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

# --- EMAIL TEMPLATE GENERATOR (Ohne Buttons) ---
def build_pro_email(title, name, message, val1_label, val1_val, val2_label, val2_val, color="#3b82f6"):
    logo_path = f"{request.host_url}static/uploads/{current_logo}" if current_logo else ""
    logo_img = f'<img src="{logo_path}" height="50" style="margin-bottom:20px; border:0;">' if current_logo else f'<h1 style="color:{color}; margin:0;">Abifinanzen</h1>'
    
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background-color:#f1f5f9; font-family:Arial, sans-serif;">
        <div style="width:100%; max-width:600px; margin:20px auto; background:#ffffff; border-radius:8px; overflow:hidden; border:1px solid #e2e8f0;">
            <div style="padding:40px; text-align:center; border-bottom:1px solid #e2e8f0;">{logo_img}</div>
            <div style="padding:40px; color:#1e293b; line-height:1.6;">
                <h2 style="margin-top:0; color:#0f172a;">{title}</h2>
                <p>Hallo {name},</p>
                <p>{message}</p>
                <table style="width:100%; background:#f8fafc; border-radius:6px; border-spacing:0; margin:20px 0;">
                    <tr>
                        <td style="padding:15px; border-bottom:1px solid #edf2f7; color:#64748b; font-size:12px; font-weight:bold; text-transform:uppercase;">{val1_label}</td>
                        <td style="padding:15px; border-bottom:1px solid #edf2f7; font-size:16px; font-weight:bold; color:#0f172a; text-align:right;">{val1_val}</td>
                    </tr>
                    {"<tr><td style='padding:15px; color:#64748b; font-size:12px; font-weight:bold; text-transform:uppercase;'>" + val2_label + "</td><td style='padding:15px; font-size:16px; font-weight:bold; color:#0f172a; text-align:right;'>" + val2_val + "</td></tr>" if val2_label else ""}
                </table>
            </div>
            <div style="background:#f8fafc; padding:20px; text-align:center; font-size:12px; color:#94a3b8;">
                Diese Mail wurde automatisch generiert. &copy; 2026 Abifinanzen.de
            </div>
        </div>
    </body>
    </html>
    """

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
        body { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
        .sidebar { background: var(--sidebar-bg); min-height: 100vh; color: white; position: fixed; width: 250px; padding-top: 20px; }
        .main-content { margin-left: 250px; padding: 40px; }
        .nav-link { color: #94a3b8; padding: 12px 20px; border-radius: 8px; margin: 4px 15px; display: flex; align-items: center; }
        .nav-link:hover, .nav-link.active { background: rgba(255,255,255,0.1); color: white; }
        .nav-link.active { border-left: 4px solid var(--accent); }
        .card { border: none; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="sidebar shadow">
        <div class="px-4 mb-4">
            <h4 class="fw-bold text-white mb-0">abi<span class="text-primary">finanzen</span></h4>
            <small class="text-muted">Admin Panel v2.1</small>
        </div>
        <div class="nav flex-column">
            <a href="/" class="nav-link {{'active' if page=='dash' else ''}}"><i class="bi bi-speedometer2 me-2"></i> Dashboard</a>
            <a href="/confirm" class="nav-link {{'active' if page=='confirm' else ''}}"><i class="bi bi-check-circle me-2"></i> Bestätigung</a>
            <a href="/remind" class="nav-link {{'active' if page=='remind' else ''}}"><i class="bi bi-alarm me-2"></i> Erinnerung</a>
            <a href="/status" class="nav-link {{'active' if page=='status' else ''}}"><i class="bi bi-bar-chart me-2"></i> Kontostand</a>
            <a href="/custom" class="nav-link {{'active' if page=='custom' else ''}}"><i class="bi bi-code-slash me-2"></i> Custom HTML</a>
        </div>
    </div>
    <div class="main-content">
"""

# --- ROUTES ---

@app.route('/')
def index():
    logo_url = url_for('uploaded_file', filename=current_logo) if current_logo else None
    content = f"""
    <div class="card p-5 mb-4 shadow-sm" style="background: linear-gradient(135deg, #1e293b, #0f172a); color: white;">
        <h1>Dashboard</h1>
        <p class="opacity-75">Passen Sie hier Ihr Logo an oder wählen Sie eine Vorlage.</p>
    </div>
    <div class="card p-4">
        <h5><i class="bi bi-image me-2"></i>Logo Hochladen</h5>
        <form action="/upload_logo" method="POST" enctype="multipart/form-data" class="d-flex gap-2">
            <input type="file" name="logo" class="form-control" accept="image/*">
            <button class="btn btn-primary">Speichern</button>
        </form>
        {f'<div class="mt-3 text-center"><img src="{logo_url}" height="50"></div>' if logo_url else ''}
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
        flash("Logo aktualisiert!")
    return redirect(request.referrer)

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/<mode>')
def mail_pages(mode):
    if mode not in ['confirm', 'remind', 'status', 'custom']: return redirect('/')
    
    config = {
        'confirm': {'title': 'Zahlungsbestätigung', 'color': '#10b981', 'icon': 'bi-check-all', 
                    'def_msg': 'Wir haben deine Zahlung für die Abikasse erhalten und erfolgreich verbucht.', 'label2': 'Verwendungszweck'},
        'remind': {'title': 'Zahlungserinnerung', 'color': '#f59e0b', 'icon': 'bi-clock-history', 
                   'def_msg': 'Dein Beitrag für die Abikasse steht leider noch aus. Bitte überweise den Betrag zeitnah.', 'label2': 'Frist bis'},
        'status': {'title': 'Kontostand-Update', 'color': '#3b82f6', 'icon': 'bi-wallet2', 
                   'def_msg': 'Hier ist deine aktuelle Übersicht über die eingegangenen Zahlungen.', 'label2': 'Letzte Buchung'}
    }
    
    if mode == 'custom':
        form_content = """
        <div class="card p-4">
            <h5>HTML Mail senden</h5>
            <form action="/send_logic" method="POST">
                <input type="hidden" name="type" value="custom">
                <input type="email" name="email" class="form-control mb-3" placeholder="Empfänger" required>
                <input type="text" name="subject" class="form-control mb-3" placeholder="Betreff" required>
                <textarea name="html_content" class="form-control mb-3" rows="10" placeholder="HTML Code..."></textarea>
                <button class="btn btn-dark w-100">Absenden</button>
            </form>
        </div>
        """
    else:
        c = config[mode]
        form_content = f"""
        <div class="card p-4 shadow-sm">
            <h4 style="color:{c['color']}"><i class="bi {c['icon']} me-2"></i>{c['title']}</h4>
            <form action="/send_logic" method="POST" class="mt-4">
                <input type="hidden" name="type" value="{mode}">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="small fw-bold">EMPFÄNGER EMAIL</label>
                        <input type="email" name="email" class="form-control" required>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="small fw-bold">NAME DES SCHÜLERS</label>
                        <input type="text" name="name" class="form-control" required>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="small fw-bold">NACHRICHT (CUSTOMIZABLE)</label>
                    <textarea name="message" class="form-control" rows="3">{c['def_msg']}</textarea>
                </div>
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="small fw-bold">BETRAG (€)</label>
                        <input type="text" name="v1" class="form-control" placeholder="0,00 €">
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="small fw-bold">{c['label2'].upper()}</label>
                        <input type="text" name="v2" class="form-control">
                    </div>
                </div>
                <button class="btn w-100 py-3 text-white fw-bold" style="background:{c['color']}">E-Mail jetzt senden</button>
            </form>
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
        name = request.form.get('name')
        msg_text = request.form.get('message')
        v1 = request.form.get('v1')
        v2 = request.form.get('v2')
        
        if m == 'confirm':
            subj = "Zahlung erfolgreich | Abifinanzen"
            content = build_pro_email("Zahlung bestätigt", name, msg_text, "Betrag", v1, "Verwendungszweck", v2, "#10b981")
        elif m == 'remind':
            subj = "WICHTIG: Zahlung ausstehend | Abifinanzen"
            content = build_pro_email("Zahlungserinnerung", name, msg_text, "Offener Betrag", v1, "Frist bis", v2, "#f59e0b")
        else:
            subj = "Kontostand-Update | Abifinanzen"
            content = build_pro_email("Dein Kontostand", name, msg_text, "Guthaben", v1, "Letzte Info", v2, "#3b82f6")

    if send_mail(email, subj, content):
        flash(f"Gesendet an {email}")
    else:
        flash("Fehler beim Versand.")
    return redirect(f"/{m}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
