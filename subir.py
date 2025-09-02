# subir.py
from flask import Flask, render_template, request, redirect, url_for, flash
import requests

app = Flask(__name__)
app.secret_key = "clave-subir"  # solo para los flash

# ⚡ Aquí apuntamos al endpoint correcto de public_app
PUBLIC_APP_URL = "https://comercioonline365-6.onrender.com/receive"

ALLOWED_EXT = {"db"}  # Solo permitimos archivos .db


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


@app.route("/")
def home():
    return render_template("subir.html")


@app.route("/send", methods=["POST"])
def send():
    password = request.form.get("password", "")
    file = request.files.get("dbfile")

    if not file or not password:
        flash("Debes proporcionar una contraseña y un archivo .db", "error")
        return redirect(url_for("home"))

    if not allowed_file(file.filename):
        flash("Solo se permiten archivos con extensión .db", "error")
        return redirect(url_for("home"))

    # Enviar el archivo + contraseña a public_app
    try:
        resp = requests.post(
            PUBLIC_APP_URL,  # ✅ ahora apunta a /receive
            data={"password": password},
            files={"dbfile": (file.filename, file.stream, "application/octet-stream")},
            timeout=15,
        )
    except Exception as e:
        flash(f"Error de conexión con public_app: {e}", "error")
        return redirect(url_for("home"))

    if resp.status_code == 200 and "OK" in resp.text:
        return redirect(url_for("success"))
    else:
        return redirect(url_for("failure"))


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/failure")
def failure():
    return render_template("failure.html")


if __name__ == "__main__":
    app.run(debug=True, port=5002)
##contraseña: pepeMalakatones.66@