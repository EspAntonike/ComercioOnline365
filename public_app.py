# public_app.py
from flask import Flask, render_template, request
from db import get_conn, init_db
from pathlib import Path
import sqlite3
import hashlib
import os

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "products.db"   # nombre fijo de la base de datos

# Asegura que la DB exista
init_db()

# 🔑 Hash SHA256 de la contraseña correcta
# Genera con: python -c "import hashlib; print(hashlib.sha256(b'mi_clave').hexdigest())"
PASSWORD_HASH = "c40e957c730718233694f439449d0166bceea4d46007c789319686233545bc54"  


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", "").strip()

    sql = "SELECT * FROM products"
    params = []
    filters = []

    if q:
        filters.append("(name LIKE ? OR description LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])
    if cat:
        filters.append("category = ?")
        params.append(cat)

    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " ORDER BY created_at DESC"

    with get_conn() as conn:
        products = conn.execute(sql, params).fetchall()
        cats = conn.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()

    categories = [r["category"] for r in cats]

    return render_template("index.html", products=products, categories=categories, q=q, cat=cat)


# === NUEVA RUTA PARA RECIBIR BD DESDE subir.py ===
@app.route("/receive", methods=["POST"])
def receive():
    password = request.form.get("password", "")
    file = request.files.get("dbfile")

    if not password or not file:
        return "FALTAN DATOS", 400

    # Hashear contraseña recibida y comparar
    phash = hashlib.sha256(password.encode()).hexdigest()
    if phash != PASSWORD_HASH:
        return "FAIL", 403

    # Guardar archivo temporalmente
    temp_path = BASE_DIR / "db_temp.db"
    file.save(temp_path)

    # Validar que es una BD SQLite legible
    try:
        with sqlite3.connect(temp_path) as conn:
            rows = conn.execute("SELECT COUNT(*) FROM products").fetchone()
            print(f"✅ BD recibida con {rows[0]} productos")
        # Reemplazar la BD actual
        os.replace(temp_path, DB_PATH)
    except Exception as e:
        return f"ERROR: {e}", 500

    return "OK", 200


if __name__ == "__main__":
    # Producción: usa gunicorn/uwsgi + reverse proxy
    app.run(debug=True, port=5000)
