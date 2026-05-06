import os
import sqlite3
import random
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secretkey123"

DB = "database.db"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "txt"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# ---------------------------------------------------
# Datenbank
# ---------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        role TEXT,
        fullname TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT,
        date TEXT,
        location TEXT,
        staff TEXT,
        progress INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS notes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT,
        message TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS uploads(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT,
        filename TEXT
    )
    """)

    # Demo User
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users(username,password,role,fullname) VALUES(?,?,?,?)",
                    ("admin", "admin123", "admin", "Administrator"))

    cur.execute("SELECT * FROM users WHERE username='mueller'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users(username,password,role,fullname) VALUES(?,?,?,?)",
                    ("mueller", "mueller123", "staff", "Frau Jana Müller"))

    # Demo Client
    cur.execute("SELECT * FROM clients WHERE client_id='abc123'")
    if not cur.fetchone():
        cur.execute("""
        INSERT INTO clients(client_id,date,location,staff,progress)
        VALUES(?,?,?,?,?)
        """, ("abc123", "2025-12-10", "Amt Mitte Raum 204", "Frau Jana Müller", 2))

    cur.execute("SELECT * FROM clients WHERE client_id='xyz789'")
    if not cur.fetchone():
        cur.execute("""
        INSERT INTO clients(client_id,date,location,staff,progress)
        VALUES(?,?,?,?,?)
        """, ("xyz789", "2025-12-18", "Amt Nord Raum 3", "Frau Jana Müller", 1))

    cur.execute("SELECT * FROM clients WHERE client_id='cfg047'")
    if not cur.fetchone():
        cur.execute("""
        INSERT INTO clients(client_id,date, location, staff, progress) 
        VALUES(?,?,?,?,?)
        """, ("cfg047", "2026-07-14", "Amt Nord Raum 3", "Frau Jana Müller", 3))

    conn.commit()
    conn.close()


# ---------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------
# Startseite
# ---------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        # Client Login
        if "client_id" in request.form:
            cid = request.form["client_id"]
            return redirect(url_for("client_view", client_id=cid))

        # Mitarbeiter Login
        if "username" in request.form:
            username = request.form["username"]
            password = request.form["password"]

            conn = get_db()
            user = conn.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            ).fetchone()
            conn.close()

            if user:
                session["username"] = user["username"]
                session["role"] = user["role"]
                session["fullname"] = user["fullname"]
                return redirect(url_for("dashboard"))
            else:
                flash("Login fehlgeschlagen")

    return render_template("index.html")


# ---------------------------------------------------
# Client Bereich
# ---------------------------------------------------
@app.route("/client/<client_id>", methods=["GET", "POST"])
def client_view(client_id):

    conn = get_db()
    client = conn.execute(
        "SELECT * FROM clients WHERE client_id=?",
        (client_id,)
    ).fetchone()

    if not client:
        conn.close()
        return "Client-ID nicht gefunden"

    if request.method == "POST":

        note = request.form.get("note")
        if note:
            conn.execute(
                "INSERT INTO notes(client_id,message) VALUES(?,?)",
                (client_id, note)
            )

        if "file" in request.files:
            file = request.files["file"]

            if file.filename != "":
                if allowed_file(file.filename):
                    filename = secure_filename(f"{client_id}_{file.filename}")
                    path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(path)

                    conn.execute(
                        "INSERT INTO uploads(client_id,filename) VALUES(?,?)",
                        (client_id, filename)
                    )

        conn.commit()

    uploads = conn.execute(
        "SELECT * FROM uploads WHERE client_id=?",
        (client_id,)
    ).fetchall()

    notes = conn.execute(
        "SELECT * FROM notes WHERE client_id=?",
        (client_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "client.html",
        client=client,
        uploads=uploads,
        notes=notes
    )


# ---------------------------------------------------
# Dashboard
# ---------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        user=session["fullname"]
    )


# ---------------------------------------------------
# Termine
# ---------------------------------------------------
@app.route("/termine")
@login_required
def termine():

    conn = get_db()

    if session["role"] == "admin":
        data = conn.execute(
            "SELECT * FROM clients"
        ).fetchall()
    else:
        data = conn.execute(
            "SELECT * FROM clients WHERE staff=?",
            (session["fullname"],)
        ).fetchall()

    conn.close()

    return render_template("termine.html", data=data)


# ---------------------------------------------------
# Dokumente
# ---------------------------------------------------
@app.route("/dokumente")
@login_required
def dokumente():

    conn = get_db()

    if session["role"] == "admin":
        docs = conn.execute("""
            SELECT uploads.client_id, uploads.filename
            FROM uploads
        """).fetchall()

    else:
        docs = conn.execute("""
            SELECT uploads.client_id, uploads.filename
            FROM uploads
            JOIN clients
            ON uploads.client_id = clients.client_id
            WHERE clients.staff=?
        """, (session["fullname"],)).fetchall()

    conn.close()

    return render_template("dokumente.html", docs=docs)

# -----------------------------------
# Client einfügen
# -----------------------------------

@app.route("/create_client")
@login_required
def create_client():

    if session["role"] != "admin":
        return "Kein Zugriff"

    # Zufällige Client-ID erzeugen
    client_id = "CL" + str(random.randint(100000, 999999))

    conn = get_db()

    conn.execute("""
        INSERT INTO clients(client_id, date, location, staff, progress)
        VALUES (?, ?, ?, ?, ?)
    """, (
        client_id,
        "noch offen",
        "noch offen",
        session["fullname"],
        1
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("termine"))
# ------------------------------
# Client bearbeiten
# ------------------------------
@app.route("/edit_client/<client_id>", methods=["GET", "POST"])
@login_required
def edit_client(client_id):

    if session["role"] != "admin":
        return "Kein Zugriff"

    conn = get_db()

    client = conn.execute(
        "SELECT * FROM clients WHERE client_id=?",
        (client_id,)
    ).fetchone()

    if request.method == "POST":
        date = request.form["date"]
        location = request.form["location"]
        staff = request.form["staff"]
        progress = request.form["progress"]

        conn.execute("""
            UPDATE clients
            SET date=?, location=?, staff=?, progress=?
            WHERE client_id=?
        """, (date, location, staff, progress, client_id))

        conn.commit()
        conn.close()

        return redirect(url_for("termine"))

    conn.close()

    return render_template("edit_client.html", client=client)

# -----------------------------------
# Client löschen
# ----------------------------------
@app.route("/delete_client/<client_id>", methods=["POST"])
@login_required
def delete_client(client_id):

    if session["role"] != "admin":
        return "Kein Zugriff"

    conn = get_db()

    # zugehörige Daten mitlöschen
    conn.execute("DELETE FROM notes WHERE client_id=?", (client_id,))
    conn.execute("DELETE FROM uploads WHERE client_id=?", (client_id,))
    conn.execute("DELETE FROM clients WHERE client_id=?", (client_id,))

    conn.commit()
    conn.close()

    flash(f"Client {client_id} wurde gelöscht")
    return redirect(url_for("termine"))


# ---------------------------------------------------
# Logout
# ---------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------------------------------------------
# Start
# ---------------------------------------------------
RESET_DB = False  # ← hier steuerst du es

if __name__ == "__main__":

    if RESET_DB and os.path.exists(DB):
        os.remove(DB)

    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)