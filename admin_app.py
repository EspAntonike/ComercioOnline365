# admin_app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from pathlib import Path
import os
import uuid
import sqlite3
from db import get_conn, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("ADMIN_SECRET", "dev-secret")

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Inicializa la base de datos en el arranque
init_db()

ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

@app.route("/")
def home():
    return redirect(url_for("new_product"))

@app.route("/admin/new", methods=["GET", "POST"])
def new_product():
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        name = request.form.get("name", "").strip()
        url = request.form.get("url", "").strip()
        description = request.form.get("description", "").strip()
        image_url = request.form.get("image_url", "").strip()
        image_file = request.files.get("image_file")

        if not category or not name or not url:
            flash("Categoría, Nombre y URL son obligatorios", "error")
            return redirect(url_for("new_product"))

        saved_path = None
        # Prioriza fichero subido, si no, usa URL remota
        if image_file and image_file.filename:
            if not allowed_file(image_file.filename):
                flash("Formato de imagen no permitido", "error")
                return redirect(url_for("new_product"))
            ext = image_file.filename.rsplit(".", 1)[1].lower()
            fname = f"{uuid.uuid4().hex}.{ext}"
            dest = UPLOAD_DIR / fname
            image_file.save(dest)
            saved_path = f"/static/uploads/{fname}"
        elif image_url:
            saved_path = image_url  # URL absoluta (CDN / imagen externa)

        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO products (category, name, url, description, image_path)
                VALUES (?, ?, ?, ?, ?)
                """,
                (category, name, url, description, saved_path),
            )
            conn.commit()

        flash("Producto añadido correctamente", "success")
        return redirect(url_for("list_products"))

    return render_template("admin_form.html")

@app.route("/admin/list")
def list_products():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()
    return render_template("admin_list.html", products=rows)

@app.route("/admin/delete/<int:pid>", methods=["POST"])
def delete_product(pid):
    # Borrado simple (no borra imagen del disco para mantenerlo sencillo)
    with get_conn() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (pid,))
        conn.commit()
    flash("Producto eliminado", "success")
    return redirect(url_for("list_products"))

if __name__ == "__main__":
    app.run(debug=True, port=5001)
