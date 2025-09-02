# public_app.py
from flask import Flask, render_template, request
from pathlib import Path
import sqlite3
import hashlib
import os

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "products.db"   # BD actual en uso
TEMP_PATH = BASE_DIR / "db_temp.db"  # BD en espera (recibida desde subir.py)

# 🔑 Hash SHA256 de la contraseña correcta
PASSWORD_HASH = "c40e957c730718233694f439449d0166bceea4d46007c789319686233545bc54"


def get_conn():
    """Devuelve conexión a la BD actual"""
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    # 🔄 Si hay una nueva BD en TEMP, la activamos
    if TEMP_PATH.exists():
        os.replace(TEMP_PATH, DB_PATH)

    conn = get_conn()
    if conn is None:
        return "⚠️ No hay base de datos disponible. Sube una con subir.py.", 503

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

    products = conn.execute(sql, params).fetchall()
    cats = conn.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()
    conn.close()

    categories = [r["category"] for r in cats]

    return render_template("index.html", products=products, categories=categories, q=q, cat=cat)


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

    # Guardar archivo como BD temporal
    file.save(TEMP_PATH)

    # Validar que es una BD SQLite legible
    try:
        with sqlite3.connect(TEMP_PATH) as conn:
            rows = conn.execute("SELECT COUNT(*) FROM products").fetchone()
            print(f"✅ BD recibida con {rows[0]} productos (esperando refresco del navegador)")
    except Exception as e:
        return f"ERROR: {e}", 500

    return "OK", 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
