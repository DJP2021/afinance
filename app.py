import os
import csv
import io
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, render_template_string, request, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "abifinanzen_ultra_v3"

# --- CONFIG ---
UPLOAD_FOLDER = 'static/uploads'
DATA_FILE = 'static/templates.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

SMTP_SERVER = "smtp.zeptomail.eu"
SMTP_PORT = 465
SMTP_USER = "emailapikey"
SMTP_PASSWORD = os.environ.get("SMTP_PASS", "yA6KbHtbug+jwGoGRhRvhJOL+t03rP06iiy14irif8IhI9Ll2qFt0EducdCzLmDdjI/Q4qhTPtsTI9rv79xafJA0NoICfJTGTuv4P2uV48xh8ciEYNYig56qBbgUG6RLcBMjDCwxRPgoWA==")

ACTUAL_SENDER = "noreply@abifinanzen.de"
SENDER_NAME = "Abifinanzen Management"

current_logo = None

# --- JSON HELPERS ---
def load_templates():
    if not os.path.exists(DATA_FILE):
        return {"confirm": [], "remind": [], "status": []}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_template_to_json(category, name, message, v1, v2):
    data = load_templates()
    data[category].append({"name": name, "msg": message, "v1": v1, "v2": v2})
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

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

def build_pro_email(title, name, message, val1_label, val1_val, val2_label, val2_val, color="#3b82f6"):
    logo_path = f"{request.host_url}static/uploads/{current_logo}" if current_logo else ""
    logo_img = f'<img src="{logo_path}" height="50" style="margin-bottom:20px; border:0;">' if current_logo else f'<h1 style="color:{color}; margin:0;">Abifinanzen</h1>'
    return f"""
    <div style="width:100%; max-width:600px; margin:20px auto; background:#ffffff; border-radius:8px; border:1px solid #e2e8f0; font-family:sans-serif;">
        <div style="padding:40px; text-align:center; border-bottom:1px solid #e2e8f0;">{logo_img}</div>
        <div style="padding:40px; color:#1e293b; line-height:1.6;">
            <h2 style="color:#0f172a;">{title}</h2>
            <p>Hallo {name},</p>
            <p>{message}</p>
            <table style="width:100%; background:#f8fafc; border-radius:6px; margin:20px 0; border-spacing:0;">
                <tr><td style="padding:15px; color:#64748b; font-size:12px; font-weight:bold;">{val1_label}</td><td style="padding:15px; font-weight:bold; text-align:right;">{val1_val}</td></tr>
                <tr><td style="padding:15px; color:#64748b; font-size:12px; font-weight:bold;">{val2_label}</td><td style="padding:15px; font-weight:bold; text-align:right;">{val2_val}</td></tr>
            </table>
        </div>
    </div>
    """

# --- UI COMPONENTS ---
HEADER = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <style>
        body { background:#f8fafc; font-family: 'Inter', sans-serif; }
        .sidebar { background:#0f172a; min-height:100vh; color:white; position:fixed; width:250px; padding-top:20px; }
        .main-content { margin-left:250px; padding:40px; }
        .nav-link { color:#94a3b8; padding:12px 20px; border-radius:8px; margin:4px 15px; display:flex; align-items:center; }
        .nav-link:hover, .nav-link.active { background:rgba(255,255,255,0.1); color:white; }
        .card { border:none; border-radius:12px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="px-4 mb-4"><h4 class="fw-bold">abi<span class="text-primary">finanzen</span></h4></div>
        <div class="nav flex-column">
            <a href="/" class="nav-link {{'active' if page=='dash' else ''}}">Dashboard</a>
            <a href="/confirm" class="nav-link {{'active' if page=='confirm' else ''}}">Bestätigung</a>
            <a href="/remind" class="nav-link {{'active' if page=='remind' else ''}}">Erinnerung</a>
            <a href="/status" class="nav-link {{'active' if page=='status' else ''}}">Kontostand</a>
        </div>
    </div>
    <div class="main-content">
"""

@app.route('/')
def index():
    return render_template_string(HEADER + "<h1>Admin Dashboard</h1><p>Wähle eine Kategorie links.</p></div></body></html>", page="dash")

@app.route('/<mode>')
def mail_pages(mode):
    if mode not in ['confirm', 'remind', 'status']: return redirect('/')
    configs = {
        'confirm': {'t': 'Zahlungsbestätigung', 'c': '#10b981', 'l2': 'Zweck'},
        'remind': {'t': 'Erinnerung', 'c': '#f59e0b', 'l2': 'Frist'},
        'status': {'t': 'Kontostand', 'c': '#3b82f6', 'l2': 'Letzte Info'}
    }
    cfg = configs[mode]
    saved = load_templates().get(mode, [])
    
    form_content = f"""
    <div class="card p-4">
        <div class="d-flex justify-content-between">
            <h4 style="color:{cfg['c']}">{cfg['t']}</h4>
            <div class="dropdown">
                <button class="btn btn-sm btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">Vorlagen laden</button>
                <ul class="dropdown-menu">
                    {''.join([f'<li><a class="dropdown-item" href="#" onclick="loadT(\'{t["msg"]}\',\'{t["v1"]}\',\'{t["v2"]}\')">{t["name"]}</a></li>' for t in saved]) if saved else '<li><span class="dropdown-item">Keine Vorlagen</span></li>'}
                </ul>
            </div>
        </div>
        <form action="/send_logic" method="POST" id="mailForm" class="mt-4">
            <input type="hidden" name="type" value="{mode}">
            <div class="row mb-3">
                <div class="col"><label class="small fw-bold">EMPFÄNGER EMAIL</label><input type="email" name="email" class="form-control" required></div>
                <div class="col"><label class="small fw-bold">NAME SCHÜLER</label><input type="text" name="name" class="form-control" required></div>
            </div>
            <div class="mb-3">
                <label class="small fw-bold">NACHRICHT</label>
                <textarea name="message" id="msg" class="form-control" rows="4"></textarea>
            </div>
            <div class="row mb-3">
                <div class="col"><label class="small fw-bold">BETRAG</label><input type="text" name="v1" id="v1" class="form-control"></div>
                <div class="col"><label class="small fw-bold">{cfg['l2'].upper()}</label><input type="text" name="v2" id="v2" class="form-control"></div>
            </div>
            <div class="d-flex gap-2">
                <button name="action" value="send" class="btn flex-grow-1 text-white fw-bold" style="background:{cfg['c']}">E-Mail senden</button>
                <button type="button" class="btn btn-outline-dark" onclick="saveT()">Als Vorlage speichern</button>
            </div>
        </form>
    </div>
    <script>
        function loadT(m, v1, v2) {{ document.getElementById('msg').value = m; document.getElementById('v1').value = v1; document.getElementById('v2').value = v2; }}
        function saveT() {{
            const name = prompt("Name für diese Vorlage:");
            if(!name) return;
            const f = document.getElementById('mailForm');
            const fd = new FormData(f);
            fd.append('tpl_name', name);
            fetch('/save_tpl', {{ method: 'POST', body: fd }}).then(() => location.reload());
        }}
    </script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    """
    return render_template_string(HEADER + form_content + "</div></body></html>", page=mode)

@app.route('/save_tpl', methods=['POST'])
def save_tpl():
    save_template_to_json(request.form['type'], request.form['tpl_name'], request.form['message'], request.form['v1'], request.form['v2'])
    return "OK"

@app.route('/send_logic', methods=['POST'])
def send_logic():
    m = request.form.get('type')
    email, name, msg_text, v1, v2 = request.form.get('email'), request.form.get('name'), request.form.get('message'), request.form.get('v1'), request.form.get('v2')
    
    titles = {"confirm": "Zahlung bestätigt", "remind": "Zahlungserinnerung", "status": "Kontostand Update"}
    labels = {"confirm": "Zweck", "remind": "Frist", "status": "Info"}
    
    content = build_pro_email(titles[m], name, msg_text, "Betrag", v1, labels[m], v2)
    if send_mail(email, f"{titles[m]} | Abifinanzen", content): flash(f"Gesendet an {email}")
    else: flash("Fehler!")
    return redirect(f"/{m}")

@app.route('/upload_logo', methods=['POST'])
def upload_logo():
    global current_logo
    file = request.files.get('logo')
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        current_logo = filename
    return redirect('/')

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8000)))
