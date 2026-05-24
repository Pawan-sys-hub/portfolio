import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# pyrefly: ignore [missing-import]
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── EMAIL VALIDATION ─────────────────────────────
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def is_valid_email(email):
    return bool(EMAIL_RE.match(email))

# ── DATABASE CONNECTION (AIVEN CLOUD) ────────────
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "defaultdb"),
        ssl_disabled=False,
        ssl_verify_cert=False,
        ssl_verify_identity=False,
        connection_timeout=10,
    )

# ── HEALTH CHECK ─────────────────────────────────
@app.route("/health")
def health():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({"status": "ok", "db": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "error", "db": str(e)}), 500

# ── HOME ─────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ── PROJECTS API ─────────────────────────────────
@app.route("/api/projects", methods=["GET"])
def get_projects():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, title, category, description,
                   image_url, live_link, git_link,
                   technologies_used
            FROM projects
            ORDER BY id ASC
        """)

        rows = cursor.fetchall()

        for row in rows:
            raw = row.get("technologies_used") or ""
            row["technologies"] = [x.strip() for x in raw.split(",") if x.strip()]
            row.pop("technologies_used", None)

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": rows})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ── GMAIL EMAIL NOTIFICATION ─────────────────────
def send_contact_email(name, sender_email, subject, message):
    """Forward contact form submission to Gmail inbox."""
    gmail_user = os.getenv("GMAIL_USER")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_user or not gmail_pass:
        return  # Email not configured — skip silently

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Portfolio Contact] {subject or 'New Message'}"
    msg["From"]    = gmail_user
    msg["To"]      = gmail_user
    msg["Reply-To"] = sender_email

    body = f"""\
New contact form submission from your portfolio:

Name    : {name}
Email   : {sender_email}
Subject : {subject}

Message:
{message}
"""
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, gmail_user, msg.as_string())

# ── CONTACT API ──────────────────────────────────
@app.route("/api/contact", methods=["POST"])
def contact():
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "Invalid JSON"}), 400

    name    = data.get("name", "").strip()
    email   = data.get("email", "").strip()
    subject = data.get("subject", "").strip()
    message = data.get("message", "").strip()

    if len(name) < 2:
        return jsonify({"success": False, "message": "Name too short"}), 422

    if not is_valid_email(email):
        return jsonify({"success": False, "message": "Invalid email"}), 422

    if len(message) < 10:
        return jsonify({"success": False, "message": "Message too short"}), 422

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO contact_messages (name, email, subject, message)
            VALUES (%s, %s, %s, %s)
        """, (name, email, subject, message))

        conn.commit()
        cursor.close()
        conn.close()

        # Send Gmail notification (non-blocking — won't fail the request)
        try:
            send_contact_email(name, email, subject, message)
        except Exception:
            pass  # Email failure is silent — DB save already succeeded

        return jsonify({"success": True, "message": "Message sent"}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ── RUN ──────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)