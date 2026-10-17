import os
import sqlite3
from datetime import datetime

from flask import (
    Flask, abort, flash, g, redirect, render_template, request, url_for,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
os.makedirs(app.instance_path, exist_ok=True)
app.config["DATABASE"] = os.path.join(app.instance_path, "books.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    author      TEXT    NOT NULL,
    year        INTEGER,
    description TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


# db

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    get_db().executescript(SCHEMA)
    get_db().commit()


with app.app_context():
    init_db()





def get_book_or_404(book_id):
    book = get_db().execute(
        "SELECT * FROM books WHERE id = ?", (book_id,)
    ).fetchone()
    if book is None:
        abort(404)
    return book


def validate(form):
    """Повертає (дані для форми, рік як int/None, словник помилок)."""
    data = {
        "title": form.get("title", "").strip(),
        "author": form.get("author", "").strip(),
        "year": form.get("year", "").strip(),
        "description": form.get("description", "").strip(),
    }
    errors = {}

    if not data["title"]:
        errors["title"] = "Вкажіть назву книги."
    elif len(data["title"]) > 200:
        errors["title"] = "Назва не може бути довшою за 200 символів."

    if not data["author"]:
        errors["author"] = "Вкажіть автора."
    elif len(data["author"]) > 100:
        errors["author"] = "Ім'я автора не може бути довшим за 100 символів."

    year = None
    if data["year"]:
        try:
            year = int(data["year"])
        except ValueError:
            errors["year"] = "Рік має бути числом."
        else:
            if not 1 <= year <= datetime.now().year:
                errors["year"] = f"Рік має бути від 1 до {datetime.now().year}."

    if len(data["description"]) > 1000:
        errors["description"] = "Опис не може бути довшим за 1000 символів."

    return data, year, errors


# crud

@app.route("/")
def index():
    """READ (список) + пошук за назвою або автором."""
    q = request.args.get("q", "").strip()
    books = get_db().execute("SELECT * FROM books ORDER BY id DESC").fetchall()
    if q:
        # SQLite LIKE не ігнорує регістр для кирилиці, тому фільтруємо в Python
        needle = q.casefold()
        books = [
            b for b in books
            if needle in b["title"].casefold() or needle in b["author"].casefold()
        ]
    return render_template("index.html", books=books, q=q)


@app.route("/books/<int:book_id>")
def detail(book_id):
    """READ (одна книга)."""
    return render_template("detail.html", book=get_book_or_404(book_id))


@app.route("/books/new", methods=["GET", "POST"])
def create():
    """CREATE."""
    if request.method == "POST":
        data, year, errors = validate(request.form)
        if not errors:
            db = get_db()
            cur = db.execute(
                "INSERT INTO books (title, author, year, description) "
                "VALUES (?, ?, ?, ?)",
                (data["title"], data["author"], year, data["description"]),
            )
            db.commit()
            flash("Книгу додано.", "success")
            return redirect(url_for("detail", book_id=cur.lastrowid))
        return render_template(
            "form.html", book=data, errors=errors, mode="create"
        ), 400
    return render_template(
        "form.html",
        book={"title": "", "author": "", "year": "", "description": ""},
        errors={}, mode="create",
    )


@app.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
def edit(book_id):
    """UPDATE."""
    book = get_book_or_404(book_id)
    if request.method == "POST":
        data, year, errors = validate(request.form)
        if not errors:
            db = get_db()
            db.execute(
                "UPDATE books SET title = ?, author = ?, year = ?, "
                "description = ? WHERE id = ?",
                (data["title"], data["author"], year, data["description"], book_id),
            )
            db.commit()
            flash("Зміни збережено.", "success")
            return redirect(url_for("detail", book_id=book_id))
        return render_template(
            "form.html", book=data, errors=errors, mode="edit", book_id=book_id
        ), 400
    current = {
        "title": book["title"],
        "author": book["author"],
        "year": book["year"] if book["year"] is not None else "",
        "description": book["description"],
    }
    return render_template(
        "form.html", book=current, errors={}, mode="edit", book_id=book_id
    )


@app.route("/books/<int:book_id>/delete", methods=["POST"])
def delete(book_id):
    """DELETE (лише через POST, щоб книгу не можна було видалити переходом за посиланням)."""
    get_book_or_404(book_id)
    db = get_db()
    db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    db.commit()
    flash("Книгу видалено.", "success")
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
