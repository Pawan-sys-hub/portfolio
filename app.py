import os
import re
import json
import urllib.request
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

# ── RESEND EMAIL NOTIFICATION ────────────────────
def send_contact_email(name, sender_email, subject, message):
    """Forward contact form submission to Gmail via Resend API."""
    api_key  = os.getenv("RESEND_API_KEY")
    to_email = os.getenv("GMAIL_USER")  # your Gmail address

    if not api_key or not to_email:
        raise ValueError("RESEND_API_KEY or GMAIL_USER not set")

    body = f"""New contact form submission from your portfolio:

Name    : {name}
Email   : {sender_email}
Subject : {subject}

Message:
{message}"""

    payload = json.dumps({
        "from": "Portfolio Contact <onboarding@resend.dev>",
        "to":   [to_email],
        "subject": f"[Portfolio Contact] {subject or 'New Message'}",
        "text": body,
        "reply_to": sender_email,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status not in (200, 201):
            raise RuntimeError(f"Resend API error: {resp.status}")

# ── CONTACT API ──────────────────────────────────────────────
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

    # ── Step 1: Send email (primary action) ───────────────────
    email_sent = False
    email_error = None
    try:
        send_contact_email(name, email, subject, message)
        email_sent = True
    except Exception as e:
        email_error = str(e)

    # ── Step 2: Save to DB (bonus — optional) ─────────────────
    db_error = None
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
    except Exception as e:
        db_error = str(e)

    # ── Step 3: Decide response ────────────────────────────────
    if email_sent:
        # Email delivered — success regardless of DB state
        return jsonify({"success": True, "message": "Message sent! I'll get back to you soon."}), 201
    elif db_error is None:
        # DB saved but email failed — still a partial success
        return jsonify({"success": True, "message": "Message received! (Email notification delayed)"}), 201
    else:
        # Both failed — return error
        return jsonify({
            "success": False,
            "message": "Could not send your message right now. Please try emailing directly.",
            "detail": email_error
        }), 500


# ── RUN ──────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)