import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "supersecretkey"

# ------------------ Upload Config ------------------
app.config['UPLOAD_FOLDER'] = os.path.join("static", "uploads")
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "avi"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------ Database Setup ------------------
def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            mobile TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
    """)

    # Admins table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            mobile TEXT,
            email TEXT UNIQUE,
            password TEXT,
            employee_id TEXT,
            aadhaar TEXT,
            role TEXT DEFAULT 'admin'
        )
    """)

    # Reports table with verification status
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            hazard_type TEXT,
            name TEXT,
            description TEXT,
            city TEXT,
            latitude TEXT,
            longitude TEXT,
            media_path TEXT,
            timestamp TEXT,
            verified TEXT DEFAULT 'unverified',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ------------------ Home ------------------
@app.route("/")
def home():
    return render_template("index.html")

# ------------------ Signin/Register ------------------
@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        action = request.form.get("action")
        role = request.form.get("role")

        # ---------- LOGIN ----------
        if action == "login":
            email = request.form.get("email")
            password = request.form.get("password")

            conn = sqlite3.connect("users.db")
            cur = conn.cursor()

            if role == "user":
                cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
            else:  # admin
                cur.execute("SELECT * FROM admins WHERE email=? AND password=?", (email, password))

            user = cur.fetchone()
            conn.close()

            if user:
                session["role"] = role
                session["user_id"] = user[0]
                return redirect(url_for("profile"))
            else:
                return render_template("accountpage.html", error="Invalid credentials.", message=None)

        # ---------- REGISTER ----------
        elif action == "register":
            name = request.form.get("name")
            mobile = request.form.get("mobile")
            email = request.form.get("email")
            password = request.form.get("password")

            conn = sqlite3.connect("users.db")
            cur = conn.cursor()

            if role == "user":
                try:
                    cur.execute("INSERT INTO users (name, mobile, email, password, role) VALUES (?, ?, ?, ?, 'user')",
                                (name, mobile, email, password))
                    conn.commit()
                    session["role"] = "user"
                    session["user_id"] = cur.lastrowid
                    conn.close()
                    return redirect(url_for("profile"))
                except sqlite3.IntegrityError:
                    conn.close()
                    return render_template("accountpage.html", error="Email already registered.", message=None)

            elif role == "admin":
                employee_id = request.form.get("employee_id")
                aadhaar = request.form.get("aadhaar")
                try:
                    cur.execute("""INSERT INTO admins (name, mobile, email, password, employee_id, aadhaar, role) 
                                   VALUES (?, ?, ?, ?, ?, ?, 'admin')""",
                                (name, mobile, email, password, employee_id, aadhaar))
                    conn.commit()
                    session["role"] = "admin"
                    session["user_id"] = cur.lastrowid
                    conn.close()
                    return redirect(url_for("profile"))
                except sqlite3.IntegrityError:
                    conn.close()
                    return render_template("accountpage.html", error="Admin email already registered.", message=None)

    return render_template("accountpage.html", error=None, message=None)

# ------------------ Profile ------------------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("signin"))

    role = session.get("role")
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    if role == "user":
        cur.execute("SELECT id, name, mobile, email, role FROM users WHERE id=?", (session["user_id"],))
    else:
        cur.execute("SELECT id, name, mobile, email, employee_id, aadhaar, role FROM admins WHERE id=?", (session["user_id"],))

    user = cur.fetchone()
    conn.close()

    return render_template("profile.html", user=user, role=role)

# ------------------ Logout ------------------
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("role", None)
    return redirect(url_for("signin"))

# ------------------ Report ------------------
@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        if "user_id" not in session or session.get("role") != "user":
            return "Login required as user", 401

        user_id = session["user_id"]
        hazard_type = request.form.get("hazard_type")
        name = request.form.get("name")
        description = request.form.get("description")
        city = request.form.get("city")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        media_file = request.files.get("media")
        media_path = None
        if media_file and allowed_file(media_file.filename):
            filename = secure_filename(f"{int(datetime.now().timestamp())}_{media_file.filename}")
            media_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            media_path = f"/static/uploads/{filename}"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reports 
            (user_id, hazard_type, name, description, city, latitude, longitude, media_path, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, hazard_type, name, description, city, latitude, longitude, media_path, timestamp))
        conn.commit()
        conn.close()

        return redirect(url_for("feed"))

    # GET request -> show report form
    return render_template("report.html")

# ------------------ Feed ------------------
@app.route("/feed")
def feed():
    if "user_id" not in session or session.get("role") != "user":
        return redirect(url_for("signin"))

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT r.id, r.hazard_type, r.name, r.description, r.city, r.latitude, r.longitude, 
               r.timestamp, r.media_path, r.verified, u.name
        FROM reports r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.timestamp DESC
    """)
    reports = cur.fetchall()
    conn.close()
    return render_template("feed.html", reports=reports, current_user=session.get("user_id"))

# ------------------ Serve Uploaded Media ------------------
@app.route("/static/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ------------------ Run App ------------------
if __name__ == "__main__":
    app.run(debug=True, port=8080)
