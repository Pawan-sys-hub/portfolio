"""
app.py – Portfolio Website Backend
Flask + MySQL + CORS + python-dotenv

Endpoints:
  GET  /                  → serves index.html
  GET  /api/projects      → returns all projects as JSON
  POST /api/contact       → validates + saves a contact message
"""

import os
import re
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error as MySQLError
from dotenv import load_dotenv

# ── Load environment variables from .env ────────────────────────────────────
load_dotenv()

# ── App factory ─────────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, resources={r"/api/*": {"origins": "*"}})  # restrict in production


# ── Database connection helper ───────────────────────────────────────────────
def get_db_connection():
    """Return a new MySQL connection using .env credentials."""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "pawan"),
            password=os.getenv("DB_PASSWORD", "Pawan@9866!"),
            database=os.getenv("DB_NAME", "pawan"),
            charset="utf8mb4",
        )
        return conn
    except MySQLError as err:
        raise err


# ── Simple email validator ──────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email))


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the single-page portfolio frontend."""
    return render_template("index.html")


# ─────────────────── GET /api/projects ────────────────────────────────────

@app.route("/api/projects", methods=["GET"])
def get_projects():
    """
    Fetch all projects from the database and return them as a JSON array.
    technologies_used (CSV string) is split into a Python list for the frontend.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                title,
                category,
                description,
                image_url,
                live_link,
                git_link,
                technologies_used
            FROM projects
            ORDER BY id ASC
            """
        )
        rows = cursor.fetchall()

        # Convert comma-separated technologies string → list
        for row in rows:
            raw = row.get("technologies_used", "") or ""
            row["technologies"] = [t.strip() for t in raw.split(",") if t.strip()]
            del row["technologies_used"]

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": rows}), 200

    except MySQLError as err:
        return jsonify({"success": False, "message": f"Database error: {err}"}), 500


# ─────────────────── POST /api/contact ────────────────────────────────────

@app.route("/api/contact", methods=["POST"])
def post_contact():
    """
    Receive a contact form JSON, validate all fields,
    and insert using parameterized queries (SQL-injection safe).
    """
    body = request.get_json(silent=True)

    if not body:
        return jsonify({"success": False, "message": "Invalid JSON body."}), 400

    name    = (body.get("name")    or "").strip()
    email   = (body.get("email")   or "").strip()
    subject = (body.get("subject") or "").strip()
    message = (body.get("message") or "").strip()

    # ── Validation ───────────────────────────────────────────────────────
    errors = []
    if not name or len(name) < 2:        errors.append("Name must be at least 2 characters.")
    if len(name) > 120:                  errors.append("Name must not exceed 120 characters.")
    if not email:                        errors.append("Email is required.")
    elif not is_valid_email(email):      errors.append("Please provide a valid email address.")
    elif len(email) > 180:              errors.append("Email address is too long.")
    if not subject or len(subject) < 3: errors.append("Subject must be at least 3 characters.")
    if len(subject) > 200:              errors.append("Subject must not exceed 200 characters.")
    if not message or len(message) < 10:errors.append("Message must be at least 10 characters.")

    if errors:
        return jsonify({"success": False, "message": " ".join(errors)}), 422

    # ── Persist to database ──────────────────────────────────────────────
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            INSERT INTO contact_messages (name, email, subject, message)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (name, email, subject, message))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Thank you! Your message has been received.",
        }), 201

    except MySQLError as err:
        return jsonify({"success": False, "message": f"Database error: {err}"}), 500


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", 5000)),
        debug=debug_mode,
    )
