# public_app.py
from flask import Flask, render_template, request
from db import get_conn, init_db
from pathlib import Path
import threading
import time
import requests

app = Flask(__name__)

# Asegura que la DB exista
init_db()

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


def ghost_pinger():
    """
    Hilo que mantiene viva la app con un ping cada 10 minutos.
    """
    while True:
        try:
            print("👻 Ghost pinging...")
            # Reemplaza la URL por la de tu subdominio en Render
            requests.get("https://TU_SUBDOMINIO_ON_RENDER.com/")
        except Exception as e:
            print(f"Ghost ping error: {e}")
        time.sleep(600)  # Cada 10 minutos (600 segundos)


if __name__ == "__main__":
    # Inicia el hilo del ping fantasma
    threading.Thread(target=ghost_pinger, daemon=True).start()
    # Arranca la app Flask
    app.run(debug=True, port=5000)
