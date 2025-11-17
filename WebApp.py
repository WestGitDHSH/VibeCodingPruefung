from flask import Flask, render_template, request, redirect, url_for, jsonify
import json

app = Flask(__name__)


def load_client_data(client_id):
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(client_id)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        client_id = request.form.get("client_id")
        return redirect(url_for("track", client_id=client_id))
    return render_template("index.html")


@app.route("/track/<client_id>", methods=["GET", "POST"])
def track(client_id):
    client = load_client_data(client_id)

    if not client:
        return "Ungültige Client-ID.", 404

    if request.method == "POST":
        note = request.form.get("note")
        client["notes"].append(note)

        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        data[client_id] = client

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return render_template("tracking.html", client=client, show_toast=True)

    return render_template("tracking.html", client=client)


@app.route("/success")
def success():
    return render_template("success.html")


if __name__ == "__main__":
    app.run(debug=True)
