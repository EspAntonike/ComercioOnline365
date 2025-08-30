# public_app.py
from flask import Flask, render_template, request
from db import get_conn, init_db
from pathlib import Path


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


if __name__ == "__main__":
# Producción: usa gunicorn/uwsgi + reverse proxy
    app.run(debug=True, port=5000)