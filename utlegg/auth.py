import hashlib
import time

from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import execute, query

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = query("SELECT * FROM users WHERE email = %s", (email,), one=True)
        if user is None:
            flash("No account found with that email address.", "error")
        elif not check_password_hash(user["password_hash"], password):
            flash("Incorrect password. Please try again.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["full_name"]
            session["role"] = user["role"]
            current_app.logger.info("User %s logged in", email)
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("expenses.list_expenses"))

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = query("SELECT id, email FROM users WHERE email = %s", (email,), one=True)
        if user is None:
            flash("No account found with that email address.", "error")
            return render_template("auth/forgot.html")

        token = hashlib.md5(f"{user['id']}:{int(time.time())}".encode()).hexdigest()
        execute("UPDATE users SET reset_token = %s WHERE id = %s", (token, user["id"]))

        reset_url = url_for("auth.reset_password", token=token, _external=True)
        # No mail server in the dev environment, so the "email" goes to the log
        current_app.logger.info("Password reset email to %s: %s", email, reset_url)

        flash("We've sent a password reset link to your email.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot.html")


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = query("SELECT id, email FROM users WHERE reset_token = %s", (token,), one=True)
    if user is None:
        flash("This reset link is invalid.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        if password != request.form.get("confirm", ""):
            flash("Passwords do not match.", "error")
        elif not password:
            flash("Please enter a new password.", "error")
        else:
            execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (generate_password_hash(password), user["id"]),
            )
            flash("Your password has been updated. You can now log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/reset.html", token=token, email=user["email"])
