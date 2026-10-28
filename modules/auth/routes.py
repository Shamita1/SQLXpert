import re
import sqlite3
from functools import wraps
from pathlib import Path

from flask import (
    Blueprint, flash, redirect, render_template,
    request, session, url_for
)
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "sqlxpert.db"


def get_db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def init_auth_db():
    with get_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped_view


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", username):
            flash(
                "Username must be 3-30 characters using letters, numbers, or underscores.",
                "danger"
            )
            return render_template("auth/register.html")

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Enter a valid email address.", "danger")
            return render_template("auth/register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        try:
            with get_db() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO users (username, email, password_hash)
                    VALUES (?, ?, ?)
                    """,
                    (username, email, generate_password_hash(password))
                )
                user_id = cursor.lastrowid

            session.clear()
            session["user_id"] = user_id
            session["username"] = username
            flash("Account created successfully.", "success")
            return redirect(url_for("home"))

        except sqlite3.IntegrityError:
            flash("That username or email is already registered.", "danger")

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "")

        with get_db() as connection:
            user = connection.execute(
                """
                SELECT id, username, password_hash
                FROM users
                WHERE username = ? COLLATE NOCASE
                   OR email = ? COLLATE NOCASE
                """,
                (identity, identity)
            ).fetchone()

        if user is None or not check_password_hash(
            user["password_hash"], password
        ):
            flash("Invalid username/email or password.", "danger")
            return render_template("auth/login.html")

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        flash("Welcome back!", "success")
        return redirect(url_for("home"))

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/me")
@login_required
def me():
    return {
        "user_id": session["user_id"],
        "username": session["username"]
    }
