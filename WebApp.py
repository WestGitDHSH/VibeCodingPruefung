import os
import json
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "uploads"
DATA_FILE = "data.json"

ALLOWED_EXTENSIONS = {"pdf", "txt"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


USERS = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "name": "Administrator"
    },
    "mueller": {
        "password": "mueller123",
        "role": "staff",
        "name": "Frau Jana Müller"
    }
}


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        if "client_id" in request.form:
            cid = request.form["client_id"]
            return redirect(url_for("client", client_id=cid))

        if "username" in request.form:
            username = request.form["username"]
            password = request.form["password"]

            user = USERS.get(username)

            if user and user["password"] == password:
                session["username"] = username
                session["role"] = user["role"]
                session["name"] = user["name"]
                return redirect(url_for("dashboard"))
            else:
                flash("Login fehlgeschlagen.")

    return render_template("index.html")


@app.route("/client/<client_id>", methods=["GET", "POST"])
def client(client_id):

    data = load_data()
    client = data.get(client_id)

    if not client:
        return "Client-ID nicht gefunden."

    if request.method == "POST":

        note = request.form.get("note")

        if note:
            client["notes"].append(note)

        if "file" in request.files:
            file = request.files["file"]

            if file.filename != "":
                if allowed_file(file.filename):
                    filename = secure_filename(f"{client_id}_{file.filename}")
                    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(filepath)
                    client["documents_uploaded"].append(filename)

        data[client_id] = client
        save_data(data)

        flash("Daten erfolgreich gespeichert.")
        return redirect(url_for("client", client_id=client_id))

    return render_template("client.html", client=client, client_id=client_id)


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=session["name"])


@app.route("/termine")
@login_required
def termine():

    data = load_data()
    role = session["role"]
    name = session["name"]

    result = {}

    if role == "admin":
        result = data
    else:
        for cid, info in data.items():
            if info["staff"] == name:
                result[cid] = info

    return render_template("termine.html", data=result)


@app.route("/dokumente")
@login_required
def dokumente():

    data = load_data()
    role = session["role"]
    name = session["name"]

    docs = []

    if role == "admin":
        for cid, info in data.items():
            for d in info.get("documents_uploaded", []):
                docs.append((cid, d))
    else:
        for cid, info in data.items():
            if info["staff"] == name:
                for d in info.get("documents_uploaded", []):
                    docs.append((cid, d))

    return render_template("dokumente.html", docs=docs)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)