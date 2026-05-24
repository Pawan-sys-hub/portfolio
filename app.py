"""
app.py – Portfolio Website Backend
Flask + MySQL (Cloud Ready) + CORS + python-dotenv
"""

import os
import re
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error as MySQLError
from dotenv import load_dotenv

# ── Load environment variables ─────────────────────────────
load_dotenv()

# ── App setup ───────────────────────────────────────────────
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── EMAIL VALIDATION ────────────────────────────────────────
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email))


# ── DATABASE CONNECTION (CLOUD SAFE) ───────────────────────
def get_db_connection():
    """Connect to MySQL (Aiven / Cloud / Local fallback)."""
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            charset="utf8mb4",
            ssl_disabled=False  # important for Aiven cloud
        )
    except MySQLError as err:
        print("Database connection failed:", err)
        raise


# ── ROUTES ──────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── GET PROJECTS ────────────────────────────────────────────
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

        # convert CSV → list
        for row in rows:
            raw = row.get("technologies_used") or ""
            row["technologies"] = [t.strip() for t in raw.split(",") if t.strip()]
            row.pop("technologies_used", None)

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": rows}), 200

    except Exception as err:
        return jsonify({"success": False, "message": str(err)}), 500


# ── CONTACT FORM ────────────────────────────────────────────
@app.route("/api/contact", methods=["POST"])
def post_contact():
    body = request.get_json(silent=True)

    if not body:
        return jsonify({"success": False, "message": "Invalid JSON"}), 400

    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip()
    subject = (body.get("subject") or "").strip()
    message = (body.get("message") or "").strip()

    # validation
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

        return jsonify({
            "success": True,
            "message": "Message sent successfully!"
        }), 201

    except Exception as err:
        return jsonify({"success": False, "message": str(err)}), 500


# ── RUN APP ─────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", 5000)),
        debug=False
    )